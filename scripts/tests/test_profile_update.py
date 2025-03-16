#!/usr/bin/env python3
"""
Test script to verify the profile update functionality.
"""

import os
import sys
import logging
import sqlite3
import subprocess
import json

# Add the project root to the Python path
sys.path.append('/home/ubuntu/nitterlocal')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_profile_update(db_path, target_url):
    """Test the profile update functionality"""
    logging.info(f"Testing profile update for URL: {target_url}")
    
    try:
        # Step 1: Ensure profile columns exist in url_tracking table
        subprocess.run(['python3', '/home/ubuntu/nitterlocal/scripts/migrations/add_profile_columns.py'], check=True)
        
        # Step 2: Run the profile update script for the target URL
        # First, get the URL ID from the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM url_tracking WHERE url LIKE ?", (f"%{target_url}%",))
        url_id = cursor.fetchone()
        
        if not url_id:
            logging.warning(f"URL not found in database: {target_url}")
            return False
        
        # Run the profile update script
        subprocess.run([
            'python3', '/home/ubuntu/nitterlocal/scripts/profile/update_profile_data.py',
            '--limit', '1'
        ], check=True)
        
        # Step 3: Check if the profile data was updated
        cursor.execute("SELECT * FROM url_tracking WHERE url LIKE ?", (f"%{target_url}%",))
        url_record = cursor.fetchone()
        
        if url_record:
            columns = [col[0] for col in cursor.description]
            url_data = dict(zip(columns, url_record))
            
            logging.info("Profile data in url_tracking table:")
            for key, value in url_data.items():
                if key in ['followers_count', 'following_count', 'tweet_count', 'profile_image_url', 
                          'profile_banner_url', 'verified', 'location', 'created_at', 'profile_updated_at']:
                    logging.info(f"  {key}: {value}")
            
            # Check if profile data was updated
            if url_data.get('followers_count') or url_data.get('profile_updated_at'):
                logging.info("SUCCESS: Profile data was updated")
                return True
            else:
                logging.warning("WARNING: Profile data was not updated")
                return False
        else:
            logging.warning(f"URL not found in database after update: {target_url}")
            return False
    
    except Exception as e:
        logging.error(f"Error testing profile update: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function"""
    # Path to the SQLite database
    db_path = "/home/ubuntu/nitterlocal/data/local_database.db"
    
    # Target URL
    target_url = "cz_binance"
    
    # Test the profile update
    test_profile_update(db_path, target_url)

if __name__ == "__main__":
    main()
