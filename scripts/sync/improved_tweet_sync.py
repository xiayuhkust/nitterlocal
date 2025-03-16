#!/usr/bin/env python3
"""
Improved tweet synchronization script for nitterlocal.

This script directly synchronizes tweets from SQLite to MySQL with dynamic column mapping
and improved error handling. It's designed to be used either standalone or called from
sync_to_mysql_combined.py.
"""

import os
import sys
import time
import logging
import argparse
import sqlite3
import mysql.connector
import dotenv
from datetime import datetime, timedelta

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the detailed logger
try:
    from src.utils.detailed_logger import log_data_operation, log_sync_summary
except ImportError:
    # Define fallback functions if the module is not available
    def log_data_operation(operation_type, table_name, record_count, details=None):
        logging.info(f"{operation_type}: {record_count} records in {table_name}")
    
    def log_sync_summary(tables_updated, total_records, duration, success=True):
        logging.info(f"Sync summary: {total_records} records across {len(tables_updated)} tables in {duration:.2f} seconds")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables from .env file
dotenv.load_dotenv()

def get_mysql_connection():
    """Get a connection to the MySQL database"""
    try:
        # Get MySQL connection parameters from environment variables
        mysql_host = os.getenv('MYSQL_HOST', '43.135.26.222')
        mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
        mysql_user = os.getenv('MYSQL_USER', 'root')
        mysql_password = os.getenv('MYSQL_PASSWORD', '')
        mysql_database = os.getenv('MYSQL_DATABASE', 'kol_info')
        
        # Connect to MySQL
        conn = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        
        return conn
    
    except Exception as e:
        logging.error(f"Error connecting to MySQL: {str(e)}")
        raise

def get_sqlite_connection(db_path='/home/ubuntu/nitterlocal/data/local_database.db'):
    """Get a connection to the SQLite database"""
    try:
        # Connect to SQLite
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        return conn
    
    except Exception as e:
        logging.error(f"Error connecting to SQLite: {str(e)}")
        raise

def get_mysql_table_columns(mysql_conn, table_name):
    """Get the column names for a MySQL table"""
    cursor = mysql_conn.cursor()
    cursor.execute(f"DESCRIBE {table_name}")
    columns = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return columns

def get_numeric_id_for_handle(mysql_conn, handle):
    """Get the numeric ID for a Twitter handle from the kol_info table"""
    try:
        cursor = mysql_conn.cursor()
        cursor.execute(
            "SELECT kol_id FROM kol_info WHERE kol_screen_name = %s",
            (handle,)
        )
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return result[0]
        return None
    
    except Exception as e:
        logging.error(f"Error getting numeric ID for handle {handle}: {str(e)}")
        return None

