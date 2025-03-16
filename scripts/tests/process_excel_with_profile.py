#!/usr/bin/env python3
"""
Script to process Excel data using both scraper and profile methods,
outputting updated url_tracking and kol_character tables.
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
    output_path = '/tmp/test_workflow_profile.xlsx'
    df.to_excel(output_path, index=False)
    
    logging.info(f"Created test Excel file at {output_path}")
    return output_path

def create_test_database():
    """Create a test database with necessary tables"""
    logging.info("Creating test database")
    
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
    
    return temp_db_path

def process_excel(excel_path, db_path):
    """Process the Excel file and store data in the database"""
    logging.info(f"Processing Excel file: {excel_path}")
    
    try:
        # Process the Excel file
        process_result = subprocess.run([
            'python3', '/home/ubuntu/nitterlocal/scripts/database/process_excel.py',
            '--excel', excel_path,
            '--db-path', db_path
        ], check=True, capture_output=True, text=True)
        
        logging.info("Excel processing completed successfully")
        logging.info(process_result.stdout)
        
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error processing Excel file: {e}")
        logging.error(f"Output: {e.stdout}")
        logging.error(f"Error: {e.stderr}")
        return False

def extract_profile_data(handle, db_path):
    """Extract profile data for a Twitter handle and update the database"""
    logging.info(f"Extracting profile data for handle: {handle}")
    
    # Set the client directory
    client_dir = os.path.join('/home/ubuntu/nitterlocal', 'src/twitter_client')
    
    # Create a temporary file for the output
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
        output_file = temp_file.name
    
    try:
        # Check if the profile client exists
        profile_client_path = os.path.join(client_dir, 'twitter_profile_client.js')
        if not os.path.exists(profile_client_path):
            logging.error(f"Profile client {profile_client_path} does not exist")
            return False
        
        # Run the Twitter profile client
        logging.info(f"Running Twitter profile client for {handle}...")
        process = subprocess.run(
            ['node', profile_client_path, handle, output_file],
            cwd=client_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Check if the output file exists
        if not os.path.exists(output_file):
            logging.error(f"Output file {output_file} does not exist")
            return False
        
        # Load the result from the output file
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        # Extract profile data
        profile = result.get('profile', {})
        
        profile_data = {
            'user_id': result.get('userId'),
            'screen_name': handle,
            'followers_count': profile.get('followersCount', 0),
            'following_count': profile.get('followingCount', 0) or profile.get('friendsCount', 0),
            'tweet_count': profile.get('tweetsCount', 0) or profile.get('statusesCount', 0),
            'profile_image_url': profile.get('avatar', ''),
            'profile_banner_url': profile.get('banner', ''),
            'verified': 1 if profile.get('verified', False) or profile.get('isVerified', False) or profile.get('isBlueVerified', False) else 0,
            'location': profile.get('location', ''),
            'description': profile.get('biography', ''),
            'created_at': profile.get('joined', ''),
            'profile_updated_at': datetime.now().isoformat()
        }
        
        # Update the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the URL from the screen_name
        url = f"https://twitter.com/{handle}"
        
        # Check if the URL exists in the database
        cursor.execute("SELECT id FROM url_tracking WHERE url = ?", (url,))
        url_record = cursor.fetchone()
        
        if url_record:
            # Update existing record
            url_id = url_record[0]
            logging.info(f"Updating profile data for URL ID {url_id}: {url}")
            
            # Update the profile data
            update_fields = []
            update_values = []
            
            for key, value in profile_data.items():
                if key != 'url':  # Skip the URL field
                    update_fields.append(f"{key} = ?")
                    update_values.append(value)
            
            update_values.append(url)  # For the WHERE clause
            
            update_query = f'''
            UPDATE url_tracking 
            SET {', '.join(update_fields)}
            WHERE url = ?
            '''
            
            cursor.execute(update_query, update_values)
            
            # Update the kol_character table with the user_id
            cursor.execute('''
            UPDATE kol_character
            SET kol_id = ?
            WHERE url_tracking_id = ?
            ''', (profile_data['user_id'], url_id))
            
        else:
            logging.error(f"URL not found in database: {url}")
            conn.close()
            return False
        
        conn.commit()
        conn.close()
        
        logging.info(f"Updated profile data for {handle}")
        return True
            
    except Exception as e:
        logging.error(f"Error extracting profile data for handle {handle}: {str(e)}")
        return False
    finally:
        # Remove the temporary file
        if os.path.exists(output_file):
            os.remove(output_file)

def display_database_data(db_path, handle):
    """Display data from the database for a specific handle"""
    logging.info(f"Displaying database data for handle: {handle}")
    
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
                    
                    # Output as JSON for easier parsing
                    print("\n=== JSON Output ===")
                    print(json.dumps({
                        "url_tracking": url_data,
                        "kol_character": kol_data
                    }, indent=2, default=str))
                    
                    return True
                else:
                    print("\nNo corresponding record found in kol_character table")
                    return False
            else:
                print("\nNo id found in url_tracking record")
                return False
        else:
            print(f"\nTarget handle not found in url_tracking table: {handle}")
            return False
            
    except Exception as e:
        logging.error(f"Error displaying database data: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function"""
    try:
        # Create a test Excel file
        excel_path = create_test_excel()
        
        # Create a test database
        db_path = create_test_database()
        
        # Process the Excel file
        if not process_excel(excel_path, db_path):
            logging.error("Failed to process Excel file")
            return False
        
        # Extract profile data for cz_binance
        if not extract_profile_data("cz_binance", db_path):
            logging.error("Failed to extract profile data")
            return False
        
        # Display database data for cz_binance
        if not display_database_data(db_path, "cz_binance"):
            logging.error("Failed to display database data")
            return False
        
        logging.info("Process completed successfully")
        
        # Clean up
        if os.path.exists(excel_path):
            os.remove(excel_path)
        if os.path.exists(db_path):
            os.remove(db_path)
        
        return True
    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")
        return False

if __name__ == "__main__":
    main()
