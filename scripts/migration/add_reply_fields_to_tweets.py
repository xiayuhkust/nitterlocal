#!/usr/bin/env python3
"""
Migration script to add reply-related fields to the tweets table:
- is_reply (INTEGER): Indicates whether a tweet is a reply (0/1)
- reply_to (TEXT): The ID of the tweet being replied to
- conversation_id (TEXT): The conversation ID

This script follows the same pattern as other migration scripts in this directory.
"""

import os
import sys
import logging
import sqlite3
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def migrate_database(db_path=None):
    """Add reply-related fields to the tweets table"""
    if db_path is None:
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data/local_database.db')
    
    logging.info(f"Migrating database at {db_path}")
    
    # Create a backup of the database before migration
    backup_path = f"{db_path}.backup_add_reply_fields"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        logging.info(f"Created database backup at {backup_path}")
    except Exception as e:
        logging.error(f"Error creating database backup: {str(e)}")
        if input("Continue without backup? (y/n): ").lower() != 'y':
            return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the tweets table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tweets'")
        if not cursor.fetchone():
            logging.error("Tweets table does not exist in the database")
            conn.close()
            return False
        
        # Check if the columns already exist
        cursor.execute("PRAGMA table_info(tweets)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add the is_reply column if it doesn't exist
        if 'is_reply' not in columns:
            logging.info("Adding is_reply column to tweets table")
            cursor.execute("ALTER TABLE tweets ADD COLUMN is_reply INTEGER DEFAULT 0")
        else:
            logging.info("is_reply column already exists in tweets table")
        
        # Add the reply_to column if it doesn't exist
        if 'reply_to' not in columns:
            logging.info("Adding reply_to column to tweets table")
            cursor.execute("ALTER TABLE tweets ADD COLUMN reply_to TEXT")
        else:
            logging.info("reply_to column already exists in tweets table")
        
        # Add the conversation_id column if it doesn't exist
        if 'conversation_id' not in columns:
            logging.info("Adding conversation_id column to tweets table")
            cursor.execute("ALTER TABLE tweets ADD COLUMN conversation_id TEXT")
        else:
            logging.info("conversation_id column already exists in tweets table")
        
        # Commit the changes
        conn.commit()
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(tweets)")
        columns = [column[1] for column in cursor.fetchall()]
        logging.info(f"Tweets table columns after migration: {columns}")
        
        # Close the connection
        conn.close()
        
        logging.info("Migration completed successfully")
        return True
    except Exception as e:
        logging.error(f"Error during migration: {str(e)}")
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Add reply-related fields to the tweets table')
    parser.add_argument('--db-path', help='Path to the SQLite database file')
    
    args = parser.parse_args()
    
    migrate_database(args.db_path)

if __name__ == "__main__":
    main()
