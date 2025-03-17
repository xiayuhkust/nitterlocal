#!/usr/bin/env python3
"""
Script to demonstrate how the process_excel_with_profile.py script processes Excel data
and stores it in the SQLite database. This script:
1. Creates a test Excel file with both twitter.com and x.com URLs
2. Processes the Excel file using process_excel_with_profile.py
3. Displays the resulting database entries to verify URL normalization and data storage
"""

import os
import sys
import logging
import subprocess
import pandas as pd
import sqlite3
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_test_excel(output_path):
    """Create a test Excel file with both twitter.com and x.com URLs"""
    logging.info(f"Creating test Excel file at {output_path}")
    
    # Create test data with both twitter.com and x.com URLs
    data = {
        'URL': [
            'https://twitter.com/cz_binance',
            'https://x.com/VitalikButerin',
            'https://twitter.com/saylor'
        ],
        'KOL Screen Name': [
            'cz_binance',
            'vitalikbuterin',
            'saylor'
        ],
        'Bio': [
            'Founder of Binance, crypto exchange leader',
            'Co-founder of Ethereum, blockchain visionary',
            'Chairman of MicroStrategy, Bitcoin advocate'
        ],
        'Lore': [
            'Built Binance into the largest crypto exchange',
            'Created Ethereum, pioneered smart contracts',
            'Corporate Bitcoin adoption pioneer'
        ]
    }
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(data)
    df.to_excel(output_path, index=False)
    logging.info(f"Created test Excel file with {len(data['URL'])} rows")
    
    return output_path

def process_excel_file(excel_path):
    """Process the Excel file using process_excel_with_profile.py"""
    logging.info(f"Processing Excel file {excel_path}")
    
    # Run the process_excel_with_profile.py script
    cmd = f"python3 scripts/database/process_excel_with_profile.py --excel {excel_path}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        logging.error(f"Error processing Excel file: {result.stderr}")
        return False
    
    logging.info(f"Excel processing output: {result.stdout}")
    return True

def check_database_entries(db_path):
    """Check the database entries to verify URL normalization and data storage"""
    logging.info(f"Checking database entries in {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check URL tracking entries
    cursor.execute("SELECT url, screen_name, user_id FROM url_tracking ORDER BY id DESC LIMIT 10")
    url_tracking_entries = cursor.fetchall()
    
    logging.info("=== URL Tracking Entries ===")
    for entry in url_tracking_entries:
        url, screen_name, user_id = entry
        logging.info(f"URL: {url}, Screen Name: {screen_name}, User ID: {user_id}")
    
    # Check KOL character entries
    cursor.execute("SELECT kol_screen_name, bio, url_tracking_id FROM kol_character ORDER BY id DESC LIMIT 10")
    kol_character_entries = cursor.fetchall()
    
    logging.info("=== KOL Character Entries ===")
    for entry in kol_character_entries:
        kol_screen_name, bio, url_tracking_id = entry
        logging.info(f"KOL Screen Name: {kol_screen_name}, Bio: {bio}, URL Tracking ID: {url_tracking_id}")
    
    # Check for x.com URLs (should be none after normalization)
    cursor.execute("SELECT COUNT(*) FROM url_tracking WHERE url LIKE '%x.com%'")
    x_com_count = cursor.fetchone()[0]
    
    logging.info(f"Number of x.com URLs in database: {x_com_count}")
    
    # Check for twitter.com URLs
    cursor.execute("SELECT COUNT(*) FROM url_tracking WHERE url LIKE '%twitter.com%'")
    twitter_com_count = cursor.fetchone()[0]
    
    logging.info(f"Number of twitter.com URLs in database: {twitter_com_count}")
    
    conn.close()
    
    return x_com_count == 0  # Success if no x.com URLs are found

def main():
    """Main function"""
    # Define paths
    excel_path = f"/tmp/test_excel_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    db_path = "data/local_database.db"
    
    # Create test Excel file
    create_test_excel(excel_path)
    
    # Process Excel file
    if not process_excel_file(excel_path):
        logging.error("Failed to process Excel file")
        return 1
    
    # Check database entries
    if check_database_entries(db_path):
        logging.info("✅ Success: All URLs are normalized to twitter.com format")
    else:
        logging.error("❌ Error: Some URLs are still in x.com format")
    
    # Display command to view database entries
    logging.info("\nTo view the database entries, run:")
    logging.info("python3 scripts/database/view_database_records.py --table all")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
