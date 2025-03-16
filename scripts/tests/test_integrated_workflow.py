#!/usr/bin/env python3
"""
Test script to verify the integrated workflow from Excel processing to Twitter ID extraction.
"""

import os
import sys
import logging
import sqlite3
import pandas as pd
import subprocess
import tempfile
import json

# Add the project root to the Python path
sys.path.append('/home/ubuntu/nitterlocal')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_integrated_workflow(excel_path, db_path, target_url):
    """Test the integrated workflow from Excel processing to Twitter ID extraction"""
    logging.info(f"Testing integrated workflow for URL: {target_url}")
    
    try:
        # Step 1: Normalize URLs in the Excel file
        normalized_excel_path = excel_path.replace('.xlsx', '_normalized.xlsx')
        subprocess.run([
            'python3', '/home/ubuntu/nitterlocal/scripts/utils/normalize_excel_urls.py',
            '--input', excel_path,
            '--output', normalized_excel_path
        ], check=True)
        
        # Step 2: Process the Excel file using database_sync.py
        from app.database_sync import process_excel_and_sync
        
        results = process_excel_and_sync(
            excel_path=normalized_excel_path,
            db_path=db_path,
            sync_to_mysql=False,
            test_mode=True
        )
        
        logging.info(f"Excel processing results: {results['excel_processing']['success']}")
        
        # Step 3: Check if the target URL exists in url_tracking table
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM url_tracking WHERE url LIKE ?", (f"%{target_url}%",))
        url_record = cursor.fetchone()
        
        if url_record:
            logging.info("Target URL found in url_tracking table:")
            columns = [col[0] for col in cursor.description]
            url_data = dict(zip(columns, url_record))
            for key, value in url_data.items():
                logging.info(f"  {key}: {value}")
            
            # Step 4: Check if there's a corresponding record in kol_character table
            if 'id' in url_data:
                cursor.execute("SELECT * FROM kol_character WHERE url_tracking_id = ?", (url_data['id'],))
                kol_record = cursor.fetchone()
                
                if kol_record:
                    logging.info("Corresponding record found in kol_character table:")
                    columns = [col[0] for col in cursor.description]
                    kol_data = dict(zip(columns, kol_record))
                    for key, value in kol_data.items():
                        logging.info(f"  {key}: {value}")
                    
                    # Step 5: Verify the user_id matches the expected value
                    expected_user_id = "902926941413453824"
                    if url_data.get('user_id') == expected_user_id:
                        logging.info(f"SUCCESS: user_id matches expected value: {expected_user_id}")
                    else:
                        logging.warning(f"WARNING: user_id {url_data.get('user_id')} does not match expected value: {expected_user_id}")
                    
                    # Step 6: Verify the kol_id matches the user_id
                    if kol_data.get('kol_id') == url_data.get('user_id'):
                        logging.info(f"SUCCESS: kol_id matches user_id: {kol_data.get('kol_id')}")
                    else:
                        logging.warning(f"WARNING: kol_id {kol_data.get('kol_id')} does not match user_id {url_data.get('user_id')}")
                else:
                    logging.warning("No corresponding record found in kol_character table")
            else:
                logging.warning("No id found in url_tracking record")
        else:
            logging.warning(f"Target URL not found in url_tracking table: {target_url}")
        
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error testing integrated workflow: {str(e)}")
        return False

def main():
    """Main function"""
    # Path to the Excel file
    excel_path = "/home/ubuntu/attachments/d8edc8f7-51cf-497e-81b0-95f823431fd7/kol_character.xlsx"
    
    # Path to the SQLite database
    db_path = "/home/ubuntu/nitterlocal/data/local_database.db"
    
    # Target URL
    target_url = "cz_binance"
    
    # Test the integrated workflow
    test_integrated_workflow(excel_path, db_path, target_url)

if __name__ == "__main__":
    main()
