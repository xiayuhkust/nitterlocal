#!/usr/bin/env python3
"""
Script to process the Excel file and show the results for cz_binance.
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

def process_excel_and_show_results(excel_path, target_url):
    """Process the Excel file and show the results for the target URL"""
    logging.info(f"Processing Excel file: {excel_path}")
    logging.info(f"Target URL: {target_url}")
    
    try:
        # Create a temporary database for testing
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        logging.info(f"Created temporary database: {temp_db_path}")
        
        # Create tables in the temporary database
        subprocess.run([
            'python3', '/home/ubuntu/nitterlocal/scripts/database/create_tables.py',
            '--db-path', temp_db_path
        ], check=True)
        
        # Normalize URLs in the Excel file
        normalized_excel_path = excel_path.replace('.xlsx', '_normalized.xlsx')
        subprocess.run([
            'python3', '/home/ubuntu/nitterlocal/scripts/utils/normalize_excel_urls.py',
            '--input', excel_path,
            '--output', normalized_excel_path
        ], check=True)
        
        # Process the Excel file
        process_result = subprocess.run([
            'python3', '/home/ubuntu/nitterlocal/scripts/database/process_excel.py',
            '--excel', normalized_excel_path,
            '--db-path', temp_db_path,
            '--verbose'
        ], check=True, capture_output=True, text=True)
        
        # Print the process output
        print("\n=== Excel Processing Output ===")
        print(process_result.stdout)
        
        # Connect to the temporary database
        conn = sqlite3.connect(temp_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get data from url_tracking table
        cursor.execute("SELECT * FROM url_tracking WHERE screen_name = ? OR url LIKE ?", 
                      ('cz_binance', '%cz_binance%'))
        url_record = cursor.fetchone()
        
        if url_record:
            print("\n=== Data for cz_binance in url_tracking table ===")
            url_data = dict(url_record)
            for key, value in url_data.items():
                print(f"{key}: {value}")
            
            # Get data from kol_character table
            if 'id' in url_data:
                cursor.execute("SELECT * FROM kol_character WHERE url_tracking_id = ?", (url_data['id'],))
                kol_record = cursor.fetchone()
                
                if kol_record:
                    print("\n=== Data for cz_binance in kol_character table ===")
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
            print(f"\nTarget URL not found in url_tracking table: {target_url}")
        
        conn.close()
        
        # Clean up temporary files
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
        if os.path.exists(normalized_excel_path):
            os.remove(normalized_excel_path)
        
        return True
    except Exception as e:
        logging.error(f"Error processing Excel and showing results: {str(e)}")
        return False

def main():
    """Main function"""
    # Path to the Excel file
    excel_path = "/home/ubuntu/attachments/d8edc8f7-51cf-497e-81b0-95f823431fd7/kol_character.xlsx"
    
    # Target URL
    target_url = "cz_binance"
    
    # Process the Excel file and show the results
    process_excel_and_show_results(excel_path, target_url)

if __name__ == "__main__":
    main()
