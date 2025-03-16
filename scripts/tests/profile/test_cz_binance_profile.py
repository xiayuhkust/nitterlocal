#!/usr/bin/env python3
"""
Test script to verify profile data update for cz_binance.
"""

import os
import sys
import logging
import sqlite3
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.append('/home/ubuntu/nitterlocal')

# Import the profile updater
from scripts.profile.update_profile_data import ProfileUpdater

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_cz_binance_profile_update():
    """Test profile data update for cz_binance"""
    logging.info("Testing profile data update for cz_binance")
    
    # Create a profile updater
    updater = ProfileUpdater()
    
    # Update profile for cz_binance
    handle = "cz_binance"
    url = f"https://twitter.com/{handle}"
    
    logging.info(f"Updating profile for {handle}")
    # Get profile data first
    profile_data = updater.get_profile_data(handle)
    
    # Then update the profile in the database
    result = updater.update_profile_in_db(url, profile_data) if profile_data else False
    
    if result:
        logging.info(f"Successfully updated profile for {handle}")
        
        # Get the updated profile data
        conn = sqlite3.connect('/home/ubuntu/nitterlocal/data/local_database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM url_tracking WHERE screen_name = ?", (handle,))
        url_record = cursor.fetchone()
        
        if url_record:
            print("\n=== Profile Data for cz_binance ===")
            url_data = dict(url_record)
            
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
                'location', 'created_at', 'profile_updated_at'
            ]
            print("\n--- Profile Information ---")
            for field in profile_fields:
                if field in url_data and url_data[field] is not None:
                    print(f"{field}: {url_data[field]}")
            
            # Verify user_id matches expected value
            expected_user_id = "902926941413453824"
            if url_data.get('user_id') == expected_user_id:
                print(f"\nSUCCESS: user_id matches expected value: {expected_user_id}")
            else:
                print(f"\nWARNING: user_id {url_data.get('user_id')} does not match expected value: {expected_user_id}")
            
            # Output as JSON for easier parsing
            print("\n=== JSON Output ===")
            print(json.dumps(url_data, indent=2, default=str))
        else:
            print(f"No record found for {handle}")
        
        conn.close()
    else:
        logging.error(f"Failed to update profile for {handle}")

if __name__ == "__main__":
    test_cz_binance_profile_update()