def sync_tweets(sqlite_conn, mysql_conn, since_days=1, test_mode=False, batch_size=100):
    """Synchronize tweets from SQLite to MySQL with dynamic column mapping"""
    try:
        start_time = time.time()
        
        # Calculate the date threshold
        threshold_date = (datetime.now() - timedelta(days=since_days)).strftime('%Y-%m-%d')
        
        # Get tweets from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("""
            SELECT t.* 
            FROM tweets t
            WHERE t.created_at >= ?
            ORDER BY t.created_at DESC
        """, (threshold_date,))
        
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            logging.info(f"No tweets found since {threshold_date}")
            return True, 0, 0, 0
        
        total_rows = len(rows)
        logging.info(f"Found {total_rows} tweets since {threshold_date}")
        
        # Get column names from SQLite
        sqlite_columns = [column[0] for column in sqlite_cursor.description]
        
        # Get column names from MySQL
        mysql_columns = get_mysql_table_columns(mysql_conn, "kol_tweet")
        logging.info(f"MySQL kol_tweet columns: {mysql_columns}")
        
        # Map SQLite columns to MySQL columns
        column_mapping = {
            'tweet_id': 'tweet_id',
            'content': 'tweet_text',
            'created_at': 'created_at',
            'likes': 'favorite_count',
            'retweets': 'retweet_count',
            'replies': 'reply_count',
            'views': 'view_count'
        }
        
        # Process each tweet
        processed_count = 0
        insert_count = 0
        update_count = 0
        error_count = 0
        
        for i, row in enumerate(rows):
            try:
                # Convert row to dict
                row_dict = dict(zip(sqlite_columns, row))
                
                # Get user_id from the tweet
                user_id = row_dict.get('user_id')
                if not user_id:
                    logging.warning(f"Tweet {row_dict.get('tweet_id', 'unknown')} has no user_id, skipping")
                    continue
                
                # Get the author from tweets as screen_name
                screen_name = row_dict.get('author')
                if not screen_name:
                    logging.warning(f"Tweet {row_dict.get('tweet_id', 'unknown')} has no author field for user_id: {user_id}, skipping")
                    continue
                
                # Get the kol_id from the screen_name
                kol_id = get_numeric_id_for_handle(mysql_conn, screen_name)
                
                if not kol_id:
                    # Try to use the user_id directly if numeric ID lookup fails
                    kol_id = user_id
                    logging.warning(f"Could not find kol_id for screen_name: {screen_name}, using user_id: {user_id}")
                
                # Create a new dict with MySQL column names
                mysql_data = {
                    'kol_id': kol_id
                }
                
                for sqlite_col, mysql_col in column_mapping.items():
                    if sqlite_col in row_dict and mysql_col in mysql_columns:
                        # Handle date format conversion for created_at
                        if sqlite_col == 'created_at':
                            # Convert ISO format to MySQL datetime format
                            created_at = row_dict[sqlite_col]
                            if created_at.endswith('Z'):
                                created_at = created_at[:-1]  # Remove the 'Z' at the end
                            mysql_data[mysql_col] = created_at.replace('T', ' ')
                        else:
                            mysql_data[mysql_col] = row_dict[sqlite_col]
                
                # Add language if available in MySQL schema
                if 'lang' in mysql_columns:
                    mysql_data['lang'] = 'en'  # Default to English if not available
                
                # Check if tweet already exists in MySQL
                mysql_cursor = mysql_conn.cursor()
                mysql_cursor.execute(
                    "SELECT COUNT(*) FROM kol_tweet WHERE tweet_id = %s",
                    (mysql_data['tweet_id'],)
                )
                count = mysql_cursor.fetchone()[0]
                
                # Filter columns to only include those that exist in MySQL
                common_columns = [col for col in mysql_data.keys() if col in mysql_columns]
                
                if count > 0:
                    # Update existing record
                    set_clause = ", ".join([f"{col} = %s" for col in common_columns if col != 'tweet_id'])
                    update_query = f"UPDATE kol_tweet SET {set_clause} WHERE tweet_id = %s"
                    
                    # Prepare parameters (all values except tweet_id, then tweet_id at the end)
                    update_params = [mysql_data[col] for col in common_columns if col != 'tweet_id']
                    update_params.append(mysql_data['tweet_id'])
                    
                    if not test_mode:
                        mysql_cursor.execute(update_query, update_params)
                    
                    update_count += 1
                else:
                    # Insert new record
                    columns_str = ", ".join(common_columns)
                    placeholders = ", ".join(["%s"] * len(common_columns))
                    insert_query = f"INSERT INTO kol_tweet ({columns_str}) VALUES ({placeholders})"
                    
                    # Prepare parameters
                    insert_params = [mysql_data[col] for col in common_columns]
                    
                    if not test_mode:
                        mysql_cursor.execute(insert_query, insert_params)
                    
                    insert_count += 1
                
                processed_count += 1
                
                # Commit every batch_size records to avoid large transactions
                if processed_count % batch_size == 0 and not test_mode:
                    mysql_conn.commit()
                    logging.info(f"Processed {processed_count}/{total_rows} tweets ({insert_count} inserts, {update_count} updates)")
                
                # Ensure all results are consumed to prevent "Unread result found" errors
                while mysql_conn.unread_result:
                    cursor = mysql_conn.cursor()
                    cursor.fetchall()
                    cursor.close()
                
            except Exception as e:
                logging.error(f"Error processing tweet {row_dict.get('tweet_id', 'unknown')}: {str(e)}")
                error_count += 1
        
        # Final commit
        if not test_mode:
            mysql_conn.commit()
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log summary
        logging.info(f"Tweet synchronization completed in {duration:.2f} seconds")
        logging.info(f"Processed {processed_count} tweets ({insert_count} inserts, {update_count} updates, {error_count} errors)")
        
        # Log detailed summary
        log_sync_summary(
            ['kol_tweet'], 
            processed_count,
            duration,
            success=(error_count == 0)
        )
        
        # Log detailed operation counts
        log_data_operation(
            'sync_to_mysql', 
            'kol_tweet', 
            processed_count,
            {
                'inserted': insert_count,
                'updated': update_count,
                'errors': error_count,
                'duration_seconds': duration
            }
        )
        
        return True, processed_count, error_count, duration
    
    except Exception as e:
        logging.error(f"Error synchronizing tweets: {str(e)}")
        if not test_mode:
            mysql_conn.rollback()
        return False, 0, 0, 0

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Synchronize tweets from SQLite to MySQL')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no actual changes)')
    parser.add_argument('--db-path', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db',
                        help='Path to SQLite database')
    parser.add_argument('--since-days', type=int, default=1, help='Synchronize data from the last N days')
    parser.add_argument('--batch-size', type=int, default=100, help='Commit batch size')
    args = parser.parse_args()
    
    try:
        logging.info(f"Starting tweet synchronization at {datetime.now().isoformat()}")
        logging.info(f"Synchronizing tweets from the last {args.since_days} days")
        
        # Connect to databases
        sqlite_conn = get_sqlite_connection(args.db_path)
        mysql_conn = get_mysql_connection()
        
        # Synchronize tweets
        success, processed_count, error_count, duration = sync_tweets(
            sqlite_conn, 
            mysql_conn, 
            args.since_days, 
            args.test,
            args.batch_size
        )
        
        # Close connections
        sqlite_conn.close()
        mysql_conn.close()
        
        logging.info(f"Tweet synchronization {'succeeded' if success else 'failed'}")
        
        return 0 if success else 1
    
    except Exception as e:
        logging.error(f"Error in tweet synchronization: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
