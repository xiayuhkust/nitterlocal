#!/usr/bin/env python3
"""
Script to clear MySQL tables and then sync data from SQLite.
This script:
1. Clears the specified tables in MySQL (kol_info, kol_tweet, kol_character)
2. Runs the existing sync scripts to repopulate the tables
"""

import os
import sys
import time
import logging
import argparse
import subprocess
import mysql.connector
from datetime import datetime
import dotenv

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_mysql_connection():
    """Get a connection to the MySQL database"""
    try:
        # Load environment variables from .env file if it exists
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        if os.path.exists(dotenv_path):
            dotenv.load_dotenv(dotenv_path)
        
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

def clear_mysql_table(mysql_conn, table_name):
    """Clear a MySQL table"""
    cursor = mysql_conn.cursor()
    
    try:
        # Get row count before clearing
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        before_count = cursor.fetchone()[0]
        
        # Clear the table
        cursor.execute(f"DELETE FROM {table_name}")
        mysql_conn.commit()
        
        # Get row count after clearing
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        after_count = cursor.fetchone()[0]
        
        logging.info(f"Cleared table {table_name}: {before_count} rows deleted, {after_count} rows remaining")
        return before_count
    
    except Exception as e:
        logging.error(f"Error clearing table {table_name}: {str(e)}")
        return 0
    
    finally:
        cursor.close()

def run_sync_script(script_name, args=None):
    """Run a sync script"""
    try:
        # Build command
        cmd = [sys.executable, script_name]
        
        # Add arguments if provided
        if args:
            cmd.extend(args)
        
        # Log command
        logging.info(f"Running: {' '.join(cmd)}")
        
        # Run command
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()
        
        # Log result
        if result.returncode == 0:
            logging.info(f"Successfully ran {script_name} in {end_time - start_time:.2f} seconds")
            logging.info(f"Output: {result.stdout.strip()}")
            return True
        else:
            logging.error(f"Error running {script_name}: {result.stderr.strip()}")
            return False
    
    except Exception as e:
        logging.error(f"Exception running {script_name}: {str(e)}")
        return False

def clear_and_sync_tables(tables=None, lock_timeout=60, since_days=30):
    """Clear and sync tables"""
    # Default tables to clear and sync
    default_tables = ['kol_info', 'kol_tweet', 'kol_character']
    
    # Use specified tables or default tables
    tables_to_sync = tables if tables else default_tables
    
    # Validate tables
    for table in tables_to_sync:
        if table not in default_tables:
            logging.warning(f"Unknown table: {table}")
    
    # Filter valid tables
    tables_to_sync = [table for table in tables_to_sync if table in default_tables]
    
    if not tables_to_sync:
        logging.error("No valid tables specified")
        return False
    
    logging.info(f"Tables to clear and sync: {tables_to_sync}")
    
    # Connect to MySQL
    try:
        mysql_conn = get_mysql_connection()
    except Exception as e:
        logging.error(f"Failed to connect to MySQL: {str(e)}")
        return False
    
    # Clear tables
    try:
        for table in tables_to_sync:
            clear_mysql_table(mysql_conn, table)
    except Exception as e:
        logging.error(f"Error clearing tables: {str(e)}")
        mysql_conn.close()
        return False
    
    # Close MySQL connection
    mysql_conn.close()
    
    # Sync tables
    sync_scripts = {
        'kol_info': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sync', 'sync_url_tracking_only.py'),
        'kol_tweet': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sync', 'sync_tweets_only.py'),
        'kol_character': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sync', 'sync_kol_character_only.py')
    }
    
    sync_args = {
        'kol_info': ['--lock-timeout', str(lock_timeout)],
        'kol_tweet': ['--since-days', str(since_days), '--lock-timeout', str(lock_timeout)],
        'kol_character': ['--lock-timeout', str(lock_timeout)]
    }
    
    # Run sync scripts
    for table in tables_to_sync:
        if table in sync_scripts:
            script_path = sync_scripts[table]
            args = sync_args[table]
            
            if os.path.exists(script_path):
                logging.info(f"Syncing table: {table}")
                success = run_sync_script(script_path, args)
                
                if not success:
                    logging.error(f"Failed to sync table: {table}")
            else:
                logging.error(f"Sync script not found: {script_path}")
    
    logging.info("Clear and sync process completed")
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Clear MySQL tables and sync data from SQLite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clear and sync all tables
  python clear_and_sync_mysql.py
  
  # Clear and sync specific tables
  python clear_and_sync_mysql.py --tables kol_info kol_tweet
  
  # Specify lock timeout and since days
  python clear_and_sync_mysql.py --lock-timeout 120 --since-days 60
"""
    )
    
    parser.add_argument(
        '--tables',
        nargs='+',
        choices=['kol_info', 'kol_tweet', 'kol_character'],
        help='Tables to clear and sync (default: all tables)'
    )
    
    parser.add_argument(
        '--lock-timeout',
        type=int,
        default=60,
        help='Lock timeout in seconds (default: 60)'
    )
    
    parser.add_argument(
        '--since-days',
        type=int,
        default=30,
        help='Number of days to sync tweets (default: 30)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Clear and sync tables
    clear_and_sync_tables(args.tables, args.lock_timeout, args.since_days)

if __name__ == "__main__":
    main()
