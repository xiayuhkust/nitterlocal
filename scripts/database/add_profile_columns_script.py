#!/usr/bin/env python3
"""
Script to add profile-related columns to url_tracking table in SQLite database.
This script can be run on the user's local machine to add the necessary columns.
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def add_profile_columns(db_path):
    """Add profile-related columns to url_tracking table"""
    if not os.path.exists(db_path):
        logging.error(f"Database file not found: {db_path}")
        return False
    
    # Create a backup before modifying the database
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    try:
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        logging.info(f"Created database backup at {backup_path}")
    except Exception as e:
        logging.error(f"Failed to create backup: {e}")
        return False
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(url_tracking)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    # Define columns to add with their types and defaults
    columns_to_add = {
        'followers_count': 'INTEGER DEFAULT 0',
        'following_count': 'INTEGER DEFAULT 0',
        'profile_image_url': 'TEXT',
        'profile_banner_url': 'TEXT',
        'verified': 'INTEGER DEFAULT 0',
        'location': 'TEXT',
        'created_at': 'TEXT',
        'profile_updated_at': 'TEXT'
    }
    
    # Add columns if they don't exist
    for column, definition in columns_to_add.items():
        if column not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE url_tracking ADD COLUMN {column} {definition}")
                logging.info(f"Added column {column} to url_tracking table")
            except sqlite3.OperationalError as e:
                logging.warning(f"Could not add column {column}: {e}")
        else:
            logging.info(f"Column {column} already exists")
    
    # Commit changes and close connection
    conn.commit()
    
    # Display updated schema
    cursor.execute("PRAGMA table_info(url_tracking)")
    columns = cursor.fetchall()
    
    logging.info("\n=== Updated Schema for table 'url_tracking' ===")
    logging.info("ID    Name                 Type            NotNull  Default         PK")
    logging.info("----------------------------------------------------------------------")
    for col in columns:
        col_id, name, type_, not_null, default, pk = col
        logging.info(f"{col_id:<5} {name:<20} {type_:<15} {not_null:<8} {str(default):<15} {pk}")
    
    conn.close()
    return True

if __name__ == "__main__":
    # Get database path from command line argument or use default
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = "data/local_database.db"
    
    add_profile_columns(db_path)
