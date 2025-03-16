#!/usr/bin/env python3
"""
Script to add url_tracking_id column to kol_character table.
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

def add_url_tracking_id_column(db_path):
    """Add url_tracking_id column to kol_character table if it doesn't exist"""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if url_tracking_id column exists
        cursor.execute("PRAGMA table_info(kol_character)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'url_tracking_id' not in columns:
            logging.info("Adding url_tracking_id column to kol_character table")
            cursor.execute("ALTER TABLE kol_character ADD COLUMN url_tracking_id INTEGER")
            
            # Create an index on the url_tracking_id column
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_kol_character_url_tracking_id 
            ON kol_character (url_tracking_id)
            ''')
            
            conn.commit()
            logging.info("Added url_tracking_id column to kol_character table")
            return True
        else:
            logging.info("url_tracking_id column already exists in kol_character table")
            return False
    
    except Exception as e:
        logging.error(f"Error adding url_tracking_id column: {str(e)}")
        return False

if __name__ == "__main__":
    # Default database path
    db_path = '/home/ubuntu/nitterlocal/data/local_database.db'
    
    # Add url_tracking_id column
    add_url_tracking_id_column(db_path)
