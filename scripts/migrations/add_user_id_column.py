#!/usr/bin/env python3
"""
Database migration script.
This script adds the user_id column to the url_tracking table.
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

def migrate_database(db_path):
    """Migrate the database to add the user_id column"""
    logging.info(f"Migrating database at {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the user_id column already exists
        cursor.execute("PRAGMA table_info(url_tracking)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' not in columns:
            # Add the user_id column
            cursor.execute("ALTER TABLE url_tracking ADD COLUMN user_id TEXT")
            
            # Create an index on the user_id column
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_url_tracking_user_id ON url_tracking (user_id)")
            
            conn.commit()
            logging.info("Added user_id column to url_tracking table")
        else:
            logging.info("user_id column already exists in url_tracking table")
        
        conn.close()
        
        return True
        
    except Exception as e:
        logging.error(f"Error migrating database: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Migrate the database to add the user_id column')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the database')
    
    args = parser.parse_args()
    
    migrate_database(args.db_path)
