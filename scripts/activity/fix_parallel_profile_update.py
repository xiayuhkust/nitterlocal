#!/usr/bin/env python3
"""
Script to fix parallel profile update in dynamic_update.py.
This script demonstrates how to create a new SQLite connection in each thread.
"""

import os
import sys
import sqlite3
import logging
import argparse
import concurrent.futures
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def update_profile_in_db(db_path, url, profile_data):
    """Update profile data in the database using a new connection"""
    if not profile_data:
        logging.error(f"No profile data to update for URL: {url}")
        return False
    
    try:
        # Create a new connection in this thread
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Build update query
        update_fields = []
        update_values = []
        
        for key, value in profile_data.items():
            if key != 'url':  # Skip the URL field
                update_fields.append(f"{key} = ?")
                update_values.append(value)
        
        # Add URL for WHERE clause
        update_values.append(url)
        
        # Execute update query
        update_query = f'''
        UPDATE url_tracking 
        SET {', '.join(update_fields)}
        WHERE url = ?
        '''
        
        cursor.execute(update_query, update_values)
        conn.commit()
        conn.close()
        
        logging.info(f"Updated profile data for URL: {url}")
        return True
    except sqlite3.Error as e:
        logging.error(f"Error updating profile data for URL {url}: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Fix parallel profile update in dynamic_update.py')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the SQLite database')
    
    args = parser.parse_args()
    
    # Resolve database path
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', args.db_path))
    
    # Example profile data
    profile_data = {
        'user_id': '123456789',
        'screen_name': 'example_user',
        'followers_count': 1000,
        'following_count': 500,
        'tweet_count': 100,
        'profile_image_url': 'https://example.com/image.jpg',
        'profile_banner_url': 'https://example.com/banner.jpg',
        'verified': 1,
        'location': 'Example Location',
        'description': 'Example Description',
        'created_at': '2020-01-01T00:00:00.000Z',
        'kol_name': 'Example User',
        'profile_updated_at': datetime.now().isoformat()
    }
    
    # Example URLs
    urls = [
        'https://twitter.com/example_user1',
        'https://twitter.com/example_user2',
        'https://twitter.com/example_user3'
    ]
    
    # Update profile data in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all URLs to the thread pool
        future_to_url = {executor.submit(update_profile_in_db, db_path, url, profile_data): url for url in urls}
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                if result:
                    logging.info(f"Successfully updated profile data for URL: {url}")
                else:
                    logging.error(f"Failed to update profile data for URL: {url}")
            except Exception as e:
                logging.error(f"Exception occurred while updating profile data for URL {url}: {str(e)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
