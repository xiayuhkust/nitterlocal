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
        
        logging.info(f"Attempting to connect to MySQL database at: {mysql_host}:{mysql_port}")
        logging.info(f"MySQL database: {mysql_database}, User: {mysql_user}")
        
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
        
        # Verify connection by checking tables
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        table_names = [list(table.values())[0] for table in tables]
        logging.info(f"MySQL database tables: {table_names}")
        
        # Check if kol_info table exists
        if 'kol_info' not in table_names:
            logging.error(f"kol_info table not found in MySQL database")
        else:
            # Check record count
            cursor.execute("SELECT COUNT(*) as count FROM kol_info;")
            result = cursor.fetchone()
            count = result['count'] if result else 0
            logging.info(f"kol_info table contains {count} records")
        
        return conn
    
    except Exception as e:
        logging.error(f"Error connecting to MySQL: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise Exception(f"Error connecting to MySQL: {str(e)}")

def get_sqlite_connection(db_path=None):
    """Get a connection to the SQLite database"""
    try:
        # If no path provided, try to determine it automatically
        if db_path is None:
            # Get the script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Try different possible paths
            possible_paths = [
                os.path.join(os.path.dirname(os.path.dirname(script_dir)), 'data', 'local_database.db'),  # /home/ubuntu/nitterlocal/data/local_database.db
                os.path.join('/home/ubuntu/nitterlocal/data', 'local_database.db'),  # Hardcoded path
                os.path.join(os.getcwd(), 'data', 'local_database.db')  # Current working directory
            ]
            
            # Log all possible paths we're checking
            logging.info(f"Checking possible database paths:")
            for path in possible_paths:
                logging.info(f"  - {path} (exists: {os.path.exists(path)})")
            
            # Use the first path that exists
            for path in possible_paths:
                if os.path.exists(path):
                    db_path = path
                    logging.info(f"Using database path: {db_path}")
                    break
            
            # If no path exists, use the default
            if db_path is None:
                db_path = possible_paths[0]
                logging.warning(f"No database found, using default path: {db_path}")
        
        logging.info(f"Attempting to connect to SQLite database at: {db_path}")
        
        # Check if database file exists
        if not os.path.exists(db_path):
            logging.error(f"SQLite database file does not exist: {db_path}")
            # Try to find database in parent directories
            parent_dir = os.path.dirname(os.path.dirname(db_path))
            logging.info(f"Checking parent directory: {parent_dir}")
            # Limit directory depth to 3 levels
            for root, dirs, files in os.walk(parent_dir, topdown=True):
                # Limit depth by modifying dirs in-place
                if root.count(os.sep) - parent_dir.count(os.sep) >= 3:
                    dirs[:] = []  # Don't go deeper than 3 levels
                for file in files:
                    if file.endswith('.db'):
                        found_path = os.path.join(root, file)
                        logging.info(f"Found database file: {found_path}")
                        # Use the first database file found
                        db_path = found_path
                        break
                if db_path != possible_paths[0]:
                    break
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Verify connection by checking tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        logging.info(f"SQLite database tables: {table_names}")
        
        # Check if url_tracking table exists
        if 'url_tracking' not in table_names:
            logging.error(f"url_tracking table not found in SQLite database")
        else:
            # Check record count
            cursor.execute("SELECT COUNT(*) FROM url_tracking;")
            count = cursor.fetchone()[0]
            logging.info(f"url_tracking table contains {count} records")
            
            # Check active records
            cursor.execute("SELECT COUNT(*) FROM url_tracking WHERE status = 'active';")
            active_count = cursor.fetchone()[0]
            logging.info(f"url_tracking table contains {active_count} active records")
        
        return conn
    
    except Exception as e:
        logging.error(f"Error connecting to SQLite: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
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

def sync_url_tracking(sqlite_conn, mysql_conn, test_mode=False, verbose=False, limit=None, specific_url=None):
    """Synchronize url_tracking table from SQLite to MySQL"""
    try:
        # Track start time for performance measurement
        start_time = time.time()
        
        # Get SQLite cursor
        sqlite_cursor = sqlite_conn.cursor()
        
        # Get MySQL cursor
        mysql_cursor = mysql_conn.cursor()
        
        # Get url_tracking records from SQLite
        query = "SELECT * FROM url_tracking"
        
        # Add specific URL filter if provided
        if specific_url:
            query += f" WHERE url = ?"
        elif limit:
            query += f" LIMIT {limit}"
        
        logging.info(f"Executing SQLite query: {query}")
        if specific_url:
            sqlite_cursor.execute(query, (specific_url,))
        else:
            sqlite_cursor.execute(query)
        rows = sqlite_cursor.fetchall()
        
        # Always log the record count, not just in verbose mode
        logging.info(f"Found {len(rows)} url_tracking records in SQLite")
        
        # Log the first few records for debugging
        if len(rows) > 0:
            sample_size = min(3, len(rows))
            logging.info(f"Sample of first {sample_size} records:")
            for i in range(sample_size):
                row = rows[i]
                row_dict = {key: row[key] for key in row.keys()}
                logging.info(f"Record {i+1}: {row_dict}")
                
                # Log specific fields that affect filtering
                status = row['status'] if 'status' in row.keys() else 'unknown'
                type_val = row['type'] if 'type' in row.keys() else 'unknown'
                screen_name = row['screen_name'] if 'screen_name' in row.keys() else 'unknown'
                logging.info(f"Record {i+1} filtering fields - status: '{status}', type: '{type_val}', screen_name: '{screen_name}'")
        else:
            logging.warning("No records found in url_tracking table")
        
        # Get MySQL table columns
        mysql_columns = get_mysql_table_columns(mysql_conn, 'kol_info')
        if verbose:
            logging.debug(f"MySQL columns: {mysql_columns}")
        
        # Get MySQL table constraints
        mysql_constraints = get_mysql_table_constraints(mysql_conn, 'kol_info')
        
        # Map SQLite columns to MySQL columns
        column_mapping = {
            'id': 'id',  # Add id mapping for primary key
            'url': 'url',  # Keep url mapping
            'user_id': 'kol_id',
            'screen_name': 'kol_screen_name',
            'kol_name': 'kol_name',  # Ensure kol_name is properly mapped
            'description': 'description',
            'followers_count': 'followers_count',
            'following_count': 'following_count',
            'profile_image_url': 'profile_image_url',
            'profile_banner_url': 'profile_banner_url',
            'verified': 'verified',
            'location': 'location',
            'type': 'first_category',
            'subtype': 'second_category'
        }
        
        # Debug log column mapping
        logging.info(f"Column mapping: {column_mapping}")
        logging.info(f"MySQL columns: {mysql_columns}")
        
        # Process each record
        processed_count = 0
        insert_count = 0
        update_count = 0
        error_count = 0
        
        for row in rows:
            # Convert SQLite row to dict for consistent access
            row_dict = dict(row)
            
            # Debug log for each row
            if verbose:
                logging.debug(f"Processing row: {row_dict['url'] if 'url' in row_dict else 'unknown'}")
            
            # Skip records that are not active
            if row_dict['status'] != 'active':
                # Always log skipped records, not just in verbose mode
                logging.info(f"Skipping inactive record: {row_dict['url']}, status: {row_dict['status']}")
                continue
            
            # Skip records that are not KOLs - case insensitive comparison
            if row_dict['type'].lower() != 'kol':
                # Always log skipped records, not just in verbose mode
                logging.info(f"Skipping non-kol record: {row_dict['url']}, type: {row_dict['type']}")
                continue
                
            # Log that we're processing this record
            logging.info(f"Processing record: {row_dict['url']}, status: {row_dict['status']}, type: {row_dict['type']}")
            
            # Prepare MySQL data
            mysql_data = {}
            
            # Extract screen_name from URL if not present
            if 'screen_name' not in row_dict or not row_dict['screen_name']:
                url = row_dict.get('url', '')
                if 'twitter.com/' in url:
                    screen_name = url.split('twitter.com/')[-1].split('/')[0].split('?')[0]
                    row_dict['screen_name'] = screen_name
                    logging.info(f"Extracted screen_name '{screen_name}' from URL: {url}")
            
            # Map columns from SQLite to MySQL
            for sqlite_column, mysql_column in column_mapping.items():
                if sqlite_column in row_dict.keys() and mysql_column in mysql_columns:
                    mysql_data[mysql_column] = convert_value_for_mysql(row_dict[sqlite_column], mysql_column, mysql_constraints)
            
            # Ensure kol_screen_name is always set (required field)
            if 'kol_screen_name' not in mysql_data or not mysql_data['kol_screen_name']:
                if 'url' in row_dict:
                    url = row_dict['url']
                    if 'twitter.com/' in url:
                        screen_name = url.split('twitter.com/')[-1].split('/')[0].split('?')[0]
                        mysql_data['kol_screen_name'] = screen_name
                        logging.info(f"Set kol_screen_name to '{screen_name}' from URL: {url}")
                elif 'kol_name' in mysql_data:
                    # Use kol_name as fallback
                    mysql_data['kol_screen_name'] = mysql_data['kol_name']
                    logging.info(f"Set kol_screen_name to kol_name: {mysql_data['kol_name']}")
                else:
                    # Generate a placeholder screen name
                    placeholder = f"user_{processed_count}"
                    mysql_data['kol_screen_name'] = placeholder
                    logging.info(f"Set kol_screen_name to placeholder: {placeholder}")
            
            # Debug log for MySQL data
            if verbose:
                logging.debug(f"MySQL data prepared: {mysql_data}")
            
            # Check if the record exists in MySQL - try multiple keys in order of preference
            lookup_found = False
            
            # First try by id if available
            if 'id' in mysql_data:
                mysql_cursor.execute("SELECT * FROM kol_info WHERE id = %s", (mysql_data['id'],))
                logging.info(f"Checking if record exists for id: {mysql_data['id']}")
                lookup_found = True
            # Then try by kol_screen_name
            elif 'kol_screen_name' in mysql_data:
                mysql_cursor.execute("SELECT * FROM kol_info WHERE kol_screen_name = %s", (mysql_data['kol_screen_name'],))
                logging.info(f"Checking if record exists for screen_name: {mysql_data['kol_screen_name']}")
                lookup_found = True
            # Then try by kol_id
            elif 'kol_id' in mysql_data:
                mysql_cursor.execute("SELECT * FROM kol_info WHERE kol_id = %s", (mysql_data['kol_id'],))
                logging.info(f"Checking if record exists for kol_id: {mysql_data['kol_id']}")
                lookup_found = True
            # Finally try by url
            elif 'url' in mysql_data:
                mysql_cursor.execute("SELECT * FROM kol_info WHERE url = %s", (mysql_data['url'],))
                logging.info(f"Checking if record exists for url: {mysql_data['url']}")
                lookup_found = True
            
            # Skip if no lookup key found
            if not lookup_found:
                logging.warning(f"Skipping record without id, kol_id, kol_screen_name, or url")
                continue
                
            # Log lookup key for debugging
            lookup_key = mysql_data.get('id', mysql_data.get('kol_id', mysql_data.get('kol_screen_name', mysql_data.get('url', 'unknown'))))
            if verbose:
                logging.debug(f"Checking if record exists for {lookup_key}")
            
            # Get the existing record
            existing_record = mysql_cursor.fetchone()
            
            if existing_record:
                # Update the record
                update_columns = []
                update_values = []
                
                for column, value in mysql_data.items():
                    # Skip the column used for WHERE clause
                    if column not in ['id', 'kol_id', 'kol_screen_name', 'url']:
                        update_columns.append(f"{column} = %s")
                        update_values.append(value)
                
                # Add the WHERE clause value based on available keys in order of preference
                if 'id' in mysql_data:
                    update_values.append(mysql_data['id'])
                    update_query = f"UPDATE kol_info SET {', '.join(update_columns)} WHERE id = %s"
                elif 'kol_id' in mysql_data:
                    update_values.append(mysql_data['kol_id'])
                    update_query = f"UPDATE kol_info SET {', '.join(update_columns)} WHERE kol_id = %s"
                elif 'kol_screen_name' in mysql_data:
                    update_values.append(mysql_data['kol_screen_name'])
                    update_query = f"UPDATE kol_info SET {', '.join(update_columns)} WHERE kol_screen_name = %s"
                else:
                    update_values.append(mysql_data['url'])
                    update_query = f"UPDATE kol_info SET {', '.join(update_columns)} WHERE url = %s"
                
                # Log the update query for debugging
                if verbose:
                    logging.debug(f"Update query: {update_query}")
                    logging.debug(f"Update values: {update_values}")
                
                # Execute the update query
                if not test_mode:
                    try:
                        mysql_cursor.execute(update_query, update_values)
                        # Remove unread_result check that was causing errors
                        
                        update_count += 1
                    except pymysql.Error as e:
                        lookup_key = mysql_data.get('kol_id', mysql_data.get('kol_screen_name', 'unknown'))
                        logging.error(f"MySQL error updating {lookup_key}: {str(e)}")
                        logging.error(f"Update query: {update_query}")
                        logging.error(f"Update values: {update_values}")
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
                
                # Always log insert operations
                logging.info(f"Inserting new record with {len(insert_columns)} columns")
                
                # Execute the insert query
                if not test_mode:
                    # Always log the query details, not just in verbose mode
                    if verbose:
                        logging.debug(f"Insert query: {insert_query}")
                        logging.debug(f"Insert values: {insert_values}")
                    try:
                        mysql_cursor.execute(insert_query, insert_values)
                        # Remove unread_result check that was causing errors
                        
                        insert_count += 1
                        logging.info(f"Successfully inserted record")
                    except pymysql.Error as e:
                        lookup_key = mysql_data.get('id', mysql_data.get('kol_id', mysql_data.get('kol_screen_name', mysql_data.get('url', 'unknown'))))
                        logging.error(f"MySQL error inserting {lookup_key}: {str(e)}")
                        logging.error(f"Insert query: {insert_query}")
                        logging.error(f"Insert values: {insert_values}")
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
        
        # Always log summary, not just in verbose mode
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
    parser.add_argument('--specific-url', type=str, help='Process only a specific URL')
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
        result = sync_url_tracking(sqlite_conn, mysql_conn, test_mode=args.test, verbose=args.verbose, limit=args.limit, specific_url=args.specific_url)
        
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
