#!/usr/bin/env python3
"""
Migration script to add reply fields to the tweets table.
This script adds is_reply, in_reply_to_status_id, and conversation_id fields to the tweets table.
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

def add_reply_fields(db_path='data/local_database.db'):
    """Add reply fields to the tweets table"""
    logging.info(f"Adding reply fields to tweets table in {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the fields already exist
        cursor.execute("PRAGMA table_info(tweets)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add is_reply field if it doesn't exist
        if 'is_reply' not in columns:
            logging.info("Adding is_reply field to tweets table")
            cursor.execute("ALTER TABLE tweets ADD COLUMN is_reply INTEGER DEFAULT 0")
        
        # Add in_reply_to_status_id field if it doesn't exist
        if 'in_reply_to_status_id' not in columns:
            logging.info("Adding in_reply_to_status_id field to tweets table")
            cursor.execute("ALTER TABLE tweets ADD COLUMN in_reply_to_status_id TEXT")
        
        # Add conversation_id field if it doesn't exist
        if 'conversation_id' not in columns:
            logging.info("Adding conversation_id field to tweets table")
            cursor.execute("ALTER TABLE tweets ADD COLUMN conversation_id TEXT")
        
        # Create an index on the is_reply column for faster lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_is_reply ON tweets (is_reply)")
        
        # Create an index on the in_reply_to_status_id column for faster lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_in_reply_to_status_id ON tweets (in_reply_to_status_id)")
        
        # Create an index on the conversation_id column for faster lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_conversation_id ON tweets (conversation_id)")
        
        # Commit the changes
        conn.commit()
        
        logging.info("Reply fields added successfully")
        
    except Exception as e:
        logging.error(f"Error adding reply fields: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()
    
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Add reply fields to the tweets table')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    
    args = parser.parse_args()
    
    # Add reply fields
    add_reply_fields(args.db_path)

if __name__ == "__main__":
    main()
