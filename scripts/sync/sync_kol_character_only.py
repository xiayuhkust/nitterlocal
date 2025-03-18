#!/usr/bin/env python3
"""
Synchronize kol_character data from SQLite to MySQL.

This script reads kol_character data from the local SQLite database
and synchronizes it to the MySQL database.
"""

import os
import sys
import logging
import sqlite3
import argparse
import pymysql
from datetime import datetime
import re
from urllib.parse import urlparse
import dotenv
import time

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

# Load environment variables from .env file
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Try to import the Twitter handle utility
try:
    from app.twitter_handle_utils import extract_twitter_handle
except ImportError:
    # Define a fallback function if the import fails
    def extract_twitter_handle(url):
        """Extract Twitter handle from a URL (fallback function)"""
        if not url:
            return None
        
        try:
            # Parse the URL
            parsed_url = urlparse(url)
            
            # Check if it's a Twitter URL
            if 'twitter.com' not in parsed_url.netloc and 'x.com' not in parsed_url.netloc:
                return None
            
            # Extract the handle from the path
            path_parts = parsed_url.path.strip('/').split('/')
            if not path_parts:
                return None
            
            handle = path_parts[0]
            
            # Clean up the handle (remove @ if present, etc.)
            handle = handle.lower()
            if handle.startswith('@'):
                handle = handle[1:]
                
            # Validate the handle format
            if re.match(r'^[a-zA-Z0-9_]{1,15}$', handle):
                return handle
            else:
                return None
                
        except Exception as e:
            logging.error(f"Error extracting Twitter handle from {url}: {str(e)}")
            return None

def acquire_lock(lock_file):
    """Acquire a lock file to prevent multiple instances from running"""
    try:
        # Check if the lock file exists
        if os.path.exists(lock_file):
            # Check if the process is still running
            with open(lock_file, 'r') as f:
                pid = f.read().strip()
            
            # Check if the process is still running
            if os.path.exists(f"/proc/{pid}"):
                logging.error(f"Another instance is already running with PID {pid}")
                return False
            
            # Remove the stale lock file
            os.remove(lock_file)
        
        # Create the lock file
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        
        logging.info(f"Acquired lock: {lock_file}")
        return True
    
    except Exception as e:
        logging.error(f"Error acquiring lock: {str(e)}")
        return False

def release_lock(lock_file):
    """Release the lock file"""
    try:
        if os.path.exists(lock_file):
            os.remove(lock_file)
        logging.info(f"Released lock: {lock_file}")
        return True
    except Exception as e:
        logging.error(f"Error releasing lock: {str(e)}")
        return False

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
        return None

