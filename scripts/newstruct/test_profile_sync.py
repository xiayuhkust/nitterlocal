#!/usr/bin/env python3
"""
Test script to verify the entire workflow from Twitter API to MySQL.
This script will:
1. Fetch profile data for a Twitter handle
2. Update the SQLite database
3. Synchronize the data to MySQL
4. Verify the data in both databases
"""

import os
import sys
import logging
import argparse
import sqlite3
import pymysql
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the necessary modules
from scripts.newstruct.fill_profiledata import ProfileUpdater
from scripts.sync.sync_url_tracking_only import sync_url_tracking, get_sqlite_connection, get_mysql_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_profile_sync(handle, db_path=None):
    """Test the entire profile synchronization workflow"""
    logging.info(f"Testing profile synchronization for handle: {handle}")
    
    # Step 1: Initialize the profile updater
    updater = ProfileUpdater(db_path)
    
    # Step 2: Update the profile in SQLite
    result = updater.update_profile_by_handle(handle)
    if not result:
        logging.error(f"Failed to update profile for handle: {handle}")
        return False
    
    logging.info(f"Successfully updated profile for handle: {handle}")
    
    # Step 3: Connect to databases
    sqlite_conn = get_sqlite_connection(db_path)
    mysql_conn = get_mysql_connection()
    
    # Step 4: Synchronize only the specific handle to MySQL
    try:
        # Get the URL for the handle
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT url FROM url_tracking WHERE url LIKE ?", (f"%twitter.com/{handle}%",))
        url_result = cursor.fetchone()
        
        if not url_result:
            logging.error(f"No URL found in SQLite for handle: {handle}")
            sqlite_conn.close()
            mysql_conn.close()
            return False
            
        url = url_result[0]
        logging.info(f"Found URL for handle {handle}: {url}")
        
        # Synchronize just this one record
        cursor = mysql_conn.cursor()
        # Use test_mode=False to actually update the MySQL database
        result = sync_url_tracking(sqlite_conn, mysql_conn, test_mode=False, verbose=True, specific_url=url)
        logging.info(f"Synchronized record for {handle} to MySQL")
    except Exception as e:
        logging.error(f"Error synchronizing data to MySQL: {str(e)}")
        return False
    finally:
        sqlite_conn.close()
        mysql_conn.close()
    
    # Step 5: Verify the data in SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT kol_name FROM url_tracking WHERE url LIKE ?", (f"%twitter.com/{handle}%",))
    result = cursor.fetchone()
    
    if not result:
        logging.error(f"No record found in SQLite for handle: {handle}")
        conn.close()
        return False
    
    kol_name_sqlite = result[0]
    logging.info(f"SQLite kol_name: {kol_name_sqlite}")
    
    conn.close()
    
    # Step 6: Verify the data in MySQL
    mysql_conn = get_mysql_connection()
    cursor = mysql_conn.cursor()
    
    cursor.execute("SELECT kol_name FROM kol_info WHERE kol_screen_name = %s", (handle,))
    result = cursor.fetchone()
    
    if not result:
        logging.error(f"No record found in MySQL for handle: {handle}")
        mysql_conn.close()
        return False
    
    kol_name_mysql = result['kol_name']
    logging.info(f"MySQL kol_name: {kol_name_mysql}")
    
    mysql_conn.close()
    
    # Step 7: Compare the values
    if kol_name_sqlite == kol_name_mysql:
        logging.info(f"Verification successful! kol_name matches in both databases: {kol_name_sqlite}")
        return True
    else:
        logging.error(f"Verification failed! kol_name does not match: SQLite={kol_name_sqlite}, MySQL={kol_name_mysql}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test profile synchronization workflow')
    parser.add_argument('--handle', type=str, default='cz_binance', help='Twitter handle to test')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the SQLite database')
    
    args = parser.parse_args()
    
    # Resolve database path
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', args.db_path))
    
    # Test profile synchronization
    if test_profile_sync(args.handle, db_path):
        print(f"Profile synchronization test passed for handle: {args.handle}")
        return 0
    else:
        print(f"Profile synchronization test failed for handle: {args.handle}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
