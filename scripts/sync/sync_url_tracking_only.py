#!/usr/bin/env python3
"""
Synchronize url_tracking table from SQLite to MySQL.
"""

import os
import sys
import time
import logging
import argparse
import sqlite3
import pymysql
from pymysql import cursors
import traceback
from datetime import datetime
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
            cursorclass=cursors.DictCursor
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
    columns = [row['Field'] for row in cursor.fetchall()]  # Access by key since we're using DictCursor
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
        # Access by key since we're using DictCursor
        column_name = row['COLUMN_NAME']
        is_nullable = row['IS_NULLABLE']
        column_key = row['COLUMN_KEY']
        data_type = row['DATA_TYPE']
        
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

def sync_url_tracking(sqlite_conn, mysql_conn, test_mode=False, verbose=False, limit=None):
    """Synchronize url_tracking table from SQLite to MySQL"""
    try:
        # Get SQLite cursor
        sqlite_cursor = sqlite_conn.cursor()
        
        # Get MySQL cursor
        mysql_cursor = mysql_conn.cursor()
        
        # Get url_tracking records from SQLite
        query = "SELECT * FROM url_tracking"
        if limit:
            query += f" LIMIT {limit}"
        
        sqlite_cursor.execute(query)
        rows = sqlite_cursor.fetchall()
        
        if verbose:
            logging.info(f"Found {len(rows)} url_tracking records in SQLite")
        
        # Get MySQL table columns
        mysql_columns = get_mysql_table_columns(mysql_conn, 'kol_info')
        if verbose:
            logging.debug(f"MySQL columns: {mysql_columns}")
        
        # Get MySQL table constraints
        mysql_constraints = get_mysql_table_constraints(mysql_conn, 'kol_info')
        
        # Map SQLite columns to MySQL columns
        column_mapping = {
            'user_id': 'kol_id',
            'screen_name': 'kol_screen_name',
            'kol_name': 'kol_name',
            'description': 'description',
            'followers_count': 'followers_count',
            'following_count': 'following_count'
        }
        
        # Process each record
        processed_count = 0
        insert_count = 0
        update_count = 0
        error_count = 0
        
        for row in rows:
            # Debug log for each row
            # SQLite rows still use dictionary-like access
            if verbose:
                logging.debug(f"Processing row: {row['url'] if 'url' in row.keys() else 'unknown'}")
            
            # Skip records that are not active
            if row['status'] != 'active':
                continue
            
            # Skip records that are not KOLs
            if row['type'] != 'kol':
                continue
            
            # Prepare MySQL data
            mysql_data = {}
            for sqlite_column, mysql_column in column_mapping.items():
                if sqlite_column in row.keys() and mysql_column in mysql_columns:
                    mysql_data[mysql_column] = convert_value_for_mysql(row[sqlite_column], mysql_column, mysql_constraints)
            
            # Check if the record exists in MySQL
            if 'kol_screen_name' in mysql_data:
                mysql_cursor.execute("SELECT * FROM kol_info WHERE kol_screen_name = %s", (mysql_data['kol_screen_name'],))
                if verbose:
                    logging.debug(f"Checking if record exists for screen_name: {mysql_data['kol_screen_name']}")
            elif 'kol_id' in mysql_data:
                mysql_cursor.execute("SELECT * FROM kol_info WHERE kol_id = %s", (mysql_data['kol_id'],))
                if verbose:
                    logging.debug(f"Checking if record exists for kol_id: {mysql_data['kol_id']}")
            else:
                if verbose:
                    logging.debug(f"Skipping record without kol_id or kol_screen_name")
                continue
            if verbose:
                lookup_key = mysql_data.get('kol_id', mysql_data.get('kol_screen_name', 'unknown'))
                logging.debug(f"Checking if record exists for {lookup_key}")
            
            # Get the existing record
            existing_record = mysql_cursor.fetchone()
            
            if existing_record:
                # Update the record
                update_columns = []
                update_values = []
                
                for column, value in mysql_data.items():
                    if column != 'kol_screen_name':  # Skip the primary key
                        update_columns.append(f"{column} = %s")
                        update_values.append(value)
                
                # Add the WHERE clause value
                if 'kol_id' in mysql_data:
                    update_values.append(mysql_data['kol_id'])
                    update_query = f"UPDATE kol_info SET {', '.join(update_columns)} WHERE kol_id = %s"
                else:
                    update_values.append(mysql_data['kol_screen_name'])
                    update_query = f"UPDATE kol_info SET {', '.join(update_columns)} WHERE kol_screen_name = %s"
                
                # Execute the update query
                if not test_mode:
                    try:
                        mysql_cursor.execute(update_query, update_values)
                        # Remove unread_result check that was causing errors
                        
                        update_count += 1
                    except pymysql.Error as e:
                        lookup_key = mysql_data.get('kol_id', mysql_data.get('kol_screen_name', 'unknown'))
                        logging.error(f"MySQL error updating {lookup_key}: {str(e)}")
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
                insert_query = f"INSERT INTO kol_info ({columns_str}) VALUES ({placeholders})"
                
                # Execute the insert query
                if not test_mode:
                    if verbose:
                        logging.debug(f"Insert query: {insert_query}")
                        logging.debug(f"Insert values: {insert_values}")
                    try:
                        mysql_cursor.execute(insert_query, insert_values)
                        # Remove unread_result check that was causing errors
                        
                        insert_count += 1
                    except pymysql.Error as e:
                        lookup_key = mysql_data.get('kol_id', mysql_data.get('kol_screen_name', 'unknown'))
                        logging.error(f"MySQL error inserting {lookup_key}: {str(e)}")
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
        error_msg = f"Error synchronizing url_tracking: {str(e)}"
        logging.error(error_msg)
        logging.error(f"Traceback: {traceback.format_exc()}")
        if not test_mode:
            mysql_conn.rollback()
        raise Exception(error_msg)

def main():
    """Main function"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Synchronize url_tracking table from SQLite to MySQL')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no changes to MySQL)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-lock', action='store_true', help='Disable lock mechanism')
    parser.add_argument('--lock-timeout', type=int, default=60, help='Lock timeout in seconds')
    parser.add_argument('--limit', type=int, help='Limit the number of records to process')
    args = parser.parse_args()
    
    # Set up lock file
    lock_file = '/home/ubuntu/nitterlocal/data/url_tracking_sync_lock.pid'
    
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
        logging.info(f"Starting url_tracking synchronization at {datetime.now().isoformat()}")
        
        # Connect to databases
        sqlite_conn = get_sqlite_connection()
        mysql_conn = get_mysql_connection()
        
        # Synchronize url_tracking table
        result = sync_url_tracking(sqlite_conn, mysql_conn, test_mode=args.test, verbose=args.verbose, limit=args.limit)
        
        # Close connections
        sqlite_conn.close()
        mysql_conn.close()
        
        # Release lock if not disabled
        if lock:
            lock.release()
            logging.info(f"Released lock: {lock_file}")
        
        return 0
    
    except Exception as e:
        logging.error(f"Error in url_tracking synchronization: {str(e)}")
        logging.debug(f"Traceback: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
