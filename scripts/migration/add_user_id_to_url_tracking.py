#!/usr/bin/env python3
"""
Migration script to add user_id and subtype columns to the url_tracking table.
"""

import os
import sqlite3
import logging
import argparse
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Path to the SQLite database
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data/local_database.db')

def check_columns_exist(conn, table_name, columns):
    """Check if columns exist in the table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    missing_columns = []
    for column in columns:
        if column not in existing_columns:
            missing_columns.append(column)
    
    return missing_columns

def add_columns(conn, table_name, columns_with_types):
    """Add columns to the table"""
    cursor = conn.cursor()
    
    for column, column_type in columns_with_types.items():
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column} {column_type}")
            logging.info(f"Added column {column} ({column_type}) to {table_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                logging.warning(f"Column {column} already exists in {table_name}")
            else:
                logging.error(f"Error adding column {column} to {table_name}: {str(e)}")
                raise
    
    conn.commit()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Add user_id and subtype columns to the url_tracking table')
    parser.add_argument('--dry-run', action='store_true', help='Dry run - do not make any changes')
    
    args = parser.parse_args()
    
    print(f"Migration script to add columns to url_tracking table in {SQLITE_DB_PATH}")
    
    # Connect to the SQLite database
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        print("Connected to SQLite database")
    except sqlite3.Error as e:
        print(f"Error connecting to SQLite database: {str(e)}")
        sys.exit(1)
    
    # Columns to add with their types
    columns_with_types = {
        'user_id': 'TEXT',
        'subtype': 'TEXT'
    }
    
    # Check if columns already exist
    missing_columns = check_columns_exist(conn, 'url_tracking', columns_with_types.keys())
    
    if not missing_columns:
        print("All columns already exist in the url_tracking table")
        conn.close()
        return
    
    print(f"Missing columns: {', '.join(missing_columns)}")
    
    # Filter columns_with_types to only include missing columns
    missing_columns_with_types = {col: columns_with_types[col] for col in missing_columns}
    
    if args.dry_run:
        print("Dry run - would add the following columns:")
        for column, column_type in missing_columns_with_types.items():
            print(f"  {column} ({column_type})")
    else:
        print("Adding missing columns...")
        add_columns(conn, 'url_tracking', missing_columns_with_types)
        print("Migration completed successfully")
    
    conn.close()

if __name__ == "__main__":
    main()
