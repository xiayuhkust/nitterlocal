#!/usr/bin/env python3
"""
Direct verification script for the integrated Excel processing workflow.
This script creates a test Excel file, processes it, and directly queries the database
to verify the results.
"""

import os
import sys
import logging
import pandas as pd
import sqlite3
import tempfile
import subprocess
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

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
    output_path = '/tmp/test_integrated_workflow.xlsx'
    df.to_excel(output_path, index=False)
    
    logging.info(f"Created test Excel file at {output_path}")
    return output_path

def display_database_results(db_path, handle):
    """Display the results from the database for a specific handle"""
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
            
            print(f"\n=== Data for {handle} in url_tracking table ===")
            
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
                'location', 'description', 'created_at', 'profile_updated_at'
            ]
            for field in profile_fields:
                if field in url_data and url_data[field] is not None:
                    print(f"{field}: {url_data[field]}")
            
            # Get data from kol_character table
            if 'id' in url_data:
                cursor.execute("SELECT * FROM kol_character WHERE url_tracking_id = ?", (url_data['id'],))
                kol_record = cursor.fetchone()
                
                if kol_record:
                    print(f"\n=== Data for {handle} in kol_character table ===")
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
                else:
                    print("\nNo corresponding record found in kol_character table")
        else:
            print(f"\nTarget handle not found in url_tracking table: {handle}")
            
    except Exception as e:
        logging.error(f"Error displaying results: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

def verify_integrated_workflow():
    """Verify the integrated Excel processing workflow"""
    try:
        # Create a test Excel file
        excel_path = create_test_excel()
        
        # Create a temporary database for testing
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        logging.info(f"Created temporary database at {db_path}")
        
        # Create tables in the temporary database
        conn = sqlite3.connect(db_path)
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
        
        # Process the Excel file using the integrated script
        logging.info("Processing Excel file using integrated script")
        process_result = subprocess.run([
            'python3', '/home/ubuntu/nitterlocal/scripts/database/process_excel_with_profile.py',
            '--excel', excel_path,
            '--db-path', db_path
        ], check=True, capture_output=True, text=True)
        
        # Print the process output
        print("\n--- Process Output ---")
        print(process_result.stdout)
        
        # Display the results directly from the database
        print("\n--- Database Query Results ---")
        display_database_results(db_path, 'cz_binance')
        
        # Clean up
        if os.path.exists(excel_path):
            os.remove(excel_path)
        if os.path.exists(db_path):
            os.remove(db_path)
        
        logging.info("Verification completed successfully")
        return True
    except Exception as e:
        logging.error(f"Error in verification: {str(e)}")
        return False

if __name__ == "__main__":
    verify_integrated_workflow()
