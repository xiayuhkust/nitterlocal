#!/usr/bin/env python3
"""
Script to add profile-related columns to url_tracking table.
This script adds columns for storing Twitter profile information.
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def add_profile_columns(db_path):
    """Add profile-related columns to url_tracking table if they don't exist"""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(url_tracking)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Define new columns to add
        new_columns = {
            'followers_count': 'INTEGER DEFAULT 0',
            'following_count': 'INTEGER DEFAULT 0',
            'tweet_count': 'INTEGER DEFAULT 0',
            'profile_image_url': 'TEXT',
            'profile_banner_url': 'TEXT',
            'verified': 'INTEGER DEFAULT 0',
            'location': 'TEXT',
            'created_at': 'TEXT',
            'profile_updated_at': 'TEXT'
        }
        
        # Add columns that don't exist
        added_columns = []
        for column_name, column_type in new_columns.items():
            if column_name not in columns:
                logging.info(f"Adding {column_name} column to url_tracking table")
                cursor.execute(f"ALTER TABLE url_tracking ADD COLUMN {column_name} {column_type}")
                added_columns.append(column_name)
        
        # Create an index on followers_count for faster sorting
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_url_tracking_followers_count 
        ON url_tracking (followers_count)
        ''')
        
        conn.commit()
        
        if added_columns:
            logging.info(f"Added {len(added_columns)} new columns to url_tracking table: {', '.join(added_columns)}")
        else:
            logging.info("All profile columns already exist in url_tracking table")
        
        return True
    
    except Exception as e:
        logging.error(f"Error adding profile columns: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function"""
    # Default database path
    db_path = '/home/ubuntu/nitterlocal/data/local_database.db'
    
    # Add profile columns
    if add_profile_columns(db_path):
        logging.info("Successfully added profile columns to url_tracking table")
    else:
        logging.error("Failed to add profile columns to url_tracking table")
        sys.exit(1)

if __name__ == "__main__":
    main()
