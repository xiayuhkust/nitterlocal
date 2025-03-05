#!/usr/bin/env python3
"""
Migration script to add user_id and subtype fields to the url_tracking table.
This script adds user_id and subtype columns to the url_tracking table.
"""

import os
import sys
import logging
import sqlite3
import argparse

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def add_fields_to_url_tracking(db_path='data/local_database.db'):
    """Add user_id and subtype fields to the url_tracking table"""
    logging.info(f"Adding user_id and subtype fields to url_tracking table in {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the fields already exist
        cursor.execute("PRAGMA table_info(url_tracking)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add user_id field if it doesn't exist
        if 'user_id' not in columns:
            logging.info("Adding user_id field to url_tracking table")
            cursor.execute("ALTER TABLE url_tracking ADD COLUMN user_id TEXT")
        else:
            logging.info("user_id field already exists in url_tracking table")
        
        # Add subtype field if it doesn't exist
        if 'subtype' not in columns:
            logging.info("Adding subtype field to url_tracking table")
            cursor.execute("ALTER TABLE url_tracking ADD COLUMN subtype TEXT")
        else:
            logging.info("subtype field already exists in url_tracking table")
        
        # Create an index on the user_id column for faster lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_url_tracking_user_id ON url_tracking (user_id)")
        
        # Commit the changes
        conn.commit()
        
        logging.info("Fields added successfully to url_tracking table")
        
    except Exception as e:
        logging.error(f"Error adding fields to url_tracking table: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()
    
    return True

def add_user_id_to_tweets(db_path='data/local_database.db'):
    """Add user_id field to the tweets table"""
    logging.info(f"Adding user_id field to tweets table in {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the field already exists
        cursor.execute("PRAGMA table_info(tweets)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add user_id field if it doesn't exist
        if 'user_id' not in columns:
            logging.info("Adding user_id field to tweets table")
            cursor.execute("ALTER TABLE tweets ADD COLUMN user_id TEXT")
            
            # Create an index on the user_id column for faster lookups
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_user_id ON tweets (user_id)")
            
            # Commit the changes
            conn.commit()
            
            logging.info("user_id field added successfully to tweets table")
        else:
            logging.info("user_id field already exists in tweets table")
        
    except Exception as e:
        logging.error(f"Error adding user_id field to tweets table: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()
    
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Add user_id and subtype fields to the url_tracking table and user_id field to the tweets table')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    
    args = parser.parse_args()
    
    # Add fields to url_tracking table
    if add_fields_to_url_tracking(args.db_path):
        logging.info("Successfully added fields to url_tracking table")
    else:
        logging.error("Failed to add fields to url_tracking table")
        return 1
    
    # Add user_id field to tweets table
    if add_user_id_to_tweets(args.db_path):
        logging.info("Successfully added user_id field to tweets table")
    else:
        logging.error("Failed to add user_id field to tweets table")
        return 1
    
    logging.info("Migration completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
