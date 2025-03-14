#!/usr/bin/env python3
"""
Script to test database processing and identify issues with kol_id and screen_name formatting.
"""

import os
import sys
import logging
import sqlite3
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Default paths
DB_PATH = '/home/ubuntu/nitterlocal/data/local_database.db'
EXCEL_PATH = '/home/ubuntu/nitterlocal/uploads/20250313_083733_c8dbf78e_test file with spaces.xlsx'

def create_test_excel():
    """Create a test Excel file with Twitter URLs"""
    try:
        # Create a temporary directory if it doesn't exist
        os.makedirs('/tmp/test_files', exist_ok=True)
        
        # Create a test Excel file
        df = pd.DataFrame({
            'Twitter url': [
                'https://twitter.com/elonmusk',
                'https://twitter.com/vitalikbuterin',
                'https://twitter.com/cz_binance'
            ],
            'first category': ['kol', 'kol', 'kol'],
            'second_category': ['-', '-', '-'],
            'bio': ['CEO of Tesla and SpaceX', 'Ethereum creator', 'Binance CEO']
        })
        
        excel_path = '/tmp/test_files/test_twitter_urls.xlsx'
        df.to_excel(excel_path, index=False)
        
        logging.info(f"Created test Excel file at {excel_path}")
        return excel_path
    except Exception as e:
        logging.error(f"Error creating test Excel file: {str(e)}")
        return None

def check_database_tables():
    """Check the database tables and their contents"""
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if the tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("Tables in the database:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Check the url_tracking table
        try:
            cursor.execute("SELECT * FROM url_tracking LIMIT 10")
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            print("\nurl_tracking table:")
            print(f"Columns: {columns}")
            print(f"Row count: {len(rows)}")
            
            for row in rows:
                row_dict = dict(zip(columns, row))
                print(f"Row: {row_dict}")
        except Exception as e:
            print(f"Error checking url_tracking table: {str(e)}")
        
        # Check the kol_character table
        try:
            cursor.execute("SELECT * FROM kol_character LIMIT 10")
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            print("\nkol_character table:")
            print(f"Columns: {columns}")
            print(f"Row count: {len(rows)}")
            
            for row in rows:
                row_dict = dict(zip(columns, row))
                print(f"Row: {row_dict}")
        except Exception as e:
            print(f"Error checking kol_character table: {str(e)}")
        
        # Close the connection
        conn.close()
    except Exception as e:
        logging.error(f"Error checking database tables: {str(e)}")

def trace_process_excel_execution():
    """Trace the execution of process_excel.py script"""
    try:
        # Import the process_excel module
        sys.path.append('/home/ubuntu/repos/nitterlocal/scripts/database')
        
        # Try to import the module
        try:
            from process_excel import extract_twitter_handle, add_url_to_tracking, add_kol_character, process_excel_file
            print("\nSuccessfully imported process_excel module")
        except ImportError as e:
            print(f"Error importing process_excel module: {str(e)}")
            return
        
        # Test extract_twitter_handle function
        print("\nTesting extract_twitter_handle function:")
        urls = [
            'https://twitter.com/elonmusk',
            'https://x.com/vitalikbuterin',
            'https://twitter.com/cz_binance/'
        ]
        
        for url in urls:
            handle = extract_twitter_handle(url)
            print(f"URL: {url} -> Handle: {handle}")
        
        # Create a test database connection
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        # Create the url_tracking table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS url_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            type TEXT,
            subtype TEXT,
            user_id TEXT,
            description TEXT,
            status TEXT,
            last_checked TEXT,
            error_count INTEGER DEFAULT 0,
            tweet_count INTEGER DEFAULT 0,
            added_at TEXT,
            UNIQUE(url)
        )
        ''')
        
        # Create the kol_character table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS kol_character (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kol_id TEXT,
            kol_screen_name TEXT NOT NULL,
            bio TEXT,
            lore TEXT,
            knowledge TEXT,
            postExamples TEXT,
            topics TEXT,
            style_all TEXT,
            style_chat TEXT,
            style_post TEXT,
            adjectives TEXT,
            UNIQUE(kol_screen_name)
        )
        ''')
        
        # Test add_url_to_tracking function
        print("\nTesting add_url_to_tracking function:")
        url = 'https://twitter.com/elonmusk'
        user_id = '44196397'  # Elon Musk's Twitter ID
        
        add_url_to_tracking(conn, url, user_id)
        
        cursor.execute("SELECT * FROM url_tracking")
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        for row in rows:
            row_dict = dict(zip(columns, row))
            print(f"url_tracking row: {row_dict}")
        
        # Test add_kol_character function
        print("\nTesting add_kol_character function:")
        kol_data = {
            'kol_id': user_id,
            'kol_screen_name': 'elonmusk',
            'bio': 'CEO of Tesla and SpaceX'
        }
        
        add_kol_character(conn, kol_data)
        
        cursor.execute("SELECT * FROM kol_character")
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        for row in rows:
            row_dict = dict(zip(columns, row))
            print(f"kol_character row: {row_dict}")
        
        # Close the connection
        conn.close()
    except Exception as e:
        logging.error(f"Error tracing process_excel execution: {str(e)}")

def main():
    """Main function"""
    print("=== Database Processing Test ===")
    
    # Check the database tables
    print("\n=== Checking Database Tables ===")
    check_database_tables()
    
    # Trace the process_excel execution
    print("\n=== Tracing process_excel Execution ===")
    trace_process_excel_execution()

if __name__ == "__main__":
    main()
