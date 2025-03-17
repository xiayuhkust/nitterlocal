#!/usr/bin/env python3
"""
Script to clear all data from url_tracking and kol_character tables
while preserving the table structure.
"""

import os
import sys
import sqlite3
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def clear_tables(db_path, backup=True):
    """Clear all data from url_tracking and kol_character tables"""
    if not os.path.exists(db_path):
        logging.error(f"Database file not found: {db_path}")
        return False
    
    # Create backup if requested
    if backup:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_path = f"{db_path}.backup_{timestamp}"
        try:
            import shutil
            shutil.copy2(db_path, backup_path)
            logging.info(f"Created database backup at {backup_path}")
        except Exception as e:
            logging.error(f"Failed to create backup: {e}")
            return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Begin transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Delete all data from tables
        logging.info("Deleting all data from kol_character table...")
        cursor.execute("DELETE FROM kol_character")
        
        logging.info("Deleting all data from url_tracking table...")
        cursor.execute("DELETE FROM url_tracking")
        
        # Reset SQLite sequence for autoincrement
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='kol_character'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='url_tracking'")
        
        # Commit transaction
        cursor.execute("COMMIT")
        
        logging.info(f"Deleted {cursor.rowcount} rows from tables")
        
    except Exception as e:
        # Rollback transaction in case of error
        cursor.execute("ROLLBACK")
        logging.error(f"Error clearing tables: {e}")
        conn.close()
        return False
    
    conn.close()
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Clear data from url_tracking and kol_character tables")
    parser.add_argument("--db-path", default="data/local_database.db", help="Path to the SQLite database")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating a backup before clearing")
    
    args = parser.parse_args()
    
    if clear_tables(args.db_path, not args.no_backup):
        logging.info(f"Successfully cleared data from tables in {args.db_path}")
        logging.info("\nTo verify the tables were cleared, run:")
        logging.info(f"sqlite3 {args.db_path} 'SELECT COUNT(*) FROM url_tracking; SELECT COUNT(*) FROM kol_character;'")
        return 0
    else:
        logging.error(f"Failed to clear data from tables in {args.db_path}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
