#!/usr/bin/env python3
"""
Script to test the database synchronization functionality.
"""

import os
import sys
import logging
import pandas as pd
from app.database_sync import process_excel_and_sync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
            ]
        })
        
        excel_path = '/tmp/test_files/test_twitter_urls.xlsx'
        df.to_excel(excel_path, index=False)
        
        logging.info(f"Created test Excel file at {excel_path}")
        return excel_path
    except Exception as e:
        logging.error(f"Error creating test Excel file: {str(e)}")
        return None

def main():
    """Main function"""
    # Create a test Excel file
    excel_path = create_test_excel()
    if not excel_path:
        logging.error("Failed to create test Excel file")
        sys.exit(1)
    
    # Process the Excel file and synchronize with MySQL
    logging.info("Processing Excel file and synchronizing with MySQL...")
    results = process_excel_and_sync(
        excel_path=excel_path,
        sync_to_mysql=True,
        test_mode=False  # Set to False to actually update MySQL
    )
    
    # Print the results
    logging.info("Excel processing results:")
    if results["excel_processing"]:
        logging.info(f"Success: {results['excel_processing']['success']}")
        logging.info(f"Processed count: {results['excel_processing']['processed_count']}")
        if results["excel_processing"]["errors"]:
            logging.error(f"Errors: {results['excel_processing']['errors']}")
    
    logging.info("SQLite kol_character table stats:")
    if results["sqlite_kol_character_stats"]:
        logging.info(f"Table exists: {results['sqlite_kol_character_stats']['exists']}")
        logging.info(f"Record count: {results['sqlite_kol_character_stats']['count']}")
    
    logging.info("SQLite url_tracking table stats:")
    if results["sqlite_url_tracking_stats"]:
        logging.info(f"Table exists: {results['sqlite_url_tracking_stats']['exists']}")
        logging.info(f"Record count: {results['sqlite_url_tracking_stats']['count']}")
    
    logging.info("MySQL synchronization results:")
    if results["kol_character_sync"]:
        logging.info(f"Success: {results['kol_character_sync']['success']}")
        logging.info(f"Processed count: {results['kol_character_sync']['processed_count']}")
        if results["kol_character_sync"]["errors"]:
            logging.error(f"Errors: {results['kol_character_sync']['errors']}")

if __name__ == "__main__":
    main()
