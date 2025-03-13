#!/usr/bin/env python3
"""
Test script to verify the kol_id fix in process_excel.py
"""

import os
import sys
import logging
import sqlite3
import pandas as pd
import tempfile
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Default paths
DB_PATH = '/home/ubuntu/nitterlocal/data/local_database.db'
UPLOAD_DIR = '/home/ubuntu/nitterlocal/uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

def create_test_excel():
    """Create a test Excel file with Twitter URLs"""
    try:
        # Create a test Excel file
        df = pd.DataFrame({
            'Twitter url': [
                'https://twitter.com/elonmusk',
                'https://twitter.com/vitalikbuterin',
                'https://twitter.com/cz_binance'
            ],
            'first category': ['kol', 'kol', 'kol'],
            'second_category': ['-', '-', '-']
        })
        
        # Save to a temporary file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_test_twitter_urls.xlsx"
        file_path = os.path.join(UPLOAD_DIR, filename)
        df.to_excel(file_path, index=False)
        
        logging.info(f"Created test Excel file at {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"Error creating test Excel file: {str(e)}")
        return None

def process_excel_file(excel_path):
    """Process the Excel file using the backend API"""
    try:
        # Import the database_sync module
        sys.path.append('/home/ubuntu/nitterlocal')
        from app.database_sync import process_excel_and_sync
        
        # Process the Excel file and synchronize data
        results = process_excel_and_sync(
            excel_path=excel_path,
            db_path=DB_PATH,
            sync_to_mysql=False,
            test_mode=True
        )
        
        logging.info(f"Excel processing results: {results}")
        return results
    except Exception as e:
        logging.error(f"Error processing Excel file: {str(e)}")
        return None

def check_database_tables():
    """Check the database tables and their contents"""
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check the kol_character table
        cursor.execute("SELECT * FROM kol_character")
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        print("\nkol_character table:")
        print(f"Columns: {columns}")
        print(f"Row count: {len(rows)}")
        
        for row in rows:
            row_dict = dict(zip(columns, row))
            print(f"Row: {row_dict}")
            
            # Check if kol_id is set correctly (should be numeric)
            if row_dict['kol_id'] == 'KOL' or row_dict['kol_id'] is None:
                print("ERROR: kol_id is not set correctly!")
            elif str(row_dict['kol_id']).isdigit():
                print(f"SUCCESS: kol_id is numeric: {row_dict['kol_id']}")
            else:
                print(f"WARNING: kol_id is not numeric: {row_dict['kol_id']}")
            
            # Check if kol_screen_name has @ prefix
            if row_dict['kol_screen_name'].startswith('@'):
                print("ERROR: kol_screen_name still has @ prefix!")
            else:
                print(f"SUCCESS: kol_screen_name is correct: {row_dict['kol_screen_name']}")
        
        # Check the url_tracking table
        cursor.execute("SELECT url, user_id FROM url_tracking WHERE user_id IS NOT NULL LIMIT 10")
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        print("\nurl_tracking table:")
        print(f"Columns: {columns}")
        print(f"Row count with user_id: {len(rows)}")
        
        for row in rows:
            row_dict = dict(zip(columns, row))
            print(f"Row: {row_dict}")
            
            # Check if user_id is numeric
            if row_dict['user_id'] and str(row_dict['user_id']).isdigit():
                print(f"SUCCESS: user_id is numeric: {row_dict['user_id']}")
            else:
                print(f"WARNING: user_id is not numeric: {row_dict['user_id']}")
        
        # Close the connection
        conn.close()
    except Exception as e:
        logging.error(f"Error checking database tables: {str(e)}")

def main():
    """Main function"""
    print("=== Testing kol_id fix ===")
    
    # Create a test Excel file
    excel_path = create_test_excel()
    if not excel_path:
        logging.error("Failed to create test Excel file")
        sys.exit(1)
    
    # Process the Excel file
    results = process_excel_file(excel_path)
    if not results:
        logging.error("Failed to process Excel file")
        sys.exit(1)
    
    # Check the database tables
    check_database_tables()

if __name__ == "__main__":
    main()
