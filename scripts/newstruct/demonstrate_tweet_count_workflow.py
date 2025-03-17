#!/usr/bin/env python3
"""
Script to demonstrate the complete Excel processing workflow with focus on tweet_count.
This script shows how tweet_count is retrieved from Twitter and stored in the database.
"""

import os
import sys
import logging
import sqlite3
import pandas as pd
import tempfile
import subprocess
import json
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_test_excel():
    """Create a test Excel file with Twitter profile data"""
    logging.info("Creating test Excel file")
    
    # Create a DataFrame with cz_binance data
    data = {
        'Twitter url': ['https://twitter.com/cz_binance'],
        'first category': ['KOL'],
        'second_category': ['-'],
        'bio': ['Founder of Binance, crypto exchange leader'],
        'lore': ['Born in China, started crypto in 2013, founded Binance in 2017']
    }
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(data)
    
    # Create a temporary file for the Excel
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
        excel_path = temp_file.name
    
    df.to_excel(excel_path, index=False)
    
    logging.info(f"Created test Excel file at {excel_path}")
    return excel_path

def check_database_before_update(db_path, handle):
    """Check the database before updating"""
    logging.info(f"Checking database before update for handle: {handle}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get data from url_tracking table
        cursor.execute("SELECT * FROM url_tracking WHERE screen_name = ?", (handle,))
        url_record = cursor.fetchone()
        
        if url_record:
            url_data = dict(url_record)
            
            print(f"\n=== Database State BEFORE Update for {handle} ===")
            
            # Display profile fields
            profile_fields = [
                'tweet_count', 'followers_count', 'following_count',
                'profile_image_url', 'profile_banner_url', 'verified',
                'location', 'description', 'created_at', 'profile_updated_at'
            ]
            for field in profile_fields:
                if field in url_data and url_data[field] is not None:
                    print(f"{field}: {url_data[field]}")
        else:
            print(f"\nNo record found for handle: {handle} before update")
            
    except Exception as e:
        logging.error(f"Error checking database before update: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

def process_excel_file(excel_path, db_path):
    """Process an Excel file with KOL character data"""
    logging.info(f"Processing Excel file: {excel_path}")
    
    try:
        # Import the process_excel_with_profile function
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
        from process_excel_with_profile import process_excel_file as process_excel
        
        # Process the Excel file
        process_excel(excel_path, db_path)
        
        logging.info(f"Processed Excel file: {excel_path}")
        return True
    except Exception as e:
        logging.error(f"Error processing Excel file: {str(e)}")
        return False

def check_database_after_update(db_path, handle):
    """Check the database after updating"""
    logging.info(f"Checking database after update for handle: {handle}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get data from url_tracking table
        cursor.execute("SELECT * FROM url_tracking WHERE screen_name = ?", (handle,))
        url_record = cursor.fetchone()
        
        if url_record:
            url_data = dict(url_record)
            
            print(f"\n=== Database State AFTER Update for {handle} ===")
            
            # Display profile fields
            profile_fields = [
                'tweet_count', 'followers_count', 'following_count',
                'profile_image_url', 'profile_banner_url', 'verified',
                'location', 'description', 'created_at', 'profile_updated_at'
            ]
            for field in profile_fields:
                if field in url_data and url_data[field] is not None:
                    print(f"{field}: {url_data[field]}")
                    
            # Check if tweet_count is populated
            if 'tweet_count' in url_data and url_data['tweet_count'] > 0:
                print(f"\nSUCCESS: tweet_count is correctly stored in the database: {url_data['tweet_count']}")
            else:
                print(f"\nWARNING: tweet_count is not populated or is zero")
        else:
            print(f"\nNo record found for handle: {handle} after update")
            
    except Exception as e:
        logging.error(f"Error checking database after update: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function"""
    # Set the database path
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/local_database.db'))
    
    # Set the handle to check
    handle = 'cz_binance'
    
    # Check the database before update
    check_database_before_update(db_path, handle)
    
    # Create a test Excel file
    excel_path = create_test_excel()
    
    # Process the Excel file
    process_excel_file(excel_path, db_path)
    
    # Check the database after Excel processing
    check_database_after_update(db_path, handle)
    
    # Clean up
    if os.path.exists(excel_path):
        os.remove(excel_path)

if __name__ == "__main__":
    main()
