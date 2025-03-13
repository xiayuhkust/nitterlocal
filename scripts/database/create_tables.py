#!/usr/bin/env python3
"""
Script to create the necessary database tables for the Twitter URL ID Service.
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

def create_url_tracking_table(db_path):
    """Create the url_tracking table in SQLite database"""
    try:
        # Ensure the database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create the url_tracking table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS url_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            type TEXT,
            subtype TEXT,
            user_id TEXT,
            description TEXT,
            status TEXT,
            last_checked TEXT,
            error_count INTEGER DEFAULT 0,
            tweet_count INTEGER DEFAULT 0,
            added_at TEXT,
            UNIQUE(url)
        )
        ''')
        
        # Create an index on the url column for faster lookups
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_url_tracking_url ON url_tracking (url)
        ''')
        
        conn.commit()
        conn.close()
        
        logging.info(f"Created url_tracking table in {db_path}")
        return True
    except Exception as e:
        logging.error(f"Error creating url_tracking table: {str(e)}")
        return False

def create_kol_character_table(db_path):
    """Create the kol_character table in SQLite database"""
    try:
        # Ensure the database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create the kol_character table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS kol_character (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kol_id TEXT,
            kol_screen_name TEXT NOT NULL,
            bio TEXT,
            lore TEXT,
            knowledge TEXT,
            postExamples TEXT,
            topics TEXT,
            style_all TEXT,
            style_chat TEXT,
            style_post TEXT,
            adjectives TEXT,
            UNIQUE(kol_screen_name)
        )
        ''')
        
        # Create an index on the kol_screen_name column for faster lookups
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_kol_character_screen_name ON kol_character (kol_screen_name)
        ''')
        
        conn.commit()
        conn.close()
        
        logging.info(f"Created kol_character table in {db_path}")
        return True
    except Exception as e:
        logging.error(f"Error creating kol_character table: {str(e)}")
        return False

def main():
    """Main function"""
    # Default database path
    db_path = '/home/ubuntu/nitterlocal/data/local_database.db'
    
    # Create the url_tracking table
    if create_url_tracking_table(db_path):
        logging.info("Successfully created url_tracking table")
    else:
        logging.error("Failed to create url_tracking table")
        sys.exit(1)
    
    # Create the kol_character table
    if create_kol_character_table(db_path):
        logging.info("Successfully created kol_character table")
    else:
        logging.error("Failed to create kol_character table")
        sys.exit(1)
    
    logging.info("All tables created successfully")

if __name__ == "__main__":
    main()
