#!/usr/bin/env python3
"""
Script to check the schema of the url_tracking table and add missing columns.
"""

import os
import sys
import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_and_update_schema(db_path):
    """Check the schema of the url_tracking table and add missing columns"""
    logging.info(f"Checking schema for database at {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if url_tracking table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='url_tracking'")
    if cursor.fetchone() is None:
        logging.error("url_tracking table does not exist")
        conn.close()
        return False
    
    # Get current columns
    cursor.execute("PRAGMA table_info(url_tracking)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    
    logging.info(f"Current columns: {columns}")
    
    # Define required columns
    required_columns = {
        'url': 'TEXT',
        'user_id': 'TEXT',
        'screen_name': 'TEXT',
        'kol_name': 'TEXT',
        'followers_count': 'INTEGER',
        'following_count': 'INTEGER',
        'tweet_count': 'INTEGER',
        'profile_image_url': 'TEXT',
        'profile_banner_url': 'TEXT',
        'verified': 'INTEGER',
        'location': 'TEXT',
        'description': 'TEXT',
        'created_at': 'TEXT',
        'profile_updated_at': 'TEXT'
    }
    
    # Add missing columns
    for column, data_type in required_columns.items():
        if column not in columns:
            try:
                logging.info(f"Adding column {column} ({data_type}) to url_tracking table")
                cursor.execute(f"ALTER TABLE url_tracking ADD COLUMN {column} {data_type}")
            except sqlite3.Error as e:
                logging.error(f"Error adding column {column}: {e}")
    
    # Commit changes
    conn.commit()
    
    # Verify columns were added
    cursor.execute("PRAGMA table_info(url_tracking)")
    updated_columns = {row[1]: row[2] for row in cursor.fetchall()}
    
    logging.info(f"Updated columns: {updated_columns}")
    
    # Close connection
    conn.close()
    
    return True

def main():
    """Main function"""
    # Get database path
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/local_database.db'))
    
    # Check and update schema
    if check_and_update_schema(db_path):
        logging.info("Schema check and update completed successfully")
    else:
        logging.error("Schema check and update failed")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
