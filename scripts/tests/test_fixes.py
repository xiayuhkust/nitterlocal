#!/usr/bin/env python3
"""
Script to test the fixes for kol_id and screen_name formatting.
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

def create_test_excel():
    """Create a test Excel file with Twitter URLs"""
    try:
        # Create a test Excel file
        df = pd.DataFrame({
            'Twitter url': [
                'https://twitter.com/elonmusk',
                'https://twitter.com/vitalikbuterin',
                'https://twitter.com/cz_binance'
            ]
        })
        
        excel_path = '/tmp/test_twitter_urls.xlsx'
        df.to_excel(excel_path, index=False)
        
        logging.info(f"Created test Excel file at {excel_path}")
        return excel_path
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
            sync_to_mysql=True,
            test_mode=False
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
            
            # Check if kol_id is set correctly
            if row_dict['kol_id'] == 'KOL' or row_dict['kol_id'] is None:
                print("ERROR: kol_id is not set correctly!")
            
            # Check if kol_screen_name has @ prefix
            if row_dict['kol_screen_name'].startswith('@'):
                print("ERROR: kol_screen_name still has @ prefix!")
        
        # Close the connection
        conn.close()
    except Exception as e:
        logging.error(f"Error checking database tables: {str(e)}")

def main():
    """Main function"""
    print("=== Testing kol_id and screen_name fixes ===")
    
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
