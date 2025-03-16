#!/usr/bin/env python3
"""
Script to restore tables from their backup versions.
This script:
1. Restores url_tracking, tweets, and kol_character tables from their backup versions
2. Provides options to restore specific tables or all tables
3. Creates a backup of the current tables before restoring (optional)
"""

import os
import sys
import logging
import argparse
import sqlite3
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def get_db_connection(db_path):
    """Get a database connection"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def backup_table(conn, table_name):
    """
    Create a backup of a table before restoring
    
    Args:
        conn: Database connection
        table_name: Name of the table to backup
        
    Returns:
        str: Name of the backup table
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_table_name = f"{table_name}_restore_backup_{timestamp}"
    
    try:
        # Check if the table exists
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if cursor.fetchone() is None:
            logging.info(f"Table {table_name} does not exist, no backup needed")
            return None
        
        # Create backup table
        cursor.execute(f"CREATE TABLE {backup_table_name} AS SELECT * FROM {table_name}")
        conn.commit()
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {backup_table_name}")
        row_count = cursor.fetchone()[0]
        
        logging.info(f"Created backup of {table_name} as {backup_table_name} ({row_count} rows)")
        
        # Log the backup
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS backup_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT,
            backup_table_name TEXT,
            timestamp TEXT,
            row_count INTEGER,
            operation TEXT
        )
        """)
        
        cursor.execute("""
        INSERT INTO backup_log (table_name, backup_table_name, timestamp, row_count, operation)
        VALUES (?, ?, ?, ?, ?)
        """, (table_name, backup_table_name, datetime.now().isoformat(), row_count, "pre_restore_backup"))
        
        conn.commit()
        
        return backup_table_name
    except Exception as e:
        logging.error(f"Error backing up table {table_name}: {str(e)}")
        conn.rollback()
        return None

def restore_table(conn, table_name, backup_table_name, create_backup=True):
    """
    Restore a table from its backup version
    
    Args:
        conn: Database connection
        table_name: Name of the table to restore
        backup_table_name: Name of the backup table to restore from
        create_backup: Whether to create a backup of the current table before restoring
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        # Check if the backup table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{backup_table_name}'")
        if cursor.fetchone() is None:
            logging.error(f"Backup table {backup_table_name} does not exist")
            return False
        
        # Get row count of backup table
        cursor.execute(f"SELECT COUNT(*) FROM {backup_table_name}")
        backup_row_count = cursor.fetchone()[0]
        
        if backup_row_count == 0:
            logging.warning(f"Backup table {backup_table_name} is empty, skipping restore")
            return False
        
        # Create a backup of the current table if requested
        if create_backup:
            backup_table(conn, table_name)
        
        # Check if the table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if cursor.fetchone() is None:
            # Create the table with the same schema as the backup
            cursor.execute(f"CREATE TABLE {table_name} AS SELECT * FROM {backup_table_name} WHERE 0")
            logging.info(f"Created table {table_name} with schema from {backup_table_name}")
        
        # Get current row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        current_row_count = cursor.fetchone()[0]
        
        # Delete all rows from the current table
        cursor.execute(f"DELETE FROM {table_name}")
        
        # Copy data from backup table
        cursor.execute(f"INSERT INTO {table_name} SELECT * FROM {backup_table_name}")
        conn.commit()
        
        # Get new row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        new_row_count = cursor.fetchone()[0]
        
        logging.info(f"Restored {table_name} from {backup_table_name} (before: {current_row_count}, after: {new_row_count})")
        
        # Log the restore
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS backup_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT,
            backup_table_name TEXT,
            timestamp TEXT,
            row_count INTEGER,
            operation TEXT
        )
        """)
        
        cursor.execute("""
        INSERT INTO backup_log (table_name, backup_table_name, timestamp, row_count, operation)
        VALUES (?, ?, ?, ?, ?)
        """, (table_name, backup_table_name, datetime.now().isoformat(), new_row_count, "restore"))
        
        conn.commit()
        
        return True
    except Exception as e:
        logging.error(f"Error restoring table {table_name} from {backup_table_name}: {str(e)}")
        conn.rollback()
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Restore tables from their backup versions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Restore all tables
  python restore_from_backup.py
  
  # Restore specific tables
  python restore_from_backup.py --tables url_tracking,tweets
  
  # Restore without creating backups
  python restore_from_backup.py --no-backup
  
  # Use custom database path
  python restore_from_backup.py --db-path /path/to/database.db
"""
    )
    
    parser.add_argument(
        '--tables',
        type=str,
        default='url_tracking,tweets,kol_character',
        help='Comma-separated list of tables to restore (default: url_tracking,tweets,kol_character)'
    )
    
    parser.add_argument(
        '--db-path',
        type=str,
        default='data/local_database.db',
        help='Database path (default: data/local_database.db)'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not create backups of current tables before restoring'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Parse tables
    tables = [table.strip() for table in args.tables.split(',')]
    
    logging.info(f"Tables to restore: {tables}")
    
    # Connect to database
    try:
        conn = get_db_connection(args.db_path)
        
        # Restore each table
        for table in tables:
            backup_table_name = f"{table}_backup"
            restore_table(conn, table, backup_table_name, not args.no_backup)
        
        conn.close()
        
        logging.info("Restore completed successfully")
        
        return 0
    except Exception as e:
        logging.error(f"Error restoring tables: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
