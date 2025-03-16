#!/usr/bin/env python3
"""
Script to fix kol_id in kol_character table to match user_id in url_tracking table.
This script:
1. Identifies mismatches between kol_id in kol_character and user_id in url_tracking
2. Updates kol_character.kol_id to match url_tracking.user_id
3. Provides options to preview changes before applying them
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
    Create a backup of a table before fixing
    
    Args:
        conn: Database connection
        table_name: Name of the table to backup
        
    Returns:
        str: Name of the backup table
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_table_name = f"{table_name}_fix_backup_{timestamp}"
    
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
        """, (table_name, backup_table_name, datetime.now().isoformat(), row_count, "pre_fix_backup"))
        
        conn.commit()
        
        return backup_table_name
    except Exception as e:
        logging.error(f"Error backing up table {table_name}: {str(e)}")
        conn.rollback()
        return None

def find_mismatches(conn):
    """
    Find mismatches between kol_id in kol_character and user_id in url_tracking
    
    Args:
        conn: Database connection
        
    Returns:
        list: List of mismatches
    """
    try:
        cursor = conn.cursor()
        
        # Check if both tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kol_character'")
        if cursor.fetchone() is None:
            logging.error("Table kol_character does not exist")
            return []
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='url_tracking'")
        if cursor.fetchone() is None:
            logging.error("Table url_tracking does not exist")
            return []
        
        # Find mismatches
        cursor.execute("""
        SELECT 
            k.kol_id AS kol_character_id,
            u.user_id AS url_tracking_id,
            k.kol_screen_name,
            u.screen_name,
            u.url
        FROM kol_character k
        JOIN url_tracking u ON k.kol_screen_name = u.screen_name
        WHERE k.kol_id != u.user_id
        """)
        
        mismatches = [dict(row) for row in cursor.fetchall()]
        
        logging.info(f"Found {len(mismatches)} mismatches between kol_character.kol_id and url_tracking.user_id")
        
        return mismatches
    except Exception as e:
        logging.error(f"Error finding mismatches: {str(e)}")
        return []

def fix_mismatches(conn, mismatches, dry_run=True):
    """
    Fix mismatches between kol_id in kol_character and user_id in url_tracking
    
    Args:
        conn: Database connection
        mismatches: List of mismatches
        dry_run: Whether to preview changes without applying them
        
    Returns:
        int: Number of rows updated
    """
    if not mismatches:
        logging.info("No mismatches to fix")
        return 0
    
    try:
        cursor = conn.cursor()
        
        # Create a backup of kol_character table
        if not dry_run:
            backup_table(conn, 'kol_character')
        
        # Update each mismatch
        updated_count = 0
        for mismatch in mismatches:
            kol_character_id = mismatch['kol_character_id']
            url_tracking_id = mismatch['url_tracking_id']
            kol_screen_name = mismatch['kol_screen_name']
            
            logging.info(f"{'Would update' if dry_run else 'Updating'} kol_id for {kol_screen_name}: {kol_character_id} -> {url_tracking_id}")
            
            if not dry_run:
                cursor.execute("""
                UPDATE kol_character
                SET kol_id = ?
                WHERE kol_screen_name = ?
                """, (url_tracking_id, kol_screen_name))
                
                updated_count += cursor.rowcount
        
        if not dry_run:
            conn.commit()
            logging.info(f"Updated {updated_count} rows in kol_character table")
        else:
            logging.info(f"Would update {len(mismatches)} rows in kol_character table (dry run)")
        
        return len(mismatches)
    except Exception as e:
        logging.error(f"Error fixing mismatches: {str(e)}")
        if not dry_run:
            conn.rollback()
        return 0

def check_missing_screen_names(conn):
    """
    Check for screen_names in url_tracking that are missing in kol_character
    
    Args:
        conn: Database connection
        
    Returns:
        list: List of missing screen_names
    """
    try:
        cursor = conn.cursor()
        
        # Find missing screen_names
        cursor.execute("""
        SELECT 
            u.screen_name,
            u.user_id,
            u.url,
            u.status
        FROM url_tracking u
        LEFT JOIN kol_character k ON u.screen_name = k.kol_screen_name
        WHERE k.kol_screen_name IS NULL
        AND u.screen_name IS NOT NULL
        """)
        
        missing = [dict(row) for row in cursor.fetchall()]
        
        logging.info(f"Found {len(missing)} screen_names in url_tracking that are missing in kol_character")
        
        return missing
    except Exception as e:
        logging.error(f"Error checking missing screen_names: {str(e)}")
        return []

def add_missing_screen_names(conn, missing, dry_run=True):
    """
    Add missing screen_names to kol_character table
    
    Args:
        conn: Database connection
        missing: List of missing screen_names
        dry_run: Whether to preview changes without applying them
        
    Returns:
        int: Number of rows added
    """
    if not missing:
        logging.info("No missing screen_names to add")
        return 0
    
    try:
        cursor = conn.cursor()
        
        # Create a backup of kol_character table
        if not dry_run:
            backup_table(conn, 'kol_character')
        
        # Add each missing screen_name
        added_count = 0
        for item in missing:
            screen_name = item['screen_name']
            user_id = item['user_id']
            
            logging.info(f"{'Would add' if dry_run else 'Adding'} {screen_name} to kol_character with kol_id {user_id}")
            
            if not dry_run:
                cursor.execute("""
                INSERT INTO kol_character (kol_screen_name, kol_id)
                VALUES (?, ?)
                """, (screen_name, user_id))
                
                added_count += cursor.rowcount
        
        if not dry_run:
            conn.commit()
            logging.info(f"Added {added_count} rows to kol_character table")
        else:
            logging.info(f"Would add {len(missing)} rows to kol_character table (dry run)")
        
        return len(missing)
    except Exception as e:
        logging.error(f"Error adding missing screen_names: {str(e)}")
        if not dry_run:
            conn.rollback()
        return 0

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Fix kol_id in kol_character table to match user_id in url_tracking table',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes without applying them
  python fix_kol_id.py
  
  # Apply changes
  python fix_kol_id.py --apply
  
  # Add missing screen_names
  python fix_kol_id.py --apply --add-missing
  
  # Use custom database path
  python fix_kol_id.py --db-path /path/to/database.db
"""
    )
    
    parser.add_argument(
        '--db-path',
        type=str,
        default='data/local_database.db',
        help='Database path (default: data/local_database.db)'
    )
    
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Apply changes (default is dry run)'
    )
    
    parser.add_argument(
        '--add-missing',
        action='store_true',
        help='Add missing screen_names to kol_character table'
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
    
    # Connect to database
    try:
        conn = get_db_connection(args.db_path)
        
        # Find mismatches
        mismatches = find_mismatches(conn)
        
        # Fix mismatches
        fix_mismatches(conn, mismatches, not args.apply)
        
        # Check for missing screen_names
        if args.add_missing:
            missing = check_missing_screen_names(conn)
            add_missing_screen_names(conn, missing, not args.apply)
        
        conn.close()
        
        if args.apply:
            logging.info("Fix completed successfully")
        else:
            logging.info("Dry run completed successfully")
        
        return 0
    except Exception as e:
        logging.error(f"Error fixing kol_id: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
