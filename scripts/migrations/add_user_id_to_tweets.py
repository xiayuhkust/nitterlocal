#!/usr/bin/env python3
"""
Database migration script.
This script adds a user_id column to the tweets table.
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
    """Migrate the database to add user_id column to tweets table"""
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
        
        # Check if the user_id column already exists in the tweets table
        cursor.execute("PRAGMA table_info(tweets)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' in columns:
            logging.info("user_id column already exists in tweets table")
            conn.close()
            return True
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Add user_id column to tweets table
        cursor.execute("ALTER TABLE tweets ADD COLUMN user_id TEXT")
        
        # Create an index on the user_id column
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_user_id ON tweets (user_id)")
        
        # Update existing tweets with user_id from url_tracking table
        cursor.execute("""
        UPDATE tweets
        SET user_id = (
            SELECT user_id
            FROM url_tracking
            WHERE url_tracking.url = tweets.source_url
        )
        WHERE EXISTS (
            SELECT 1
            FROM url_tracking
            WHERE url_tracking.url = tweets.source_url
            AND url_tracking.user_id IS NOT NULL
        )
        """)
        
        # Commit the transaction
        conn.commit()
        
        # Get the number of updated tweets
        cursor.execute("SELECT COUNT(*) FROM tweets WHERE user_id IS NOT NULL")
        updated_count = cursor.fetchone()[0]
        
        # Get the total number of tweets
        cursor.execute("SELECT COUNT(*) FROM tweets")
        total_count = cursor.fetchone()[0]
        
        logging.info(f"Added user_id column to tweets table")
        logging.info(f"Updated {updated_count} out of {total_count} tweets with user_id")
        
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
    parser = argparse.ArgumentParser(description='Migrate the database to add user_id column to tweets table')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the database')
    parser.add_argument('--no-backup', action='store_true', help='Do not create a backup of the database')
    
    args = parser.parse_args()
    
    migrate_database(args.db_path, backup=not args.no_backup)
