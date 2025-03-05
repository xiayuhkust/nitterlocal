#!/usr/bin/env python3
"""
Migration script to change the primary key of the url_tracking table from user_id to url.
This script creates a new table with the desired schema, copies the data, and then replaces the old table.
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

def change_primary_key_to_url(db_path, dry_run=False):
    """Change the primary key of the url_tracking table from user_id to url"""
    logging.info(f"Changing primary key of url_tracking table from user_id to url in database at {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='url_tracking'")
        if not cursor.fetchone():
            logging.error("url_tracking table does not exist")
            conn.close()
            return False
        
        # Get the current schema
        cursor.execute("PRAGMA table_info(url_tracking)")
        columns = cursor.fetchall()
        
        # Check if user_id is the primary key
        user_id_is_pk = False
        for column in columns:
            if column[1] == 'user_id' and column[5] == 1:  # column[5] is the pk flag
                user_id_is_pk = True
                break
        
        if not user_id_is_pk:
            logging.info("user_id is not the primary key, no need to change")
            conn.close()
            return True
        
        logging.info("user_id is the primary key, changing to url")
        
        if not dry_run:
            # Create a new table with url as the primary key
            cursor.execute('''
            CREATE TABLE url_tracking_new (
                url TEXT PRIMARY KEY,
                user_id TEXT,
                description TEXT,
                status TEXT DEFAULT 'active',
                last_checked TEXT,
                error_count INTEGER DEFAULT 0,
                tweet_count INTEGER DEFAULT 0,
                type TEXT,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_scraped TEXT,
                last_error TEXT
            )
            ''')
            
            # Copy data from the old table to the new table
            cursor.execute('''
            INSERT OR IGNORE INTO url_tracking_new (
                url, user_id, description, status, last_checked, error_count, tweet_count, type, added_at, last_scraped, last_error
            )
            SELECT url, user_id, description, status, last_checked, error_count, tweet_count, type, added_at, last_scraped, last_error
            FROM url_tracking
            ''')
            
            # Drop the old table
            cursor.execute("DROP TABLE url_tracking")
            
            # Rename the new table to the old name
            cursor.execute("ALTER TABLE url_tracking_new RENAME TO url_tracking")
            
            # Create an index on the url column for faster lookups
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_url_tracking_url ON url_tracking (url)
            ''')
            
            # Create an index on the user_id column for faster lookups
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_url_tracking_user_id ON url_tracking (user_id)
            ''')
            
            conn.commit()
            logging.info("Primary key changed from user_id to url")
        else:
            logging.info("[DRY RUN] Would change primary key from user_id to url")
        
        conn.close()
        
        return True
        
    except Exception as e:
        logging.error(f"Error changing primary key: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Change the primary key of the url_tracking table from user_id to url')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making changes')
    
    args = parser.parse_args()
    
    # Change the primary key
    change_primary_key_to_url(db_path=args.db_path, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
