#!/usr/bin/env python3
"""
Fix the kol_character table schema in the SQLite database.
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

def fix_kol_character_table():
    """Fix the kol_character table schema in the SQLite database"""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if kol_character table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kol_character'")
        if cursor.fetchone() is None:
            # Create kol_character table with id column
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
                url_tracking_id INTEGER,
                UNIQUE(kol_screen_name)
            )
            ''')
            conn.commit()
            logging.info("Created kol_character table with id column")
        else:
            # Check if id column exists
            cursor.execute("PRAGMA table_info(kol_character)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'id' not in columns:
                # Create a new table with id column
                cursor.execute('''
                CREATE TABLE kol_character_new (
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
                    url_tracking_id INTEGER,
                    UNIQUE(kol_screen_name)
                )
                ''')
                
                # Copy data from old table to new table
                cursor.execute('''
                INSERT INTO kol_character_new (
                    kol_id, kol_screen_name, bio, lore, knowledge, postExamples,
                    topics, style_all, style_chat, style_post, adjectives, url_tracking_id
                )
                SELECT 
                    kol_id, kol_screen_name, bio, lore, knowledge, postExamples,
                    topics, style_all, style_chat, style_post, adjectives, url_tracking_id
                FROM kol_character
                ''')
                
                # Drop old table
                cursor.execute("DROP TABLE kol_character")
                
                # Rename new table to old table name
                cursor.execute("ALTER TABLE kol_character_new RENAME TO kol_character")
                
                conn.commit()
                logging.info("Added id column to kol_character table")
            else:
                logging.info("id column already exists in kol_character table")
        
        # Create an index on the kol_screen_name column for faster lookups
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_kol_character_screen_name ON kol_character (kol_screen_name)
        ''')
        
        conn.commit()
        conn.close()
        
        logging.info("Fixed kol_character table schema")
        return True
    
    except Exception as e:
        logging.error(f"Error fixing kol_character table schema: {str(e)}")
        return False

if __name__ == "__main__":
    fix_kol_character_table()
