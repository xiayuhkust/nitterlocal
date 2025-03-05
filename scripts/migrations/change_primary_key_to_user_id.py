#!/usr/bin/env python3
"""
Database migration script.
This script changes the primary key of the url_tracking table from url to user_id.
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
    """Migrate the database to change the primary key from url to user_id"""
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
        
        # Check if the user_id column exists
        cursor.execute("PRAGMA table_info(url_tracking)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' not in columns:
            logging.error("user_id column does not exist in url_tracking table. Run add_user_id_column.py first.")
            conn.close()
            return False
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Create a new table with user_id as the primary key
        cursor.execute("""
        CREATE TABLE url_tracking_new (
            user_id TEXT PRIMARY KEY,
            url TEXT UNIQUE NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active',
            last_checked TEXT,
            error_count INTEGER DEFAULT 0,
            tweet_count INTEGER DEFAULT 0,
            type TEXT,
            added_at TEXT,
            last_scraped TEXT,
            last_error TEXT
        )
        """)
        
        # Get all records from the old table
        cursor.execute("SELECT * FROM url_tracking")
        rows = cursor.fetchall()
        
        # Get column names
        cursor.execute("PRAGMA table_info(url_tracking)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Insert records into the new table
        for row in rows:
            # Create a dictionary of column names and values
            record = dict(zip(columns, row))
            
            # Skip records without a user_id
            if not record.get('user_id'):
                logging.warning(f"Skipping record with URL {record.get('url')} because it has no user_id")
                continue
            
            # Check if the user_id already exists in the new table
            cursor.execute("SELECT COUNT(*) FROM url_tracking_new WHERE user_id = ?", (record.get('user_id'),))
            count = cursor.fetchone()[0]
            
            if count > 0:
                logging.warning(f"User ID {record.get('user_id')} already exists in the new table. Skipping URL {record.get('url')}")
                continue
            
            # Insert the record into the new table
            placeholders = ', '.join(['?'] * len(columns))
            columns_str = ', '.join(columns)
            
            cursor.execute(f"INSERT INTO url_tracking_new ({columns_str}) VALUES ({placeholders})", tuple(record.values()))
        
        # Drop the old table
        cursor.execute("DROP TABLE url_tracking")
        
        # Rename the new table
        cursor.execute("ALTER TABLE url_tracking_new RENAME TO url_tracking")
        
        # Create an index on the url column
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_url_tracking_url ON url_tracking (url)")
        
        # Commit the transaction
        conn.commit()
        
        logging.info("Changed primary key from url to user_id successfully")
        
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
    parser = argparse.ArgumentParser(description='Migrate the database to change the primary key from url to user_id')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the database')
    parser.add_argument('--no-backup', action='store_true', help='Do not create a backup of the database')
    
    args = parser.parse_args()
    
    migrate_database(args.db_path, backup=not args.no_backup)
