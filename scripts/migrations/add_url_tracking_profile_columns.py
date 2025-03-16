#!/usr/bin/env python3
"""
Migration script to add profile-related columns to the url_tracking table.
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

def add_profile_columns(db_path):
    """Add profile-related columns to the url_tracking table"""
    logging.info(f"Adding profile columns to url_tracking table in {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(url_tracking)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Define columns to add
        columns_to_add = {
            'followers_count': 'INTEGER',
            'following_count': 'INTEGER',
            'profile_image_url': 'TEXT',
            'profile_banner_url': 'TEXT',
            'verified': 'INTEGER',
            'location': 'TEXT',
            'created_at': 'TEXT',
            'profile_updated_at': 'TEXT'
        }
        
        # Add columns if they don't exist
        for column_name, column_type in columns_to_add.items():
            if column_name not in columns:
                logging.info(f"Adding column {column_name} ({column_type})")
                cursor.execute(f"ALTER TABLE url_tracking ADD COLUMN {column_name} {column_type}")
            else:
                logging.info(f"Column {column_name} already exists")
        
        # Commit changes
        conn.commit()
        logging.info("Successfully added profile columns to url_tracking table")
        
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
        logging.error(f"Error adding profile columns: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Add profile columns to url_tracking table')
    parser.add_argument('--db-path', default=DEFAULT_DB_PATH, help='Path to SQLite database')
    args = parser.parse_args()
    
    add_profile_columns(args.db_path)

if __name__ == "__main__":
    main()
