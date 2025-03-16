#!/usr/bin/env python3
"""
Test script to verify the Excel processing workflow with cz_binance example.
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

def create_test_excel(output_path):
    """Create a test Excel file with cz_binance data"""
    logging.info(f"Creating test Excel file at {output_path}")
    
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
    
    df = pd.DataFrame(data)
    df.to_excel(output_path, index=False)
    
    logging.info(f"Created test Excel file with cz_binance data")
    return output_path

def create_tables(db_path):
    """Create the necessary tables in the database"""
    logging.info(f"Creating tables in database: {db_path}")
    
    try:
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
        
        logging.info("Tables created successfully")
        return True
    except Exception as e:
        logging.error(f"Error creating tables: {str(e)}")
        return False

def test_excel_processing(excel_path):
    """Test the Excel processing workflow with cz_binance example"""
    logging.info(f"Testing Excel processing workflow with {excel_path}")
    
    try:
        # Create a temporary database for testing
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        logging.info(f"Created temporary database: {temp_db_path}")
        
        # Create tables in the temporary database
        create_tables(temp_db_path)
        
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
        
        # Get data from url_tracking table
        cursor.execute("SELECT * FROM url_tracking WHERE url LIKE ?", ('%cz_binance%',))
        url_record = cursor.fetchone()
        
        if url_record:
            print("\n=== Data for cz_binance in url_tracking table ===")
            url_data = dict(url_record)
            
            # Display basic fields first
            basic_fields = ['id', 'url', 'user_id', 'description', 'status', 'type', 'subtype', 'screen_name']
            for field in basic_fields:
                if field in url_data:
                    print(f"{field}: {url_data[field]}")
            
            # Display profile-related fields
            print("\n=== Profile Data in url_tracking table ===")
            profile_fields = ['followers_count', 'following_count', 'tweet_count', 
                             'profile_image_url', 'profile_banner_url', 'verified', 
                             'location', 'created_at', 'profile_updated_at']
            for field in profile_fields:
                if field in url_data and url_data[field]:
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
                else:
                    print("\nNo corresponding record found in kol_character table")
            else:
                print("\nNo id found in url_tracking record")
        else:
            print(f"\nTarget URL not found in url_tracking table: cz_binance")
        
        conn.close()
        
        # Clean up temporary files
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
        
        return True
    except Exception as e:
        logging.error(f"Error testing Excel processing: {str(e)}")
        return False

def main():
    """Main function"""
    # Create a test Excel file
    excel_path = "/tmp/cz_binance_test.xlsx"
    create_test_excel(excel_path)
    
    # Test the Excel processing workflow
    test_excel_processing(excel_path)
    
    # Clean up
    if os.path.exists(excel_path):
        os.remove(excel_path)

if __name__ == "__main__":
    main()
