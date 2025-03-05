#!/usr/bin/env python3
"""
Database migration script.
This script adds reply-related fields to the tweets table.
"""

import os
import sys
import logging
import sqlite3
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def migrate_database(db_path, backup=True):
    """Migrate the database to add reply-related fields to tweets table"""
    logging.info(f"Migrating database at {db_path}")
    
    # Create a backup of the database
    if backup:
        backup_path = f"{db_path}.backup_{int(datetime.now().timestamp())}"
        logging.info(f"Creating backup at {backup_path}")
        
        try:
            import shutil
            shutil.copy2(db_path, backup_path)
            logging.info(f"Backup created successfully")
        except Exception as e:
            logging.error(f"Error creating backup: {str(e)}")
            return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the reply-related columns already exist in the tweets table
        cursor.execute("PRAGMA table_info(tweets)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Add is_reply column if it doesn't exist
        if 'is_reply' not in columns:
            cursor.execute("ALTER TABLE tweets ADD COLUMN is_reply BOOLEAN DEFAULT 0")
            logging.info("Added is_reply column to tweets table")
        else:
            logging.info("is_reply column already exists in tweets table")
        
        # Add in_reply_to_status_id column if it doesn't exist
        if 'in_reply_to_status_id' not in columns:
            cursor.execute("ALTER TABLE tweets ADD COLUMN in_reply_to_status_id TEXT")
            logging.info("Added in_reply_to_status_id column to tweets table")
        else:
            logging.info("in_reply_to_status_id column already exists in tweets table")
        
        # Add conversation_id column if it doesn't exist
        if 'conversation_id' not in columns:
            cursor.execute("ALTER TABLE tweets ADD COLUMN conversation_id TEXT")
            logging.info("Added conversation_id column to tweets table")
        else:
            logging.info("conversation_id column already exists in tweets table")
        
        # Create indexes on the new columns
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_is_reply ON tweets (is_reply)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_in_reply_to_status_id ON tweets (in_reply_to_status_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_conversation_id ON tweets (conversation_id)")
        
        # Commit the transaction
        conn.commit()
        
        logging.info(f"Added reply-related fields to tweets table")
        
        conn.close()
        
        return True
        
    except Exception as e:
        logging.error(f"Error migrating database: {str(e)}")
        
        # Rollback the transaction
        try:
            conn.rollback()
        except:
            pass
        
        try:
            conn.close()
        except:
            pass
        
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Migrate the database to add reply-related fields to tweets table')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the database')
    parser.add_argument('--no-backup', action='store_true', help='Do not create a backup of the database')
    
    args = parser.parse_args()
    
    migrate_database(args.db_path, backup=not args.no_backup)
