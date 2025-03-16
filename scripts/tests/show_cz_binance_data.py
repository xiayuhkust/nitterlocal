#!/usr/bin/env python3
"""
Script to show the data for cz_binance in url_tracking and kol_character tables.
"""

import os
import sys
import logging
import sqlite3
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.append('/home/ubuntu/nitterlocal')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_cz_binance_data(db_path):
    """Get the data for cz_binance from url_tracking and kol_character tables"""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get data from url_tracking table
        cursor.execute("SELECT * FROM url_tracking WHERE screen_name = ? OR url LIKE ?", 
                      ('cz_binance', '%cz_binance%'))
        url_record = cursor.fetchone()
        
        if not url_record:
            logging.warning("No record found for cz_binance in url_tracking table")
            return None, None
        
        # Convert to dict
        url_data = dict(url_record)
        
        # Get data from kol_character table
        if 'id' in url_data:
            cursor.execute("SELECT * FROM kol_character WHERE url_tracking_id = ?", (url_data['id'],))
            kol_record = cursor.fetchone()
            
            if kol_record:
                # Convert to dict
                kol_data = dict(kol_record)
            else:
                logging.warning(f"No record found in kol_character table with url_tracking_id = {url_data['id']}")
                kol_data = None
        else:
            logging.warning("No id found in url_tracking record")
            kol_data = None
        
        conn.close()
        return url_data, kol_data
    
    except Exception as e:
        logging.error(f"Error getting cz_binance data: {str(e)}")
        return None, None

def main():
    """Main function"""
    # Path to the SQLite database
    db_path = "/home/ubuntu/nitterlocal/data/local_database.db"
    
    # Get the data for cz_binance
    url_data, kol_data = get_cz_binance_data(db_path)
    
    if url_data:
        print("\n=== Data for cz_binance in url_tracking table ===")
        for key, value in url_data.items():
            print(f"{key}: {value}")
    
    if kol_data:
        print("\n=== Data for cz_binance in kol_character table ===")
        for key, value in kol_data.items():
            print(f"{key}: {value}")
    
    # Also output as JSON for easier parsing
    result = {
        "url_tracking": url_data,
        "kol_character": kol_data
    }
    
    print("\n=== JSON Output ===")
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
