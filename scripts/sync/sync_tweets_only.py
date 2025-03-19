#!/usr/bin/env python3
"""
Synchronize tweets table from SQLite to MySQL.
"""

import os
import sys
import time
import logging
import argparse
import sqlite3
import pymysql
import traceback
from datetime import datetime, timedelta
import dotenv

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the sync lock
try:
    from scripts.sync.sync_lock import SyncLock
except ImportError:
    # Define a fallback SyncLock class if the module is not available
    class SyncLock:
        def __init__(self, lock_file=None, timeout=None):
            self.locked = False
            self.lock_file = lock_file
            self.timeout = timeout
        
        def acquire(self):
            self.locked = True
            return True
        
        def release(self):
            self.locked = False
            return True
        
        def __enter__(self):
            self.acquire()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.release()

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
            database=mysql_database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        return conn
    
    except Exception as e:
        logging.error(f"Error connecting to MySQL: {str(e)}")
        logging.debug(f"Traceback: {traceback.format_exc()}")
        raise Exception(f"Error connecting to MySQL: {str(e)}")

def get_sqlite_connection(db_path='/home/ubuntu/nitterlocal/data/local_database.db'):
    """Get a connection to the SQLite database"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        return conn
    
    except Exception as e:
        logging.error(f"Error connecting to SQLite: {str(e)}")
        logging.debug(f"Traceback: {traceback.format_exc()}")
        raise Exception(f"Error connecting to SQLite: {str(e)}")

def get_mysql_table_columns(mysql_conn, table_name):
    """Get the column names for a MySQL table"""
    cursor = mysql_conn.cursor()
    cursor.execute(f"DESCRIBE {table_name}")
    columns = [row['Field'] for row in cursor.fetchall()]
    cursor.close()
    return columns

def get_mysql_table_constraints(mysql_conn, table_name):
    """Get the constraints for a MySQL table"""
    cursor = mysql_conn.cursor()
    cursor.execute("""
        SELECT COLUMN_NAME, IS_NULLABLE, COLUMN_KEY, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
    """, (table_name,))
    
    constraints = {}
    for row in cursor.fetchall():
        column_name, is_nullable, column_key, data_type = row['COLUMN_NAME'], row['IS_NULLABLE'], row['COLUMN_KEY'], row['DATA_TYPE']
        constraints[column_name] = {
            'nullable': is_nullable == 'YES',
            'key': column_key,
            'type': data_type
        }
    
    cursor.close()
    return constraints

def convert_value_for_mysql(value, column_name, constraints):
    """Convert a value to the appropriate type for MySQL"""
    if value is None:
        return None
    
    # Get the column constraints
    column_constraints = constraints.get(column_name, {})
    data_type = column_constraints.get('type', '').lower()
    
    # Convert based on data type
    if 'varchar' in data_type or 'text' in data_type:
        return str(value) if value is not None else None
    elif 'int' in data_type:
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return 0
    elif 'bigint' in data_type:
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return 0
    elif 'datetime' in data_type:
        if isinstance(value, str):
            # Try to parse the datetime string
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt
            except (ValueError, TypeError):
                return None
        return value
    
    # Default return the original value
    return value

def sync_tweets(sqlite_conn, mysql_conn, since_days=30, batch_size=100, test_mode=False, verbose=False, all_tweets=False):
    """Synchronize tweets table from SQLite to MySQL"""
    try:
        # Get SQLite cursor
        sqlite_cursor = sqlite_conn.cursor()
        
        # Get MySQL cursor
        mysql_cursor = mysql_conn.cursor()
        
        # Calculate the date threshold if not syncing all tweets
        since_date_str = None
        if not all_tweets:
            since_date = datetime.now() - timedelta(days=since_days)
            since_date_str = since_date.isoformat()
        
        # Get tweets from SQLite
        if since_date_str:
            # Filter by date if not syncing all tweets
            sqlite_cursor.execute("""
                SELECT * FROM tweets
                WHERE created_at >= ?
                ORDER BY created_at DESC
            """, (since_date_str,))
        else:
            # Get all tweets
            sqlite_cursor.execute("""
                SELECT * FROM tweets
                ORDER BY created_at DESC
            """)
        
        rows = sqlite_cursor.fetchall()
        
        if verbose:
            if not all_tweets:
                logging.info(f"Found {len(rows)} tweets since {since_date.strftime('%Y-%m-%d')}")
            else:
                logging.info(f"Found {len(rows)} tweets (all tweets)")
        
        # Get MySQL table columns
        mysql_columns = get_mysql_table_columns(mysql_conn, 'kol_tweet')
        if verbose:
            logging.debug(f"MySQL columns: {mysql_columns}")
        
        # Get MySQL table constraints
        mysql_constraints = get_mysql_table_constraints(mysql_conn, 'kol_tweet')
        
        # Map SQLite columns to MySQL columns
        column_mapping = {
            'tweet_id': 'tweet_id',
            'user_id': 'user_id',
            'screen_name': 'screen_name',
            'text': 'text',
            'created_at': 'created_at',
            'retweet_count': 'retweet_count',
            'favorite_count': 'favorite_count',
            'reply_count': 'reply_count',
            'quote_count': 'quote_count',
            'lang': 'lang',
            'source': 'source',
            'in_reply_to_status_id': 'in_reply_to_status_id',
            'in_reply_to_user_id': 'in_reply_to_user_id',
            'in_reply_to_screen_name': 'in_reply_to_screen_name',
            'is_quote_status': 'is_quote_status',
            'quoted_status_id': 'quoted_status_id',
            'quoted_status_text': 'quoted_status_text',
            'retweeted_status_id': 'retweeted_status_id',
            'retweeted_status_text': 'retweeted_status_text',
            'possibly_sensitive': 'possibly_sensitive',
            'added_at': 'added_at',
            'last_updated': 'last_updated'
        }
        
        # Process tweets in batches
        processed_count = 0
        insert_count = 0
        update_count = 0
        error_count = 0
        
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            
            for row in batch:
                # Prepare MySQL data
                mysql_data = {}
                for sqlite_column, mysql_column in column_mapping.items():
                    if sqlite_column in row.keys() and mysql_column in mysql_columns:
                        mysql_data[mysql_column] = convert_value_for_mysql(row[sqlite_column], mysql_column, mysql_constraints)
                
                # Check if the tweet exists in MySQL
                mysql_cursor.execute("SELECT * FROM kol_tweet WHERE tweet_id = %s", (mysql_data['tweet_id'],))
                existing_record = mysql_cursor.fetchone()
                
                if existing_record:
                    # Update the record
                    update_columns = []
                    update_values = []
                    
                    for column, value in mysql_data.items():
                        if column != 'tweet_id':  # Skip the primary key
                            update_columns.append(f"{column} = %s")
                            update_values.append(value)
                    
                    # Add the WHERE clause value
                    update_values.append(mysql_data['tweet_id'])
                    
                    # Build the update query
                    update_query = f"UPDATE kol_tweet SET {', '.join(update_columns)} WHERE tweet_id = %s"
                    
                    # Execute the update query
                    if not test_mode:
                        try:
                            mysql_cursor.execute(update_query, update_values)
                            update_count += 1
                        except pymysql.Error as e:
                            logging.error(f"MySQL error updating tweet {mysql_data['tweet_id']}: {str(e)}")
                            error_count += 1
                    else:
                        update_count += 1
                else:
                    # Insert the record
                    insert_columns = []
                    insert_values = []
                    
                    for column, value in mysql_data.items():
                        insert_columns.append(column)
                        insert_values.append(value)
                    
                    # Build the insert query
                    columns_str = ", ".join(insert_columns)
                    placeholders = ", ".join(["%s"] * len(insert_columns))
                    insert_query = f"INSERT INTO kol_tweet ({columns_str}) VALUES ({placeholders})"
                    
                    # Execute the insert query
                    if not test_mode:
                        try:
                            mysql_cursor.execute(insert_query, insert_values)
                            insert_count += 1
                        except pymysql.Error as e:
                            logging.error(f"MySQL error inserting tweet {mysql_data['tweet_id']}: {str(e)}")
                            error_count += 1
                    else:
                        insert_count += 1
                
                processed_count += 1
        
        # Commit the changes
        if not test_mode:
            mysql_conn.commit()
        
        # Close cursors
        mysql_cursor.close()
        sqlite_cursor.close()
        
        if verbose:
            logging.info(f"Synchronization completed in {time.time() - start_time:.2f} seconds")
            logging.info(f"Inserted: {insert_count}, Updated: {update_count}, Errors: {error_count}")
        
        return processed_count
    
    except Exception as e:
        logging.error(f"Error synchronizing tweets: {str(e)}")
        logging.debug(f"Traceback: {traceback.format_exc()}")
        if not test_mode:
            mysql_conn.rollback()
        raise Exception(f"Error synchronizing tweets: {str(e)}")

def main():
    """Main function"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Synchronize tweets table from SQLite to MySQL kol_tweet table')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no changes to MySQL)')
    parser.add_argument('--db-path', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db', help='Path to SQLite database')
    parser.add_argument('--since-days', type=int, default=30, help='Synchronize tweets from the last N days')
    parser.add_argument('--all-tweets', action='store_true', help='Synchronize all tweets, not just recent ones')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for processing tweets')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-lock', action='store_true', help='Disable lock mechanism')
    parser.add_argument('--lock-timeout', type=int, default=60, help='Lock timeout in seconds')
    args = parser.parse_args()
    
    # Set up lock file
    lock_file = '/home/ubuntu/nitterlocal/data/tweets_sync_lock.pid'
    
    # Start time
    global start_time
    start_time = time.time()
    
    # Use lock if not disabled
    if args.no_lock:
        logging.info("Lock mechanism disabled")
        lock = None
    else:
        lock = SyncLock(lock_file=lock_file, timeout=args.lock_timeout)
    
    try:
        # Acquire lock if not disabled
        if lock:
            if not lock.acquire():
                logging.error(f"Could not acquire lock: {lock_file}")
                return 1
            logging.info(f"Acquired lock: {lock_file}")
        
        # Log start time
        logging.info(f"Starting tweets synchronization at {datetime.now().isoformat()}")
        if args.all_tweets:
            logging.info("Synchronizing ALL tweets (no date filter)")
        else:
            logging.info(f"Synchronizing tweets from the last {args.since_days} days")
        
        # Connect to databases
        sqlite_conn = get_sqlite_connection(args.db_path)
        mysql_conn = get_mysql_connection()
        
        # Synchronize tweets table
        result = sync_tweets(
            sqlite_conn,
            mysql_conn,
            since_days=args.since_days,
            batch_size=args.batch_size,
            test_mode=args.test,
            verbose=args.verbose,
            all_tweets=args.all_tweets
        )
        
        # Close connections
        sqlite_conn.close()
        mysql_conn.close()
        
        # Release lock if not disabled
        if lock:
            lock.release()
            logging.info(f"Released lock: {lock_file}")
        
        return 0
    
    except Exception as e:
        logging.error(f"Error in tweets synchronization: {str(e)}")
        logging.debug(f"Traceback: {traceback.format_exc()}")
        
        # Release lock if not disabled
        if lock and lock.locked:
            lock.release()
            logging.info(f"Released lock: {lock_file}")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
