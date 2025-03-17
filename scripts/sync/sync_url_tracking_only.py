#!/usr/bin/env python3
"""
Dedicated script for synchronizing url_tracking table to MySQL kol_info table.

This script focuses only on url_tracking synchronization with improved error handling
and detailed logging to diagnose synchronization issues.
"""

import os
import sys
import time
import logging
import argparse
import sqlite3
import mysql.connector
from datetime import datetime
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

def get_mysql_table_constraints(mysql_conn, table_name):
    """Get the constraints for a MySQL table"""
    cursor = mysql_conn.cursor()
    cursor.execute(f"""
        SELECT COLUMN_NAME, IS_NULLABLE, COLUMN_KEY
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
    """, (table_name,))
    constraints = {}
    for row in cursor.fetchall():
        column_name, is_nullable, column_key = row
        constraints[column_name] = {
            'nullable': is_nullable == 'YES',
            'key': column_key
        }
    cursor.close()
    return constraints

def sync_url_tracking(sqlite_conn, mysql_conn, test_mode=False, verbose=False):
    """Synchronize url_tracking table from SQLite to MySQL (kol_info table)
    
    Note: This function maps SQLite's url_tracking.user_id to MySQL's kol_info.kol_id
    """
    try:
        start_time = time.time()
        
        # Get data from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT * FROM url_tracking")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            logging.info("No url_tracking data to synchronize")
            return 0
        
        total_rows = len(rows)
        logging.info(f"Found {total_rows} url_tracking records in SQLite")
        
        # Prepare MySQL cursor
        mysql_cursor = mysql_conn.cursor()
        
        # Get column names from SQLite
        sqlite_columns = [column[0] for column in sqlite_cursor.description]
        
        # Get column names and constraints from MySQL
        mysql_columns = get_mysql_table_columns(mysql_conn, "kol_info")
        mysql_constraints = get_mysql_table_constraints(mysql_conn, "kol_info")
        
        logging.info(f"MySQL kol_info columns: {mysql_columns}")
        if verbose:
            logging.info(f"MySQL kol_info constraints: {mysql_constraints}")
        
        # Count of processed records
        processed_count = 0
        insert_count = 0
        update_count = 0
        error_count = 0
        skipped_count = 0
        
        # Process each row
        for i, row in enumerate(rows):
            try:
                # Convert row to dict
                row_dict = dict(zip(sqlite_columns, row))
                
                # Skip rows with no user_id
                if not row_dict.get('user_id'):
                    logging.warning(f"Skipping row with no user_id: {row_dict.get('url', 'unknown')}")
                    skipped_count += 1
                    continue
                
                # Get Twitter handle from URL if available
                twitter_handle = None
                url = row_dict.get('url', '')
                if url and 'twitter.com/' in url:
                    parts = url.split('twitter.com/')
                    if len(parts) > 1:
                        twitter_handle = parts[1].split('/')[0].split('?')[0]
                
                # Skip if we can't extract a Twitter handle and kol_screen_name is required
                if not twitter_handle and 'kol_screen_name' in mysql_columns and not mysql_constraints.get('kol_screen_name', {}).get('nullable', True):
                    logging.warning(f"Skipping row with no Twitter handle (required for kol_screen_name): {url}")
                    skipped_count += 1
                    continue
                
                # Check if record already exists in MySQL
                # First try to match by screen_name if available
                if 'screen_name' in row_dict and row_dict['screen_name']:
                    mysql_cursor.execute(
                        "SELECT COUNT(*) FROM kol_info WHERE kol_screen_name = %s",
                        (row_dict['screen_name'],)
                    )
                    count = mysql_cursor.fetchone()[0]
                    if count > 0 and verbose:
                        logging.info(f"Found existing record by screen_name: {row_dict['screen_name']}")
                else:
                    # Fall back to kol_id if screen_name not available
                    mysql_cursor.execute(
                        "SELECT COUNT(*) FROM kol_info WHERE kol_id = %s",
                        (row_dict['user_id'],)  # Use user_id from SQLite as kol_id in MySQL
                    )
                    count = mysql_cursor.fetchone()[0]
                
                if count > 0:
                    # Update existing record - only include columns that exist in MySQL
                    set_clauses = []
                    update_params = []
                    
                    # Add kol_screen_name if it exists in MySQL
                    if 'kol_screen_name' in mysql_columns and twitter_handle:
                        set_clauses.append("kol_screen_name = %s")
                        update_params.append(twitter_handle)
                    
                    # Add description if it exists in both tables
                    if 'description' in mysql_columns and 'description' in row_dict and row_dict['description']:
                        set_clauses.append("description = %s")
                        update_params.append(row_dict['description'])
                    
                    # Add kol_name if it exists in both tables
                    if 'kol_name' in mysql_columns and 'kol_name' in row_dict and row_dict['kol_name']:
                        set_clauses.append("kol_name = %s")
                        update_params.append(row_dict['kol_name'])
                    
                    # Only proceed if there are columns to update
                    if set_clauses:
                        set_clause = ", ".join(set_clauses)
                        update_query = f"UPDATE kol_info SET {set_clause} WHERE kol_id = %s"
                        update_params.append(row_dict['user_id'])
                        
                        if not test_mode:
                            mysql_cursor.execute(update_query, update_params)
                            # Ensure all results are consumed
                            while mysql_conn.unread_result:
                                cursor = mysql_conn.cursor()
                                cursor.fetchall()
                                cursor.close()
                        
                        if verbose:
                            logging.info(f"Updated kol_info record for kol_id: {row_dict['user_id']}")
                        
                        update_count += 1
                    else:
                        if verbose:
                            logging.info(f"No columns to update for kol_id: {row_dict['user_id']}")
                        skipped_count += 1
                else:
                    # Insert new record - only include columns that exist in MySQL
                    insert_columns = ['kol_id']
                    insert_values = [row_dict['user_id']]
                    
                    # Add kol_screen_name if it exists in MySQL
                    if 'kol_screen_name' in mysql_columns:
                        # First try to use screen_name from the row if available
                        if 'screen_name' in row_dict and row_dict['screen_name']:
                            insert_columns.append('kol_screen_name')
                            insert_values.append(row_dict['screen_name'])
                            if verbose:
                                logging.info(f"Using screen_name from url_tracking: {row_dict['screen_name']}")
                        # Fall back to extracted twitter_handle if screen_name not available
                        elif twitter_handle:
                            insert_columns.append('kol_screen_name')
                            insert_values.append(twitter_handle)
                            if verbose:
                                logging.info(f"Using extracted twitter_handle: {twitter_handle}")
                        elif not mysql_constraints.get('kol_screen_name', {}).get('nullable', True):
                            # Skip if kol_screen_name is required but we don't have a Twitter handle
                            logging.warning(f"Skipping insert for kol_id {row_dict['user_id']} - kol_screen_name is required but not available")
                            skipped_count += 1
                            continue
                    
                    # Add description if it exists in both tables
                    if 'description' in mysql_columns and 'description' in row_dict and row_dict['description']:
                        insert_columns.append('description')
                        insert_values.append(row_dict['description'])
                    
                    # Add kol_name if it exists in both tables
                    if 'kol_name' in mysql_columns and 'kol_name' in row_dict and row_dict['kol_name']:
                        insert_columns.append('kol_name')
                        insert_values.append(row_dict['kol_name'])
                    
                    # Add created_at if it exists in MySQL
                    if 'created_at' in mysql_columns:
                        insert_columns.append('created_at')
                        insert_values.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                
                # Add profile columns if they exist in MySQL
                if 'followers_count' in mysql_columns and 'followers_count' in row_dict and row_dict['followers_count']:
                    insert_columns.append('followers_count')
                    insert_values.append(row_dict['followers_count'])
                if 'following_count' in mysql_columns and 'following_count' in row_dict and row_dict['following_count']:
                    insert_columns.append('following_count')
                    insert_values.append(row_dict['following_count'])
                if 'tweet_count' in mysql_columns and 'tweet_count' in row_dict and row_dict['tweet_count']:
                    insert_columns.append('tweet_count')
                    insert_values.append(row_dict['tweet_count'])
                if 'profile_image_url' in mysql_columns and 'profile_image_url' in row_dict and row_dict['profile_image_url']:
                    insert_columns.append('profile_image_url')
                    insert_values.append(row_dict['profile_image_url'])
                if 'profile_banner_url' in mysql_columns and 'profile_banner_url' in row_dict and row_dict['profile_banner_url']:
                    insert_columns.append('profile_banner_url')
                    insert_values.append(row_dict['profile_banner_url'])
                if 'verified' in mysql_columns and 'verified' in row_dict and row_dict['verified']:
                    insert_columns.append('verified')
                    insert_values.append(row_dict['verified'])
                if 'location' in mysql_columns and 'location' in row_dict and row_dict['location']:
                    insert_columns.append('location')
                    insert_values.append(row_dict['location'])
                if 'created_at' in mysql_columns and 'created_at' in row_dict and row_dict['created_at']:
                    insert_columns.append('created_at')
                    insert_values.append(row_dict['created_at'])
                if 'profile_updated_at' in mysql_columns and 'profile_updated_at' in row_dict and row_dict['profile_updated_at']:
                    insert_columns.append('profile_updated_at')
                    insert_values.append(row_dict['profile_updated_at'])
                    
                    # This section is now handled above in the kol_screen_name section
                    
                    # Build the query
                    columns_str = ", ".join(insert_columns)
                    placeholders = ", ".join(["%s"] * len(insert_columns))
                    insert_query = f"INSERT INTO kol_info ({columns_str}) VALUES ({placeholders})"
                    
                    if not test_mode:
                        try:
                            mysql_cursor.execute(insert_query, insert_values)
                            # Ensure all results are consumed
                            while mysql_conn.unread_result:
                                cursor = mysql_conn.cursor()
                                cursor.fetchall()
                                cursor.close()
                            
                            if verbose:
                                logging.info(f"Inserted new kol_info record for kol_id: {row_dict['user_id']}")
                            
                            insert_count += 1
                        except mysql.connector.Error as e:
                            logging.error(f"MySQL error inserting record for kol_id {row_dict['user_id']}: {str(e)}")
                            error_count += 1
                    else:
                        if verbose:
                            logging.info(f"Would insert new kol_info record for kol_id: {row_dict['user_id']}")
                        insert_count += 1
                
                processed_count += 1
                
                # Commit every 50 records to avoid large transactions
                if processed_count % 50 == 0 and not test_mode:
                    mysql_conn.commit()
                    logging.info(f"Processed {processed_count}/{total_rows} url_tracking records ({insert_count} inserts, {update_count} updates)")
                
            except Exception as e:
                logging.error(f"Error processing url_tracking record {i}: {str(e)}")
                error_count += 1
        
        # Final commit
        if not test_mode:
            mysql_conn.commit()
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log summary
        logging.info(f"URL tracking synchronization completed in {duration:.2f} seconds")
        logging.info(f"Processed {processed_count} records ({insert_count} inserts, {update_count} updates, {skipped_count} skipped, {error_count} errors)")
        
        # Try to log detailed summary if the module is available
        try:
            from src.utils.detailed_logger import log_sync_summary, log_data_operation
            
            # Log detailed summary
            log_sync_summary(
                ['url_tracking'], 
                processed_count,
                duration,
                success=(error_count == 0)
            )
            
            # Log detailed operation counts
            log_data_operation(
                'sync_to_mysql', 
                'url_tracking', 
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
        logging.error(f"Error synchronizing url_tracking: {str(e)}")
        if not test_mode:
            mysql_conn.rollback()
        raise

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Synchronize url_tracking table to MySQL')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no actual changes)')
    parser.add_argument('--db-path', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db',
                        help='Path to SQLite database')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-lock', action='store_true', help='Disable the lock mechanism')
    parser.add_argument('--lock-timeout', type=int, default=30, help='Lock timeout in seconds')
    args = parser.parse_args()
    
    # Use a lock to prevent overlapping executions
    lock_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                            'data/url_tracking_sync_lock.pid')
    
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
            logging.info(f"Starting url_tracking synchronization at {datetime.now().isoformat()}")
            
            # Connect to databases
            sqlite_conn = get_sqlite_connection(args.db_path)
            mysql_conn = get_mysql_connection()
            
            # Synchronize url_tracking
            processed_count = sync_url_tracking(sqlite_conn, mysql_conn, args.test, args.verbose)
            
            # Close connections
            sqlite_conn.close()
            mysql_conn.close()
            
            # Calculate duration
            duration = time.time() - start_time
            
            logging.info(f"URL tracking synchronization completed in {duration:.2f} seconds")
            logging.info(f"Synchronized {processed_count} url_tracking records")
            
            return 0
        
        except Exception as e:
            logging.error(f"Error in url_tracking synchronization: {str(e)}")
            return 1

if __name__ == "__main__":
    sys.exit(main())
