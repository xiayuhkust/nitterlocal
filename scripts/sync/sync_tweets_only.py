#!/usr/bin/env python3
"""
Dedicated script for synchronizing tweets table to MySQL kol_tweet table.

This script focuses only on tweets synchronization with improved error handling
and detailed logging to diagnose synchronization issues.
"""

import os
import sys
import time
import logging
import argparse
import sqlite3
import mysql.connector
from datetime import datetime, timedelta
import dotenv

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the sync lock
try:
    from scripts.sync.sync_lock import SyncLock
except ImportError:
    # Define a fallback SyncLock class if the module is not available
    class SyncLock:
        def __init__(self, lock_file=None, timeout=None):
            self.locked = False
        
        def acquire(self):
            self.locked = True
            return True
        
        def release(self):
            self.locked = False
        
        def __enter__(self):
            self.acquire()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.release()

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
        
        # If not found by exact match, try case-insensitive match
        cursor = mysql_conn.cursor()
        cursor.execute(
            "SELECT kol_id FROM kol_info WHERE LOWER(kol_screen_name) = LOWER(%s)",
            (handle,)
        )
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            logging.info(f"Found kol_id for {handle} using case-insensitive match")
            return result[0]
            
        return None
    
    except Exception as e:
        logging.error(f"Error getting numeric ID for handle {handle}: {str(e)}")
        return None

def sync_tweets(sqlite_conn, mysql_conn, since_days=30, test_mode=False, batch_size=100, verbose=False):
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
            return 0
        
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
        skipped_count = 0
        
        for i, row in enumerate(rows):
            try:
                # Convert row to dict
                row_dict = dict(zip(sqlite_columns, row))
                
                # Get user_id from the tweet
                user_id = row_dict.get('user_id')
                if not user_id:
                    logging.warning(f"Tweet {row_dict.get('tweet_id', 'unknown')} has no user_id, skipping")
                    skipped_count += 1
                    continue
                
                # Get the author from tweets as screen_name
                screen_name = row_dict.get('author')
                if not screen_name:
                    logging.warning(f"Tweet {row_dict.get('tweet_id', 'unknown')} has no author field for user_id: {user_id}, skipping")
                    skipped_count += 1
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
                    set_clauses = []
                    update_params = []
                    
                    for col in common_columns:
                        if col != 'tweet_id':  # Skip the primary key
                            set_clauses.append(f"{col} = %s")
                            update_params.append(mysql_data[col])
                    
                    if set_clauses:
                        set_clause = ", ".join(set_clauses)
                        update_query = f"UPDATE kol_tweet SET {set_clause} WHERE tweet_id = %s"
                        
                        # Prepare parameters (all values except tweet_id, then tweet_id at the end)
                        update_params.append(mysql_data['tweet_id'])
                        
                        if not test_mode:
                            mysql_cursor.execute(update_query, update_params)
                            # Ensure all results are consumed
                            while mysql_conn.unread_result:
                                cursor = mysql_conn.cursor()
                                cursor.fetchall()
                                cursor.close()
                        
                        update_count += 1
                    else:
                        skipped_count += 1
                else:
                    # Insert new record
                    columns_str = ", ".join(common_columns)
                    placeholders = ", ".join(["%s"] * len(common_columns))
                    insert_query = f"INSERT INTO kol_tweet ({columns_str}) VALUES ({placeholders})"
                    
                    # Prepare parameters
                    insert_params = [mysql_data[col] for col in common_columns]
                    
                    if not test_mode:
                        try:
                            mysql_cursor.execute(insert_query, insert_params)
                            # Ensure all results are consumed
                            while mysql_conn.unread_result:
                                cursor = mysql_conn.cursor()
                                cursor.fetchall()
                                cursor.close()
                            
                            insert_count += 1
                        except mysql.connector.Error as e:
                            logging.error(f"MySQL error inserting tweet {mysql_data['tweet_id']}: {str(e)}")
                            error_count += 1
                    else:
                        insert_count += 1
                
                processed_count += 1
                
                # Commit every batch_size records to avoid large transactions
                if processed_count % batch_size == 0 and not test_mode:
                    mysql_conn.commit()
                    logging.info(f"Processed {processed_count}/{total_rows} tweets ({insert_count} inserts, {update_count} updates)")
                
                # Log verbose details if requested
                if verbose and processed_count % 100 == 0:
                    logging.info(f"Progress: {processed_count}/{total_rows} tweets processed")
                
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
        logging.info(f"Processed {processed_count} tweets ({insert_count} inserts, {update_count} updates, {skipped_count} skipped, {error_count} errors)")
        
        # Try to log detailed summary if the module is available
        try:
            from src.utils.detailed_logger import log_sync_summary, log_data_operation
            
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
                    'skipped': skipped_count,
                    'errors': error_count,
                    'duration_seconds': duration
                }
            )
        except ImportError:
            # Detailed logging not available, continue without it
            pass
        
        return processed_count
    
    except Exception as e:
        logging.error(f"Error synchronizing tweets: {str(e)}")
        if not test_mode:
            mysql_conn.rollback()
        return 0

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Synchronize tweets table to MySQL')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no actual changes)')
    parser.add_argument('--db-path', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db',
                        help='Path to SQLite database')
    parser.add_argument('--since-days', type=int, default=30, help='Synchronize data from the last N days')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for commits')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-lock', action='store_true', help='Disable the lock mechanism')
    parser.add_argument('--lock-timeout', type=int, default=30, help='Lock timeout in seconds')
    args = parser.parse_args()
    
    # Use a lock to prevent overlapping executions
    lock_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                            'data/tweets_sync_lock.pid')
    
    # Skip the lock if requested
    if args.no_lock:
        lock = type('DummyLock', (), {'__enter__': lambda x: x, '__exit__': lambda x, *args: None})()
        logging.info("Lock mechanism disabled")
    else:
        lock = SyncLock(lock_file, args.lock_timeout)
    
    with lock:
        # If we couldn't acquire the lock, exit
        if not getattr(lock, 'locked', True):
            logging.warning("Could not acquire lock, another synchronization process is running")
            return 0
        
        try:
            start_time = time.time()
            logging.info(f"Starting tweets synchronization at {datetime.now().isoformat()}")
            
            # Connect to databases
            sqlite_conn = get_sqlite_connection(args.db_path)
            mysql_conn = get_mysql_connection()
            
            # Synchronize tweets
            processed_count = sync_tweets(
                sqlite_conn, 
                mysql_conn, 
                args.since_days, 
                args.test, 
                args.batch_size,
                args.verbose
            )
            
            # Close connections
            sqlite_conn.close()
            mysql_conn.close()
            
            # Calculate duration
            duration = time.time() - start_time
            
            logging.info(f"Tweets synchronization completed in {duration:.2f} seconds")
            logging.info(f"Synchronized {processed_count} tweets")
            
            return 0
        
        except Exception as e:
            logging.error(f"Error in tweets synchronization: {str(e)}")
            return 1

if __name__ == "__main__":
    sys.exit(main())
