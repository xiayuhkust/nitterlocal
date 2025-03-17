#!/usr/bin/env python3
"""
Script to clear data from url_tracking and kol_character tables.
This script preserves the table structure but removes all records.
"""

import os
import sys
import logging
import sqlite3
import argparse
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def backup_database(db_path):
    """Create a backup of the database"""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        
        # Create a backup
        backup_conn = sqlite3.connect(backup_path)
        conn.backup(backup_conn)
        
        # Close connections
        backup_conn.close()
        conn.close()
        
        logging.info(f"Created database backup at {backup_path}")
        return backup_path
    except Exception as e:
        logging.error(f"Error creating database backup: {str(e)}")
        return None

def clear_tables(db_path):
    """Clear data from url_tracking and kol_character tables"""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get record counts before clearing
        cursor.execute("SELECT COUNT(*) FROM kol_character")
        kol_count_before = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM url_tracking")
        url_count_before = cursor.fetchone()[0]
        
        # Clear kol_character table first (due to foreign key constraint)
        cursor.execute("DELETE FROM kol_character")
        
        # Clear url_tracking table
        cursor.execute("DELETE FROM url_tracking")
        
        # Commit changes
        conn.commit()
        
        # Get record counts after clearing
        cursor.execute("SELECT COUNT(*) FROM kol_character")
        kol_count_after = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM url_tracking")
        url_count_after = cursor.fetchone()[0]
        
        # Close connection
        conn.close()
        
        logging.info(f"Cleared tables in {db_path}")
        logging.info(f"kol_character: {kol_count_before} records before, {kol_count_after} records after")
        logging.info(f"url_tracking: {url_count_before} records before, {url_count_after} records after")
        
        return True
    except Exception as e:
        logging.error(f"Error clearing tables: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Clear data from url_tracking and kol_character tables')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the SQLite database')
    parser.add_argument('--no-backup', action='store_true', help='Skip database backup')
    
    args = parser.parse_args()
    
    # Resolve database path
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', args.db_path))
    
    # Create database backup
    if not args.no_backup:
        backup_path = backup_database(db_path)
        if not backup_path:
            logging.warning("Failed to create database backup, proceeding without backup")
    
    # Clear tables
    if not clear_tables(db_path):
        logging.error("Failed to clear tables, exiting")
        return 1
    
    print(f"\nSuccessfully cleared all records from url_tracking and kol_character tables in {db_path}")
    print("The database structure is preserved, but all data has been removed.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
