#!/usr/bin/env python3
"""
Test script to verify the full workflow of Excel processing, profile data extraction,
and synchronization to MySQL.
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

def create_test_excel():
    """Create a test Excel file with cz_binance data"""
    logging.info("Creating test Excel file")
    
    # Create a DataFrame with cz_binance data
    data = {
        'Twitter url': ['https://twitter.com/cz_binance'],
        'first category': ['KOL'],
        'second_category': ['-'],
        'bio': ['Founder of Binance, crypto exchange leader'],
        'lore': ['Born in China, started crypto in 2013, founded Binance in 2017'],
        'knowledge': ['Crypto Trading: Expert in exchange ops. Markets: Analyzes BTC trends. Regulation: Addresses policy'],
        'postExamples': ['"Bitcoin is controlled by math" 2025/2/20 "BNB adoption grows" 2025/1/15 "Crypto needs clarity" 2024/12/10 "Stay safe in trading" 2024/11/5'],
        'topics': ['Crypto Exchanges: Runs Binance. Market Trends: Tracks BTC. Regulation: Discusses rules'],
        'style_all': ['Bold: Confident market takes. Analytical: Ties to trends. Direct: Clear, no-nonsense tone'],
        'style_chat': ['Concise: Brief replies. Confident: Firm stance. Supportive: Helps community'],
        'style_post': ['Concise: Sharp posts. Bold: Strong statements. Informative: Shares updates'],
        'adjectives': ['Bold, Analytical, Direct']
    }
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(data)
    output_path = '/tmp/test_workflow.xlsx'
    df.to_excel(output_path, index=False)
    
    logging.info(f"Created test Excel file at {output_path}")
    return output_path

def process_excel(excel_path):
    """Process the Excel file"""
    logging.info(f"Processing Excel file: {excel_path}")
    
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
    try:
        process_result = subprocess.run([
            'python3', '/home/ubuntu/nitterlocal/scripts/database/process_excel.py',
            '--excel', excel_path,
            '--db-path', temp_db_path
        ], check=True, capture_output=True, text=True)
        
        logging.info("Excel processing completed successfully")
        logging.info(process_result.stdout)
        
        return temp_db_path
    except subprocess.CalledProcessError as e:
        logging.error(f"Error processing Excel file: {e}")
        logging.error(f"Output: {e.stdout}")
        logging.error(f"Error: {e.stderr}")
        return None

def update_profile_data(db_path):
    """Update profile data for URLs in the database"""
    logging.info(f"Updating profile data for URLs in database: {db_path}")
    
    try:
        # Run the profile update script
        update_result = subprocess.run([
            'python3', '/home/ubuntu/nitterlocal/scripts/profile/update_profile_data.py',
            '--db-path', db_path,
            '--limit', '1'  # Only process one URL for testing
        ], check=True, capture_output=True, text=True)
        
        logging.info("Profile update completed successfully")
        logging.info(update_result.stdout)
        
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error updating profile data: {e}")
        logging.error(f"Output: {e.stdout}")
        logging.error(f"Error: {e.stderr}")
        return False

def verify_profile_data(db_path):
    """Verify that profile data was extracted and stored correctly"""
    logging.info(f"Verifying profile data in database: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get data from url_tracking table
        cursor.execute("SELECT * FROM url_tracking WHERE url LIKE ?", ('%cz_binance%',))
        url_record = cursor.fetchone()
        
        if url_record:
            url_data = dict(url_record)
            
            print("\n=== Data for cz_binance in url_tracking table ===")
            
            # Display basic fields
            basic_fields = ['id', 'url', 'user_id', 'status', 'type', 'subtype', 'screen_name']
            for field in basic_fields:
                if field in url_data:
                    print(f"{field}: {url_data[field]}")
            
            # Display profile fields
            print("\n=== Profile Data in url_tracking table ===")
            profile_fields = [
                'followers_count', 'following_count', 'tweet_count',
                'profile_image_url', 'profile_banner_url', 'verified',
                'location', 'created_at', 'profile_updated_at'
            ]
            for field in profile_fields:
                if field in url_data and url_data[field] is not None:
                    print(f"{field}: {url_data[field]}")
            
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
                    
                    # Verify profile data is present
                    if url_data.get('followers_count', 0) > 0:
                        print(f"SUCCESS: followers_count is populated: {url_data.get('followers_count')}")
                    else:
                        print(f"WARNING: followers_count is not populated: {url_data.get('followers_count')}")
                    
                    return True
                else:
                    print("\nNo corresponding record found in kol_character table")
                    return False
            else:
                print("\nNo id found in url_tracking record")
                return False
        else:
            print(f"\nTarget URL not found in url_tracking table: cz_binance")
            return False
            
    except Exception as e:
        logging.error(f"Error verifying profile data: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function"""
    try:
        # Create a test Excel file
        excel_path = create_test_excel()
        
        # Process the Excel file
        db_path = process_excel(excel_path)
        if not db_path:
            logging.error("Failed to process Excel file")
            return False
        
        # Update profile data
        if not update_profile_data(db_path):
            logging.error("Failed to update profile data")
            return False
        
        # Verify profile data
        if not verify_profile_data(db_path):
            logging.error("Failed to verify profile data")
            return False
        
        logging.info("Full workflow test completed successfully")
        
        # Clean up
        if os.path.exists(excel_path):
            os.remove(excel_path)
        if os.path.exists(db_path):
            os.remove(db_path)
        
        return True
    except Exception as e:
        logging.error(f"Error in full workflow test: {str(e)}")
        return False

if __name__ == "__main__":
    main()