def get_sqlite_connection(db_path):
    """Get a connection to the SQLite database"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logging.error(f"Error connecting to SQLite: {str(e)}")
        return None

def get_kol_screen_name(kol_id, kol_screen_name, url, screen_name):
    """
    Get the kol_screen_name value using a hierarchical approach
    
    Args:
        kol_id: The KOL ID
        kol_screen_name: The kol_screen_name from the kol_character table
        url: The URL from the url_tracking table
        screen_name: The screen_name from the url_tracking table
        
    Returns:
        A valid kol_screen_name value
    """
    # First, try to use the kol_screen_name from the kol_character table
    if kol_screen_name:
        return kol_screen_name
    
    # Second, try to extract the handle from the URL
    if url:
        handle = extract_twitter_handle(url)
        if handle:
            return handle
    
    # Third, try to use the screen_name from the url_tracking table
    if screen_name:
        return screen_name
    
    # Finally, use a default value based on the kol_id
    return f"unknown_user_{kol_id}"

def sync_kol_character(sqlite_conn, mysql_conn, test_mode=False, verbose=False):
    """
    Synchronize kol_character data from SQLite to MySQL
    
    Args:
        sqlite_conn: SQLite connection
        mysql_conn: MySQL connection
        test_mode: Whether to run in test mode (no actual changes)
        verbose: Whether to print verbose output
        
    Returns:
        True if successful, False otherwise
    """
    try:
        start_time = datetime.now()
        logging.info(f"Starting kol_character synchronization at {start_time.isoformat()}")
        
        # Get SQLite cursor
        sqlite_cursor = sqlite_conn.cursor()
        
        # Check if kol_character table exists
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kol_character'")
        kol_character_exists = sqlite_cursor.fetchone() is not None
        
        if not kol_character_exists:
            logging.error("kol_character table does not exist in SQLite")
            return False
        
        # Get all kol_character records from SQLite
        if verbose:
            logging.info("Fetching kol_character records from SQLite")
        
        # Check if url_tracking_id column exists in kol_character
        sqlite_cursor.execute("PRAGMA table_info(kol_character)")
        columns = [col[1] for col in sqlite_cursor.fetchall()]
        
        # Determine the query based on available columns
        if 'url_tracking_id' in columns:
            # Use the joined query if url_tracking_id exists
            sqlite_cursor.execute('''
            SELECT 
                k.id, k.kol_id, k.kol_screen_name, k.bio, k.lore, k.knowledge,
                k.postExamples, k.topics, k.style_all, k.style_chat, k.style_post,
                k.adjectives, k.url_tracking_id,
                u.url, u.type, u.subtype, u.user_id, u.screen_name
            FROM 
                kol_character k
            LEFT JOIN 
                url_tracking u ON k.url_tracking_id = u.id
            ''')
        else:
            # Use a simple query if url_tracking_id doesn't exist
            sqlite_cursor.execute("SELECT * FROM kol_character")
        
        kol_records = sqlite_cursor.fetchall()
        
        if not kol_records:
            logging.error("No kol_character records found in SQLite")
            return False
        
        logging.info(f"Found {len(kol_records)} kol_character records in SQLite")
        
        # Get MySQL cursor
        mysql_cursor = mysql_conn.cursor()
        
        # Get MySQL kol_character columns
        mysql_cursor.execute("SHOW COLUMNS FROM kol_character")
        mysql_columns = [col['Field'] for col in mysql_cursor.fetchall()]
        
        logging.info(f"MySQL kol_character columns: {mysql_columns}")
        
        # Determine common columns
        sqlite_columns = list(kol_records[0].keys())
        common_columns = [col for col in sqlite_columns if col in mysql_columns]
        
        logging.info(f"Common columns for kol_character: {common_columns}")
        
        # Synchronize each record
        inserted_count = 0
        updated_count = 0
        error_count = 0
        
        for record in kol_records:
            try:
                # Convert SQLite row to dict
                record_dict = dict(record)
                
                # Get kol_id
                kol_id = record_dict.get('kol_id')
                
                if not kol_id:
                    logging.warning(f"Skipping record with no kol_id: {record_dict}")
                    continue
                
                # Get kol_screen_name using the hierarchical approach
                kol_screen_name = get_kol_screen_name(
                    kol_id,
                    record_dict.get('kol_screen_name'),
                    record_dict.get('url'),
                    record_dict.get('screen_name')
                )
                
                # Update the record_dict with the kol_screen_name
                record_dict['kol_screen_name'] = kol_screen_name
                
                # Check if the record exists in MySQL
                mysql_cursor.execute("SELECT id FROM kol_character WHERE kol_id = %s", (kol_id,))
                existing_record = mysql_cursor.fetchone()
                
                if existing_record:
                    # Update existing record
                    if not test_mode:
                        # Build the update query
                        update_columns = [f"{col} = %s" for col in common_columns if col != 'id']
                        update_values = [record_dict.get(col) for col in common_columns if col != 'id']
                        update_values.append(kol_id)
                        
                        update_query = f"UPDATE kol_character SET {', '.join(update_columns)} WHERE kol_id = %s"
                        
                        mysql_cursor.execute(update_query, update_values)
                        updated_count += 1
                        
                        if verbose:
                            logging.info(f"Updated record for kol_id {kol_id}")
                    else:
                        if verbose:
                            logging.info(f"Test mode: Would update record for kol_id {kol_id}")
                        updated_count += 1
                else:
                    # Insert new record
                    if not test_mode:
                        # Build the insert query
                        insert_columns = [col for col in common_columns if col != 'id']
                        insert_values = [record_dict.get(col) for col in common_columns if col != 'id']
                        
                        insert_query = f"INSERT INTO kol_character ({', '.join(insert_columns)}) VALUES ({', '.join(['%s'] * len(insert_columns))})"
                        
                        mysql_cursor.execute(insert_query, insert_values)
                        inserted_count += 1
                        
                        if verbose:
                            logging.info(f"Inserted record for kol_id {kol_id}")
                    else:
                        if verbose:
                            logging.info(f"Test mode: Would insert record for kol_id {kol_id}")
                        inserted_count += 1
            
            except Exception as e:
                logging.error(f"MySQL error {'inserting' if not existing_record else 'updating'} record for kol_id {kol_id}: {str(e)}")
                error_count += 1
        
        # Commit changes
        if not test_mode:
            mysql_conn.commit()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logging.info(f"Synchronization completed in {duration:.2f} seconds")
        logging.info(f"Inserted: {inserted_count}, Updated: {updated_count}, Errors: {error_count}")
        
        return True
    
    except Exception as e:
        logging.error(f"Error synchronizing kol_character: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Synchronize kol_character data from SQLite to MySQL')
    parser.add_argument('--sqlite-db', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db',
                        help='Path to SQLite database')
    parser.add_argument('--lock-file', type=str, default='/home/ubuntu/nitterlocal/data/kol_character_sync_lock.pid',
                        help='Lock file path')
    parser.add_argument('--lock-timeout', type=int, default=30,
                        help='Lock timeout in seconds')
    parser.add_argument('--no-lock', action='store_true',
                        help='Disable the lock mechanism')
    parser.add_argument('--test', action='store_true',
                        help='Run in test mode (no actual changes)')
    parser.add_argument('--verbose', action='store_true',
                        help='Print verbose output')
    
    args = parser.parse_args()
    
    # Use a lock to prevent overlapping executions
    lock_file = args.lock_file
    
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
            return 1
        
        try:
            # Get SQLite connection
            sqlite_conn = get_sqlite_connection(args.sqlite_db)
            if not sqlite_conn:
                return 1
            
            # Get MySQL connection
            mysql_conn = get_mysql_connection()
            if not mysql_conn:
                sqlite_conn.close()
                return 1
            
            # Synchronize kol_character
            success = sync_kol_character(sqlite_conn, mysql_conn, args.test, args.verbose)
            
            # Close connections
            mysql_conn.close()
            sqlite_conn.close()
            
            return 0 if success else 1
        except Exception as e:
            logging.error(f"Error in main function: {str(e)}")
            return 1

if __name__ == "__main__":
    sys.exit(main())
