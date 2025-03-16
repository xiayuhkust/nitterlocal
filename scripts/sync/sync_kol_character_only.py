#!/usr/bin/env python3
"""
Dedicated script for synchronizing kol_character table to MySQL.

This script focuses only on kol_character synchronization with improved error handling
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

def sync_kol_character(sqlite_conn, mysql_conn, test_mode=False, verbose=False):
    """Synchronize kol_character table from SQLite to MySQL"""
    try:
        start_time = time.time()
        
        # Get data from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        # Check if kol_character table exists, if not use url_tracking
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kol_character'")
        use_url_tracking = not sqlite_cursor.fetchone()
        
        if use_url_tracking:
            logging.info("kol_character table not found, using url_tracking table instead")
            sqlite_cursor.execute("SELECT * FROM url_tracking")
        else:
            sqlite_cursor.execute("SELECT * FROM kol_character")
            
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            logging.info("No kol_character data to synchronize")
            return 0
        
        total_rows = len(rows)
        logging.info(f"Found {total_rows} kol_character records in SQLite")
        
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
        insert_count = 0
        update_count = 0
        error_count = 0
        
        # Process each row
        for i, row in enumerate(rows):
            try:
                # Convert row to dict
                row_dict = dict(zip(sqlite_columns, row))
                
                # For url_tracking table, extract Twitter handle from URL if available
                twitter_handle = None
                if 'url' in row_dict and row_dict.get('url') and 'twitter.com/' in row_dict.get('url', ''):
                    url = row_dict.get('url', '')
                    parts = url.split('twitter.com/')
                    if len(parts) > 1:
                        twitter_handle = parts[1].split('/')[0].split('?')[0]
                        if verbose:
                            logging.info(f"Extracted Twitter handle {twitter_handle} from URL {url}")
                
                # Check if record already exists in MySQL
                # Handle different column names between url_tracking and kol_character
                kol_id = row_dict.get('kol_id', row_dict.get('user_id'))
                if not kol_id:
                    logging.warning(f"Skipping row with no kol_id or user_id")
                    error_count += 1
                    continue
                    
                mysql_cursor.execute(
                    "SELECT COUNT(*) FROM kol_character WHERE kol_id = %s",
                    (kol_id,)
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
                        update_params.append(kol_id)
                        
                        if not test_mode:
                            mysql_cursor.execute(update_query, update_params)
                            # Ensure all results are consumed
                            while mysql_conn.unread_result:
                                cursor = mysql_conn.cursor()
                                cursor.fetchall()
                                cursor.close()
                        
                        if verbose:
                            logging.info(f"Updated kol_character record for kol_id: {row_dict['kol_id']}")
                            logging.info(f"Used columns: {[col for col in common_columns if col != 'kol_id']}")
                        
                        update_count += 1
                    else:
                        if verbose:
                            logging.info(f"No columns to update for kol_id: {row_dict['kol_id']}")
                else:
                    # Insert new record - only include columns that exist in MySQL
                    # Make sure kol_id is included
                    insert_columns = ['kol_id']
                    insert_values = [kol_id]
                    
                    # 修复：正确处理kol_screen_name字段
                    if 'kol_screen_name' in mysql_columns:
                        if not use_url_tracking and 'kol_screen_name' in row_dict and row_dict['kol_screen_name']:
                            # 直接使用kol_character表中的值
                            insert_columns.append('kol_screen_name')
                            insert_values.append(row_dict['kol_screen_name'])
                            if verbose:
                                logging.info(f"Using kol_screen_name '{row_dict['kol_screen_name']}' from SQLite kol_character table")
                        elif use_url_tracking and twitter_handle:
                            # 从URL中提取的Twitter用户名
                            insert_columns.append('kol_screen_name')
                            insert_values.append(twitter_handle)
                            if verbose:
                                logging.info(f"Using extracted Twitter handle '{twitter_handle}' for kol_screen_name")
                        elif use_url_tracking and 'screen_name' in row_dict and row_dict['screen_name']:
                            # 使用url_tracking表中的screen_name字段
                            insert_columns.append('kol_screen_name')
                            insert_values.append(row_dict['screen_name'])
                            if verbose:
                                logging.info(f"Using screen_name '{row_dict['screen_name']}' from url_tracking table")
                        else:
                            # 使用默认值
                            logging.warning(f"No kol_screen_name available for kol_id {kol_id}, using default 'unknown_user'")
                            insert_columns.append('kol_screen_name')
                            insert_values.append(f"unknown_user_{kol_id}")
                    
                    # Add other common columns
                    for col in common_columns:
                        if col not in ['kol_id', 'kol_screen_name'] and col in row_dict:
                            insert_columns.append(col)
                            insert_values.append(row_dict[col])
                    
                    # Add created_at if it exists in MySQL
                    if 'created_at' in mysql_columns and 'created_at' not in insert_columns:
                        insert_columns.append('created_at')
                        insert_values.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    
                    # Build the query
                    columns_str = ", ".join(insert_columns)
                    placeholders = ", ".join(["%s"] * len(insert_columns))
                    insert_query = f"INSERT INTO kol_character ({columns_str}) VALUES ({placeholders})"
                    
                    if not test_mode:
                        try:
                            mysql_cursor.execute(insert_query, insert_values)
                            # Ensure all results are consumed
                            while mysql_conn.unread_result:
                                cursor = mysql_conn.cursor()
                                cursor.fetchall()
                                cursor.close()
                            
                            if verbose:
                                logging.info(f"Inserted new kol_character record for kol_id: {row_dict['kol_id']}")
                                logging.info(f"Used columns: {insert_columns}")
                            
                            insert_count += 1
                        except mysql.connector.Error as e:
                            logging.error(f"MySQL error inserting record for kol_id {row_dict['kol_id']}: {str(e)}")
                            error_count += 1
                    else:
                        if verbose:
                            logging.info(f"Would insert new kol_character record for kol_id: {row_dict['kol_id']}")
                        insert_count += 1
                
                processed_count += 1
                
                # Commit every 50 records to avoid large transactions
                if processed_count % 50 == 0 and not test_mode:
                    mysql_conn.commit()
                    logging.info(f"Processed {processed_count}/{total_rows} kol_character records ({insert_count} inserts, {update_count} updates)")
                
            except Exception as e:
                logging.error(f"Error processing kol_character record {i}: {str(e)}")
                error_count += 1
        
        # Final commit
        if not test_mode:
            mysql_conn.commit()
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log summary
        logging.info(f"KOL character synchronization completed in {duration:.2f} seconds")
        logging.info(f"Processed {processed_count} records ({insert_count} inserts, {update_count} updates, {error_count} errors)")
        
        # Try to log detailed summary if the module is available
        try:
            from src.utils.detailed_logger import log_sync_summary, log_data_operation
            
            # Log detailed summary
            log_sync_summary(
                ['kol_character'], 
                processed_count,
                duration,
                success=(error_count == 0)
            )
            
            # Log detailed operation counts
            log_data_operation(
                'sync_to_mysql', 
                'kol_character', 
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
        
        return processed_count
    
    except Exception as e:
        logging.error(f"Error synchronizing kol_character: {str(e)}")
        if not test_mode:
            mysql_conn.rollback()
        raise

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Synchronize kol_character table to MySQL')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no actual changes)')
    parser.add_argument('--db-path', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db',
                        help='Path to SQLite database')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-lock', action='store_true', help='Disable the lock mechanism')
    parser.add_argument('--lock-timeout', type=int, default=30, help='Lock timeout in seconds')
    args = parser.parse_args()
    
    # Use a lock to prevent overlapping executions
    lock_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                            'data/kol_character_sync_lock.pid')
    
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
            logging.info(f"Starting kol_character synchronization at {datetime.now().isoformat()}")
            
            # Connect to databases
            sqlite_conn = get_sqlite_connection(args.db_path)
            mysql_conn = get_mysql_connection()
            
            # Synchronize kol_character
            processed_count = sync_kol_character(sqlite_conn, mysql_conn, args.test, args.verbose)
            
            # Close connections
            sqlite_conn.close()
            mysql_conn.close()
            
            # Calculate duration
            duration = time.time() - start_time
            
            logging.info(f"KOL character synchronization completed in {duration:.2f} seconds")
            logging.info(f"Synchronized {processed_count} kol_character records")
            
            return 0
        
        except Exception as e:
            logging.error(f"Error in kol_character synchronization: {str(e)}")
            return 1

if __name__ == "__main__":
    sys.exit(main())
