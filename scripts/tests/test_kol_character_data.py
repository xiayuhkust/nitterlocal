#!/usr/bin/env python3
"""
Test script to verify the kol_character data from Excel processing.
"""

import os
import sys
import logging
import sqlite3
import pandas as pd
import subprocess

# Add the project root to the Python path
sys.path.append('/home/ubuntu/nitterlocal')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_kol_character_data(excel_path, db_path, target_url):
    """Test the kol_character data from Excel processing"""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Step 1: Process the Excel file
        from scripts.database.process_excel import process_excel_file
        
        # Normalize the Excel file first
        normalized_excel_path = excel_path.replace('.xlsx', '_normalized.xlsx')
        subprocess.run([
            'python3', '/home/ubuntu/nitterlocal/scripts/utils/normalize_excel_urls.py',
            '--input', excel_path,
            '--output', normalized_excel_path
        ], check=True)
        
        # Process the normalized Excel file
        process_excel_file(normalized_excel_path, db_path)
        
        # Step 2: Check if the target URL exists in url_tracking table
        cursor.execute("SELECT * FROM url_tracking WHERE url LIKE ?", (f"%{target_url}%",))
        url_record = cursor.fetchone()
        
        if url_record:
            logging.info("Target URL found in url_tracking table:")
            columns = [col[0] for col in cursor.description]
            url_data = dict(zip(columns, url_record))
            for key, value in url_data.items():
                logging.info(f"  {key}: {value}")
            
            # Step 3: Check if there's a corresponding record in kol_character table
            if 'id' in url_data:
                cursor.execute("SELECT * FROM kol_character WHERE url_tracking_id = ?", (url_data['id'],))
                kol_record = cursor.fetchone()
                
                if kol_record:
                    logging.info("Corresponding record found in kol_character table:")
                    columns = [col[0] for col in cursor.description]
                    kol_data = dict(zip(columns, kol_record))
                    for key, value in kol_data.items():
                        logging.info(f"  {key}: {value}")
                else:
                    # Try to find by screen_name
                    if 'screen_name' in url_data:
                        cursor.execute("SELECT * FROM kol_character WHERE kol_screen_name = ?", (url_data['screen_name'],))
                        kol_record = cursor.fetchone()
                        
                        if kol_record:
                            logging.info("Corresponding record found in kol_character table by screen_name:")
                            columns = [col[0] for col in cursor.description]
                            kol_data = dict(zip(columns, kol_record))
                            for key, value in kol_data.items():
                                logging.info(f"  {key}: {value}")
                        else:
                            logging.warning("No corresponding record found in kol_character table by screen_name")
                    else:
                        logging.warning("No screen_name found in url_tracking record")
            else:
                logging.warning("No id found in url_tracking record")
        else:
            logging.warning(f"Target URL not found in url_tracking table: {target_url}")
        
        # Step 4: Show all kol_character records
        cursor.execute("SELECT COUNT(*) FROM kol_character")
        kol_count = cursor.fetchone()[0]
        logging.info(f"Total kol_character records: {kol_count}")
        
        if kol_count > 0:
            cursor.execute("SELECT * FROM kol_character LIMIT 5")
            kol_records = cursor.fetchall()
            
            logging.info("Sample kol_character records:")
            columns = [col[0] for col in cursor.description]
            
            for record in kol_records:
                kol_data = dict(zip(columns, record))
                logging.info(f"Record ID: {kol_data.get('id')}")
                for key, value in kol_data.items():
                    if key != 'id':
                        logging.info(f"  {key}: {value}")
                logging.info("---")
        
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error testing kol_character data: {str(e)}")
        return False

if __name__ == "__main__":
    # Path to the Excel file
    excel_path = "/home/ubuntu/attachments/d8edc8f7-51cf-497e-81b0-95f823431fd7/kol_character.xlsx"
    
    # Path to the SQLite database
    db_path = "/home/ubuntu/nitterlocal/data/local_database.db"
    
    # Target URL
    target_url = "cz_binance"
    
    # Test the kol_character data
    test_kol_character_data(excel_path, db_path, target_url)
