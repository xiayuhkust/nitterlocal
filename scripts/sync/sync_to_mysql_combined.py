#!/usr/bin/env python3
"""
Combined MySQL synchronization script for nitterlocal.

This script synchronizes data from the local SQLite database to the MySQL database.
It handles kol_character, url_tracking, and tweets tables.
Includes a lock mechanism to prevent overlapping executions.
"""

import os
import sys
import time
import logging
import argparse
import sqlite3
import pymysql
import subprocess
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
        mysql_password = os.getenv('MYSQL_PASSWORD', 'z1050493759')
        mysql_database = os.getenv('MYSQL_DATABASE', 'kol_info')
        
        # Connect to MySQL
        conn = pymysql.connect(
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

def sync_kol_character(sqlite_conn, mysql_conn, test_mode=False):
    """Synchronize kol_character table from SQLite to MySQL"""
    try:
        # Get data from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT * FROM kol_character")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            logging.info("No kol_character data to synchronize")
            return 0
        
        # Prepare MySQL cursor
        mysql_cursor = mysql_conn.cursor()
        
        # Get column names from SQLite
        sqlite_columns = [column[0] for column in sqlite_cursor.description]
        
        # Get column names from MySQL
        mysql_columns = get_mysql_table_columns(mysql_conn, "kol_character")
        logging.info(f"MySQL kol_character columns: {mysql_columns}")
        
        # Find common columns (only synchronize columns that exist in both tables)
        common_columns = [col for col in sqlite_columns if col in mysql_columns]
        logging.info(f"Common columns for kol_character: {common_columns}")
        
        # Count of processed records
        processed_count = 0
        
        # Process each row
        for row in rows:
            # Convert row to dict
            row_dict = dict(zip(sqlite_columns, row))
            
            # Check if record already exists in MySQL
            mysql_cursor.execute(
                "SELECT COUNT(*) FROM kol_character WHERE kol_id = %s",
                (row_dict['kol_id'],)
            )
            count = mysql_cursor.fetchone()[0]
            
            if count > 0:
                # Update existing record - only include columns that exist in MySQL
                set_clauses = []
                update_params = []
                
                for col in common_columns:
                    if col != 'kol_id':  # Skip the primary key
                        set_clauses.append(f"{col} = %s")
                        update_params.append(row_dict[col])
                
                # Only proceed if there are columns to update
                if set_clauses:
                    set_clause = ", ".join(set_clauses)
                    update_query = f"UPDATE kol_character SET {set_clause} WHERE kol_id = %s"
                    update_params.append(row_dict['kol_id'])
                    
                    if not test_mode:
                        mysql_cursor.execute(update_query, update_params)
                    
                    logging.info(f"Updated kol_character record for kol_id: {row_dict['kol_id']}")
                    logging.info(f"Used columns: {[col for col in common_columns if col != 'kol_id']}")
                else:
                    logging.info(f"No columns to update for kol_id: {row_dict['kol_id']}")
            else:
                # Insert new record - only include columns that exist in MySQL
                insert_columns = common_columns
                insert_values = [row_dict[col] for col in common_columns]
                
                # Build the query
                columns_str = ", ".join(insert_columns)
                placeholders = ", ".join(["%s"] * len(insert_columns))
                insert_query = f"INSERT INTO kol_character ({columns_str}) VALUES ({placeholders})"
                
                if not test_mode:
                    mysql_cursor.execute(insert_query, insert_values)
                
                logging.info(f"Inserted new kol_character record for kol_id: {row_dict['kol_id']}")
                logging.info(f"Used columns: {insert_columns}")
            
            processed_count += 1
        
        # Commit changes
        if not test_mode:
            mysql_conn.commit()
        
        logging.info(f"Synchronized {processed_count} kol_character records to MySQL")
        return processed_count
    
    except Exception as e:
        logging.error(f"Error synchronizing kol_character: {str(e)}")
        if not test_mode:
            mysql_conn.rollback()
        raise

def get_mysql_table_columns(mysql_conn, table_name):
    """Get the column names for a MySQL table"""
    cursor = mysql_conn.cursor()
    cursor.execute(f"DESCRIBE {table_name}")
    columns = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return columns

def sync_url_tracking(sqlite_conn, mysql_conn, test_mode=False):
    """Synchronize url_tracking table from SQLite to MySQL (kol_info table)
    
    Note: This function maps SQLite's url_tracking.user_id to MySQL's kol_info.kol_id
    """
    try:
        # Get data from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT * FROM url_tracking")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            logging.info("No url_tracking data to synchronize")
            return 0
        
        # Prepare MySQL cursor
        mysql_cursor = mysql_conn.cursor()
        
        # Get column names from SQLite
        sqlite_columns = [column[0] for column in sqlite_cursor.description]
        
        # Get column names from MySQL
        mysql_columns = get_mysql_table_columns(mysql_conn, "kol_info")
        logging.info(f"MySQL kol_info columns: {mysql_columns}")
        
        # Count of processed records
        processed_count = 0
        
        # Process each row
        for row in rows:
            # Convert row to dict
            row_dict = dict(zip(sqlite_columns, row))
            
            # Skip rows with no user_id
            if not row_dict.get('user_id'):
                logging.warning(f"Skipping row with no user_id: {row_dict.get('url', 'unknown')}")
                continue
            
            # Log record status and type but don't skip
            if row_dict.get('status') != 'active':
                logging.info(f"Processing inactive record: {row_dict.get('url', 'unknown')}, status: {row_dict.get('status', 'unknown')}")
            
            if row_dict.get('type', '').lower() != 'kol':
                logging.info(f"Processing non-kol record: {row_dict.get('url', 'unknown')}, type: {row_dict.get('type', 'unknown')}")
            
            # Check if record already exists in MySQL
            # Note: MySQL uses kol_id column while SQLite uses user_id
            mysql_cursor.execute(
                "SELECT COUNT(*) FROM kol_info WHERE kol_id = %s",
                (row_dict['user_id'],)  # Use user_id from SQLite as kol_id in MySQL
            )
            count = mysql_cursor.fetchone()[0]
            
            # Get Twitter handle from URL if available
            twitter_handle = None
            url = row_dict.get('url', '')
            if url and 'twitter.com/' in url:
                parts = url.split('twitter.com/')
                if len(parts) > 1:
                    twitter_handle = parts[1].split('/')[0].split('?')[0]
            
            if count > 0:
                # Update existing record - only include columns that exist in MySQL
                set_clauses = []
                update_params = []
                
                # Add kol_screen_name if it exists in MySQL
                if 'kol_screen_name' in mysql_columns:
                    set_clauses.append("kol_screen_name = %s")
                    update_params.append(twitter_handle or '')
                
                # For description, we need to check the existing MySQL value
                if 'description' in mysql_columns:
                    # Get existing MySQL description
                    mysql_cursor.execute(
                        "SELECT description FROM kol_info WHERE kol_id = %s",
                        (row_dict['user_id'],)
                    )
                    mysql_description = mysql_cursor.fetchone()[0]
                    
                    # Only update if SQLite value is not empty and MySQL value is empty
                    # or if both have values but SQLite value is different
                    if row_dict.get('description') and (not mysql_description or 
                                                       (mysql_description and row_dict['description'] != mysql_description)):
                        set_clauses.append("description = %s")
                        update_params.append(row_dict['description'])
                        logging.info(f"Updating description from '{mysql_description}' to '{row_dict['description']}'")
                    else:
                        logging.info(f"Preserving existing MySQL description: '{mysql_description}'")
                
                # Add followers_count if it exists in MySQL
                if 'followers_count' in mysql_columns and 'followers_count' in row_dict:
                    set_clauses.append("followers_count = %s")
                    update_params.append(row_dict['followers_count'] or '0')
                
                # Add following_count if it exists in MySQL
                if 'following_count' in mysql_columns and 'following_count' in row_dict:
                    set_clauses.append("following_count = %s")
                    update_params.append(int(row_dict['following_count']) if row_dict['following_count'] else 0)
                
                # Add type as first_category if it exists in MySQL
                if 'first_category' in mysql_columns and 'type' in row_dict:
                    set_clauses.append("first_category = %s")
                    update_params.append(row_dict['type'] or '')
                
                # Add subtype as second_category if it exists in MySQL
                if 'second_category' in mysql_columns and 'subtype' in row_dict:
                    set_clauses.append("second_category = %s")
                    update_params.append(row_dict['subtype'] or '')
                
                # Add kol_name if it exists in MySQL
                if 'kol_name' in mysql_columns and 'kol_name' in row_dict:
                    set_clauses.append("kol_name = %s")
                    update_params.append(row_dict['kol_name'] or '')
                
                # Only proceed if there are columns to update
                if set_clauses:
                    set_clause = ", ".join(set_clauses)
                    update_query = f"UPDATE kol_info SET {set_clause} WHERE kol_id = %s"
                    update_params.append(row_dict['user_id'])
                    
                    if not test_mode:
                        mysql_cursor.execute(update_query, update_params)
                    
                    logging.info(f"Updated kol_info record for kol_id: {row_dict['user_id']}")
                else:
                    logging.info(f"No columns to update for kol_id: {row_dict['user_id']}")
            else:
                # Insert new record - only include columns that exist in MySQL
                insert_columns = ['kol_id']
                insert_values = [row_dict['user_id']]
                
                # Add kol_screen_name if it exists in MySQL
                if 'kol_screen_name' in mysql_columns:
                    insert_columns.append('kol_screen_name')
                    insert_values.append(twitter_handle or '')
                
                # Add created_at if it exists in MySQL
                if 'created_at' in mysql_columns:
                    insert_columns.append('created_at')
                    insert_values.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                
                # Add description if it exists in MySQL
                if 'description' in mysql_columns and 'description' in row_dict:
                    insert_columns.append('description')
                    insert_values.append(row_dict['description'] or '')
                
                # Add followers_count if it exists in MySQL
                if 'followers_count' in mysql_columns and 'followers_count' in row_dict:
                    insert_columns.append('followers_count')
                    insert_values.append(row_dict['followers_count'] or '0')
                
                # Add following_count if it exists in MySQL
                if 'following_count' in mysql_columns and 'following_count' in row_dict:
                    insert_columns.append('following_count')
                    insert_values.append(int(row_dict['following_count']) if row_dict['following_count'] else 0)
                
                # Add type as first_category if it exists in MySQL
                if 'first_category' in mysql_columns and 'type' in row_dict:
                    insert_columns.append('first_category')
                    insert_values.append(row_dict['type'] or '')
                
                # Add subtype as second_category if it exists in MySQL
                if 'second_category' in mysql_columns and 'subtype' in row_dict:
                    insert_columns.append('second_category')
                    insert_values.append(row_dict['subtype'] or '')
                
                # Add kol_name if it exists in MySQL
                if 'kol_name' in mysql_columns and 'kol_name' in row_dict:
                    insert_columns.append('kol_name')
                    insert_values.append(row_dict['kol_name'] or '')
                
                # Build the query
                columns_str = ", ".join(insert_columns)
                placeholders = ", ".join(["%s"] * len(insert_columns))
                insert_query = f"INSERT INTO kol_info ({columns_str}) VALUES ({placeholders})"
                
                if not test_mode:
                    mysql_cursor.execute(insert_query, insert_values)
                
                logging.info(f"Inserted new kol_info record for kol_id: {row_dict['user_id']}")
                logging.info(f"Used columns: {insert_columns}")
            
            processed_count += 1
        
        # Commit changes
        if not test_mode:
            mysql_conn.commit()
        
        logging.info(f"Synchronized {processed_count} url_tracking records to MySQL")
        return processed_count
    
    except Exception as e:
        logging.error(f"Error synchronizing url_tracking: {str(e)}")
        if not test_mode:
            mysql_conn.rollback()
        raise

def sync_tweets(sqlite_conn, mysql_conn, since_days=1, test_mode=False, batch_size=100, all_tweets=False):
    """Synchronize tweets from SQLite to MySQL with dynamic column mapping"""
    try:
        start_time = time.time()
        
        # Calculate the date threshold if not syncing all tweets
        threshold_date = None if all_tweets else (datetime.now() - timedelta(days=since_days)).strftime('%Y-%m-%d')
        
        # Get tweets from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        if threshold_date:
            # Filter by date if not syncing all tweets
            sqlite_cursor.execute("""
                SELECT t.* 
                FROM tweets t
                WHERE t.created_at >= ?
                ORDER BY t.created_at DESC
            """, (threshold_date,))
        else:
            # Get all tweets
            sqlite_cursor.execute("""
                SELECT t.* 
                FROM tweets t
                ORDER BY t.created_at DESC
            """)
        
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            logging.info(f"No tweets found since {threshold_date}")
            return True
        
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
            'user_id': 'kol_id',
            'author': 'kol_screen_name',
            'content': 'tweet_text',
            'created_at': 'created_at',
            'likes': 'favorite_count',
            'retweets': 'retweet_count',
            'replies': 'reply_count',
            'views': 'view_count',
            'lang': 'lang'
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
                try:
                    from scripts.sync.get_numeric_id import get_numeric_id_for_handle
                    kol_id = get_numeric_id_for_handle(mysql_conn, screen_name)
                except ImportError:
                    # Fallback implementation if module not available
                    cursor = mysql_conn.cursor()
                    cursor.execute(
                        "SELECT kol_id FROM kol_info WHERE kol_screen_name = %s",
                        (screen_name,)
                    )
                    result = cursor.fetchone()
                    cursor.close()
                    kol_id = result[0] if result else None
                
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
                    'errors': error_count,
                    'duration_seconds': duration
                }
            )
        except ImportError:
            # Detailed logging not available, continue without it
            pass
        
        return True
    
    except Exception as e:
        logging.error(f"Error synchronizing tweets: {str(e)}")
        if not test_mode:
            mysql_conn.rollback()
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Synchronize SQLite data to MySQL')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no actual changes)')
    parser.add_argument('--db-path', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db',
                        help='Path to SQLite database')
    parser.add_argument('--since-days', type=int, default=1, help='Synchronize data from the last N days')
    parser.add_argument('--tweets-only', action='store_true', help='Only synchronize tweets')
    parser.add_argument('--all-tweets', action='store_true', help='Synchronize all tweets, not just recent ones')
    parser.add_argument('--no-lock', action='store_true', help='Disable the lock mechanism')
    parser.add_argument('--lock-timeout', type=int, default=30, help='Lock timeout in seconds')
    args = parser.parse_args()
    
    # Use a lock to prevent overlapping executions
    lock_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                            'data/sync_lock.pid')
    
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
            logging.info(f"Starting synchronization at {datetime.now().isoformat()}")
            
            # Connect to databases
            sqlite_conn = get_sqlite_connection(args.db_path)
            
            # Try to connect to MySQL, but continue with test mode if it fails
            mysql_conn = None
            try:
                mysql_conn = get_mysql_connection()
            except Exception as e:
                if not args.test:
                    logging.error(f"Error connecting to MySQL: {str(e)}")
                    return 1
                else:
                    logging.warning(f"MySQL connection failed, but continuing in test mode: {str(e)}")
            
            # Initialize counters
            kol_character_count = 0
            url_tracking_count = 0
            tweets_synced = False
            
            # Synchronize data (skip if tweets-only is specified)
            if not args.tweets_only and mysql_conn:
                try:
                    kol_character_count = sync_kol_character(sqlite_conn, mysql_conn, args.test)
                except Exception as e:
                    logging.warning(f"Error synchronizing kol_character (skipping): {str(e)}")
                    kol_character_count = 0
                
                try:
                    url_tracking_count = sync_url_tracking(sqlite_conn, mysql_conn, args.test)
                except Exception as e:
                    logging.warning(f"Error synchronizing url_tracking (skipping): {str(e)}")
                    url_tracking_count = 0
            
            # Synchronize tweets (always do this)
            try:
                if args.all_tweets:
                    logging.info("Synchronizing ALL tweets (no date filter)")
                else:
                    logging.info(f"Synchronizing tweets from the last {args.since_days} days")
                tweets_synced = sync_tweets(sqlite_conn, mysql_conn, args.since_days, args.test, batch_size=100, all_tweets=args.all_tweets)
            except Exception as e:
                logging.error(f"Error synchronizing tweets: {str(e)}")
                tweets_synced = False
            
            # Close connections
            sqlite_conn.close()
            if mysql_conn:
                mysql_conn.close()
            
            # Calculate duration
            duration = time.time() - start_time
            
            logging.info(f"Synchronization completed in {duration:.2f} seconds")
            if not args.tweets_only:
                logging.info(f"Synchronized {kol_character_count} kol_character records")
                logging.info(f"Synchronized {url_tracking_count} url_tracking records")
            logging.info(f"Tweets synchronization {'succeeded' if tweets_synced else 'failed'}")
            
            return 0
        
        except Exception as e:
            logging.error(f"Error in synchronization: {str(e)}")
            return 1

if __name__ == "__main__":
    sys.exit(main())
