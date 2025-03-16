#!/usr/bin/env python3
"""
Script to process only the first row of the Excel file (cz_binance) and show the results.
"""

import os
import sys
import logging
import sqlite3
import pandas as pd
import subprocess
import tempfile
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.append('/home/ubuntu/nitterlocal')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_test_excel_with_first_row(input_excel_path, output_excel_path):
    """Create a test Excel file with only the first row from the input Excel"""
    logging.info(f"Creating test Excel with first row from {input_excel_path}")
    
    try:
        # Read the Excel file
        df = pd.read_excel(input_excel_path)
        
        # Keep only the first row
        first_row_df = df.iloc[0:1]
        
        # Save to a new Excel file
        first_row_df.to_excel(output_excel_path, index=False)
        
        logging.info(f"Created test Excel with first row at {output_excel_path}")
        return True
    except Exception as e:
        logging.error(f"Error creating test Excel with first row: {str(e)}")
        return False

def process_excel_first_row(excel_path):
    """Process only the first row of the Excel file and show the results"""
    logging.info(f"Processing first row of Excel file: {excel_path}")
    
    try:
        # Create a temporary database for testing
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        logging.info(f"Created temporary database: {temp_db_path}")
        
        # Create tables in the temporary database
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Create url_tracking table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS url_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            user_id TEXT,
            description TEXT,
            status TEXT DEFAULT 'active',
            last_checked TEXT,
            error_count INTEGER DEFAULT 0,
            tweet_count INTEGER DEFAULT 0,
            type TEXT,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_scraped TEXT,
            last_error TEXT,
            subtype TEXT,
            screen_name TEXT,
            followers_count INTEGER,
            following_count INTEGER,
            profile_image_url TEXT,
            profile_banner_url TEXT,
            verified INTEGER,
            location TEXT,
            created_at TEXT,
            profile_updated_at TEXT
        )
        ''')
        
        # Create kol_character table
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
            url_tracking_id INTEGER,
            UNIQUE(kol_screen_name)
        )
        ''')
        
        conn.commit()
        conn.close()
        
        # Process the Excel file
        process_result = subprocess.run([
            'python3', '/home/ubuntu/nitterlocal/scripts/database/process_excel.py',
            '--excel', excel_path,
            '--db-path', temp_db_path
        ], check=True, capture_output=True, text=True)
        
        # Print the process output
        print("\n=== Excel Processing Output ===")
        print(process_result.stdout)
        
        # Connect to the temporary database
        conn = sqlite3.connect(temp_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all data from url_tracking table
        cursor.execute("SELECT * FROM url_tracking")
        url_records = cursor.fetchall()
        
        if url_records:
            print(f"\n=== Found {len(url_records)} records in url_tracking table ===")
            
            # Get the first record (should be cz_binance)
            url_data = dict(url_records[0])
            
            print("\n=== Data in url_tracking table ===")
            for key, value in url_data.items():
                print(f"{key}: {value}")
            
            # Get data from kol_character table
            if 'id' in url_data:
                cursor.execute("SELECT * FROM kol_character WHERE url_tracking_id = ?", (url_data['id'],))
                kol_record = cursor.fetchone()
                
                if kol_record:
                    print("\n=== Data in kol_character table ===")
                    kol_data = dict(kol_record)
                    for key, value in kol_data.items():
                        print(f"{key}: {value}")
                    
                    # Verify the user_id matches the expected value
                    expected_user_id = "902926941413453824"
                    if url_data.get('user_id') == expected_user_id:
                        print(f"\nSUCCESS: user_id matches expected value: {expected_user_id}")
                    else:
                        print(f"\nWARNING: user_id {url_data.get('user_id')} does not match expected value: {expected_user_id}")
                    
                    # Verify the kol_id matches the user_id
                    if kol_data.get('kol_id') == url_data.get('user_id'):
                        print(f"SUCCESS: kol_id matches user_id: {kol_data.get('kol_id')}")
                    else:
                        print(f"WARNING: kol_id {kol_data.get('kol_id')} does not match user_id {url_data.get('user_id')}")
                else:
                    print("\nNo corresponding record found in kol_character table")
            else:
                print("\nNo id found in url_tracking record")
        else:
            print(f"\nNo records found in url_tracking table")
        
        # Also output as JSON for easier parsing
        result = {
            "url_tracking": url_data if 'url_data' in locals() else None,
            "kol_character": kol_data if 'kol_data' in locals() else None
        }
        
        print("\n=== JSON Output ===")
        print(json.dumps(result, indent=2, default=str))
        
        conn.close()
        
        # Clean up temporary files
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
        
        return True
    except Exception as e:
        logging.error(f"Error processing Excel first row: {str(e)}")
        return False

def main():
    """Main function"""
    # Path to the Excel file
    original_excel_path = "/home/ubuntu/attachments/d8edc8f7-51cf-497e-81b0-95f823431fd7/kol_character.xlsx"
    
    # Create a test Excel file with only the first row
    first_row_excel_path = "/tmp/cz_binance_first_row.xlsx"
    create_test_excel_with_first_row(original_excel_path, first_row_excel_path)
    
    # Process the first row Excel file
    process_excel_first_row(first_row_excel_path)
    
    # Clean up
    if os.path.exists(first_row_excel_path):
        os.remove(first_row_excel_path)

if __name__ == "__main__":
    main()
