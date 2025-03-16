#!/usr/bin/env python3
"""
Migration script to ensure all profile-related columns exist in the url_tracking table.
"""

import os
import sys
import logging
import sqlite3
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Default database path
DEFAULT_DB_PATH = '/home/ubuntu/nitterlocal/data/local_database.db'

def ensure_profile_columns(db_path):
    """Ensure all profile-related columns exist in the url_tracking table"""
    logging.info(f"Ensuring profile columns in url_tracking table in {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(url_tracking)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Define columns to ensure
        columns_to_ensure = {
            'followers_count': 'INTEGER DEFAULT 0',
            'following_count': 'INTEGER DEFAULT 0',
            'tweet_count': 'INTEGER DEFAULT 0',
            'profile_image_url': 'TEXT',
            'profile_banner_url': 'TEXT',
            'verified': 'INTEGER DEFAULT 0',
            'location': 'TEXT',
            'created_at': 'TEXT',
            'profile_updated_at': 'TEXT',
            'screen_name': 'TEXT'
        }
        
        # Add columns that don't exist
        added_columns = []
        for column_name, column_type in columns_to_ensure.items():
            if column_name not in columns:
                logging.info(f"Adding column {column_name} ({column_type})")
                cursor.execute(f"ALTER TABLE url_tracking ADD COLUMN {column_name} {column_type}")
                added_columns.append(column_name)
            else:
                logging.info(f"Column {column_name} already exists")
        
        # Create indexes for faster queries
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_url_tracking_followers_count 
        ON url_tracking (followers_count)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_url_tracking_screen_name 
        ON url_tracking (screen_name)
        ''')
        
        conn.commit()
        
        if added_columns:
            logging.info(f"Added {len(added_columns)} new columns to url_tracking table: {', '.join(added_columns)}")
        else:
            logging.info("All profile columns already exist in url_tracking table")
        
        # Display the updated schema
        cursor.execute("PRAGMA table_info(url_tracking)")
        schema = cursor.fetchall()
        print("\n=== Updated Schema for table 'url_tracking' ===")
        print("ID    Name                 Type            NotNull  Default         PK")
        print("----------------------------------------------------------------------")
        for column in schema:
            print(f"{column[0]:<5} {column[1]:<20} {column[2]:<15} {column[3]:<8} {str(column[4]):<15} {column[5]}")
        
        return True
    except Exception as e:
        logging.error(f"Error ensuring profile columns: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Ensure profile columns in url_tracking table')
    parser.add_argument('--db-path', default=DEFAULT_DB_PATH, help='Path to SQLite database')
    args = parser.parse_args()
    
    ensure_profile_columns(args.db_path)

if __name__ == "__main__":
    main()
