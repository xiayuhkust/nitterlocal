#!/usr/bin/env python3
"""
Debug script to investigate why kol_name is not being saved to the database.
This script will trace the update_profile_in_db function execution.
"""

import os
import sys
import logging
import sqlite3
import argparse
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed logging
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def debug_profile_update(db_path, handle):
    """Debug profile update for a Twitter handle"""
    logging.info(f"Debugging profile update for handle: {handle}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get URL from handle
        cursor.execute("SELECT url FROM url_tracking WHERE url LIKE ? COLLATE NOCASE", (f"%twitter.com/{handle}%",))
        result = cursor.fetchone()
        
        if not result:
            logging.error(f"No URL found for handle: {handle}")
            conn.close()
            return False
        
        url = result[0]
        logging.info(f"Found URL for handle {handle}: {url}")
        
        # Get current record data
        cursor.execute("SELECT * FROM url_tracking WHERE url = ?", (url,))
        row = cursor.fetchone()
        
        if not row:
            logging.error(f"No record found for URL: {url}")
            conn.close()
            return False
        
        # Get column names
        column_names = [description[0] for description in cursor.description]
        record_data = dict(zip(column_names, row))
        
        logging.info(f"Current record data: {record_data}")
        
        # Create test profile data
        test_profile_data = {
            'user_id': record_data.get('user_id', ''),
            'screen_name': handle,
            'followers_count': 9999999,  # Use a distinctive number for testing
            'following_count': 1234,
            'tweet_count': 5678,
            'profile_image_url': 'https://example.com/test_image.jpg',
            'profile_banner_url': 'https://example.com/test_banner.jpg',
            'verified': 1,
            'location': 'Test Location',
            'description': 'Test Description',
            'created_at': '2017-08-30T16:12:13.000Z',
            'kol_name': 'TEST KOL NAME',  # Use a distinctive name for testing
            'profile_updated_at': datetime.now().isoformat()
        }
        
        logging.info(f"Test profile data: {test_profile_data}")
        
        # Build update query with only columns that exist in the table
        # Get table schema
        cursor.execute("PRAGMA table_info(url_tracking)")
        table_info = cursor.fetchall()
        table_columns = [row[1] for row in table_info]
        
        logging.info(f"Table columns: {table_columns}")
        
        # Check if kol_name column exists
        if 'kol_name' not in table_columns:
            logging.error("kol_name column does not exist in url_tracking table")
            # Add the column if it doesn't exist
            try:
                cursor.execute("ALTER TABLE url_tracking ADD COLUMN kol_name TEXT")
                conn.commit()
                logging.info("Added kol_name column to url_tracking table")
                # Refresh table columns
                cursor.execute("PRAGMA table_info(url_tracking)")
                table_info = cursor.fetchall()
                table_columns = [row[1] for row in table_info]
            except sqlite3.Error as e:
                logging.error(f"Error adding kol_name column: {e}")
        
        # Build update query
        update_fields = []
        update_values = []
        
        for key, value in test_profile_data.items():
            # Skip the URL field and any fields not in the table
            if key != 'url' and key in table_columns:
                update_fields.append(f"{key} = ?")
                update_values.append(value)
                logging.debug(f"Adding field to update: {key} = {value}")
            elif key != 'url':
                logging.warning(f"Skipping field not in table: {key}")
        
        # If we have no valid fields to update, return
        if not update_fields:
            logging.warning(f"No valid fields to update for URL: {url}")
            conn.close()
            return False
            
        # Add URL for WHERE clause
        update_values.append(url)
        
        # Execute update query
        update_query = f'''
        UPDATE url_tracking 
        SET {', '.join(update_fields)}
        WHERE url = ?
        '''
        
        logging.info(f"Update query: {update_query}")
        logging.info(f"Update values: {update_values}")
        
        cursor.execute(update_query, update_values)
        conn.commit()
        
        # Verify the update
        cursor.execute("SELECT * FROM url_tracking WHERE url = ?", (url,))
        updated_row = cursor.fetchone()
        updated_data = dict(zip(column_names, updated_row))
        
        logging.info(f"Updated record data: {updated_data}")
        
        # Check if kol_name was updated
        if updated_data.get('kol_name') == 'TEST KOL NAME':
            logging.info("kol_name was successfully updated")
        else:
            logging.error(f"kol_name was not updated. Current value: {updated_data.get('kol_name')}")
        
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error debugging profile update: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Debug profile update for Twitter handle')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the SQLite database')
    parser.add_argument('--handle', type=str, default='cz_binance', help='Twitter handle to debug')
    
    args = parser.parse_args()
    
    # Resolve database path
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', args.db_path))
    
    # Debug profile update
    if debug_profile_update(db_path, args.handle):
        print(f"Successfully debugged profile update for handle: {args.handle}")
    else:
        print(f"Failed to debug profile update for handle: {args.handle}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
