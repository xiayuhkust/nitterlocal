#!/usr/bin/env python3
"""
Fix the url_tracking table schema in the SQLite database by adding missing profile columns.
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

# SQLite database path
db_path = '/home/ubuntu/nitterlocal/data/local_database.db'

def fix_url_tracking_table():
    """Fix the url_tracking table schema in the SQLite database by adding missing profile columns"""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if url_tracking table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='url_tracking'")
        if cursor.fetchone() is None:
            # Create url_tracking table with all required columns
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS url_tracking (
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
                last_error TEXT,
                subtype TEXT DEFAULT '-',
                screen_name TEXT,
                followers_count INTEGER DEFAULT 0,
                following_count INTEGER DEFAULT 0,
                profile_image_url TEXT,
                profile_banner_url TEXT,
                verified INTEGER DEFAULT 0,
                location TEXT,
                created_at TEXT,
                profile_updated_at TEXT,
                kol_name TEXT
            )
            ''')
            conn.commit()
            logging.info("Created url_tracking table with all required columns")
            return True
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(url_tracking)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Define required profile columns with their types and defaults
        profile_columns = {
            'followers_count': 'INTEGER DEFAULT 0',
            'following_count': 'INTEGER DEFAULT 0',
            'tweet_count': 'INTEGER DEFAULT 0',
            'profile_image_url': 'TEXT',
            'profile_banner_url': 'TEXT',
            'verified': 'INTEGER DEFAULT 0',
            'location': 'TEXT',
            'created_at': 'TEXT',
            'profile_updated_at': 'TEXT',
            'kol_name': 'TEXT'
        }
        
        # Add missing columns
        for column, column_type in profile_columns.items():
            if column not in columns:
                try:
                    cursor.execute(f"ALTER TABLE url_tracking ADD COLUMN {column} {column_type}")
                    logging.info(f"Added {column} column to url_tracking table")
                except Exception as e:
                    logging.error(f"Error adding {column} column: {str(e)}")
        
        # Create an index on the screen_name column for faster lookups
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_url_tracking_screen_name ON url_tracking (screen_name)
        ''')
        
        conn.commit()
        conn.close()
        
        logging.info("Fixed url_tracking table schema")
        return True
    
    except Exception as e:
        logging.error(f"Error fixing url_tracking table schema: {str(e)}")
        return False

if __name__ == "__main__":
    fix_url_tracking_table()
