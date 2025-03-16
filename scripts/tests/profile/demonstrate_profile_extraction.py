#!/usr/bin/env python3
"""
Script to demonstrate how profile data is extracted from Twitter URLs and stored in url_tracking table.
"""

import os
import sys
import logging
import sqlite3
import json
import tempfile
import subprocess
from datetime import datetime

# Add the project root to the Python path
sys.path.append('/home/ubuntu/nitterlocal')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def extract_profile_data(handle):
    """Extract profile data for a Twitter handle using the Twitter client"""
    logging.info(f"Extracting profile data for handle: {handle}")
    
    # Set the client directory
    client_dir = os.path.join('/home/ubuntu/nitterlocal', 'src/twitter_client')
    
    # Check if the Twitter client exists
    client_path = os.path.join(client_dir, 'twitter_client.js')
    if not os.path.exists(client_path):
        logging.error(f"Twitter client {client_path} does not exist")
        return None
    
    # Create a temporary file for the output
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
        output_file = temp_file.name
    
    try:
        # Run the Twitter client to get profile data
        logging.info(f"Running Twitter client to get profile data for {handle}...")
        process = subprocess.run(
            ['node', client_path, handle, '1', '0', output_file],
            cwd=client_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Check if the output file exists
        if not os.path.exists(output_file):
            logging.error(f"Output file {output_file} does not exist")
            return None
        
        # Load the result from the output file
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        # Extract profile data
        profile_data = {
            'user_id': result.get('userId'),
            'screen_name': handle,
            'followers_count': result.get('followersCount', 0),
            'following_count': result.get('followingCount', 0),
            'tweet_count': result.get('statusesCount', 0),
            'profile_image_url': result.get('profileImageUrl', ''),
            'profile_banner_url': result.get('profileBannerUrl', ''),
            'verified': 1 if result.get('verified', False) else 0,
            'location': result.get('location', ''),
            'description': result.get('description', ''),
            'created_at': result.get('createdAt', ''),
            'profile_updated_at': datetime.now().isoformat()
        }
        
        logging.info(f"Extracted profile data for {handle}: {profile_data}")
        return profile_data
            
    except Exception as e:
        logging.error(f"Error extracting profile data for handle {handle}: {str(e)}")
        return None
    finally:
        # Remove the temporary file
        if os.path.exists(output_file):
            os.remove(output_file)

def store_profile_data(db_path, url, profile_data):
    """Store profile data in the url_tracking table"""
    if not profile_data:
        logging.warning(f"No profile data to store for URL: {url}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
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
            
        else:
            # Insert new record
            logging.info(f"Inserting new record for URL: {url}")
            
            # Prepare fields and values for insertion
            fields = ['url']
            values = [url]
            
            for key, value in profile_data.items():
                if key != 'url':  # Skip the URL field
                    fields.append(key)
                    values.append(value)
            
            placeholders = ', '.join(['?'] * len(values))
            
            insert_query = f'''
            INSERT INTO url_tracking ({', '.join(fields)})
            VALUES ({placeholders})
            '''
            
            cursor.execute(insert_query, values)
            url_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        logging.info(f"Stored profile data for URL: {url}")
        return url_id
        
    except Exception as e:
        logging.error(f"Error storing profile data for URL {url}: {str(e)}")
        return False

def demonstrate_profile_extraction(handle):
    """Demonstrate profile data extraction and storage for a Twitter handle"""
    logging.info(f"Demonstrating profile extraction for handle: {handle}")
    
    # Create URL from handle
    url = f"https://twitter.com/{handle}"
    
    # Extract profile data
    profile_data = extract_profile_data(handle)
    
    if profile_data:
        # Display extracted profile data
        print("\n=== Extracted Profile Data ===")
        print(f"User ID: {profile_data.get('user_id')}")
        print(f"Screen Name: {profile_data.get('screen_name')}")
        print(f"Followers Count: {profile_data.get('followers_count')}")
        print(f"Following Count: {profile_data.get('following_count')}")
        print(f"Tweet Count: {profile_data.get('tweet_count')}")
        print(f"Profile Image URL: {profile_data.get('profile_image_url')}")
        print(f"Profile Banner URL: {profile_data.get('profile_banner_url')}")
        print(f"Verified: {profile_data.get('verified')}")
        print(f"Location: {profile_data.get('location')}")
        print(f"Description: {profile_data.get('description')}")
        print(f"Created At: {profile_data.get('created_at')}")
        print(f"Profile Updated At: {profile_data.get('profile_updated_at')}")
        
        # Create a temporary database for demonstration
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        # Create url_tracking table in the temporary database
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
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
        
        conn.commit()
        conn.close()
        
        # Store profile data in the temporary database
        url_id = store_profile_data(temp_db_path, url, profile_data)
        
        if url_id:
            # Retrieve and display the stored profile data
            conn = sqlite3.connect(temp_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM url_tracking WHERE id = ?", (url_id,))
            url_record = cursor.fetchone()
            
            if url_record:
                url_data = dict(url_record)
                
                print("\n=== Stored Profile Data in url_tracking Table ===")
                
                # Display basic fields
                basic_fields = ['id', 'url', 'user_id', 'screen_name', 'status', 'type', 'subtype']
                print("\n--- Basic Information ---")
                for field in basic_fields:
                    if field in url_data:
                        print(f"{field}: {url_data[field]}")
                
                # Display profile fields
                profile_fields = [
                    'followers_count', 'following_count', 'tweet_count',
                    'profile_image_url', 'profile_banner_url', 'verified',
                    'location', 'description', 'created_at', 'profile_updated_at'
                ]
                print("\n--- Profile Information ---")
                for field in profile_fields:
                    if field in url_data and url_data[field] is not None:
                        print(f"{field}: {url_data[field]}")
                
                # Output as JSON for easier parsing
                print("\n=== JSON Output ===")
                print(json.dumps(url_data, indent=2, default=str))
            
            conn.close()
        
        # Clean up temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
    
    else:
        print(f"Failed to extract profile data for handle: {handle}")

def main():
    """Main function"""
    # Demonstrate profile extraction for cz_binance
    demonstrate_profile_extraction("cz_binance")

if __name__ == "__main__":
    main()
