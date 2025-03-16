#!/usr/bin/env python3
"""
Test script to reset the database structure and verify it.
"""

import os
import sys
import logging
import sqlite3
import subprocess
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def reset_database(db_path, reset_sql_path, sample_data_sql_path=None):
    """Reset the database structure and optionally add sample data"""
    try:
        # Check if the database file exists
        if not os.path.exists(db_path):
            logging.info(f"Database file {db_path} does not exist, creating it")
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Create an empty database file
            conn = sqlite3.connect(db_path)
            conn.close()
        
        # Reset the database structure
        logging.info(f"Resetting database structure using {reset_sql_path}")
        result = subprocess.run(
            f"sqlite3 {db_path} < {reset_sql_path}",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logging.error(f"Error resetting database structure: {result.stderr}")
            return False
        
        logging.info("Database structure reset successfully")
        
        # Add sample data if provided
        if sample_data_sql_path:
            logging.info(f"Adding sample data using {sample_data_sql_path}")
            result = subprocess.run(
                f"sqlite3 {db_path} < {sample_data_sql_path}",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logging.error(f"Error adding sample data: {result.stderr}")
                return False
            
            logging.info("Sample data added successfully")
        
        # Verify the database structure
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' OR type='view'")
        tables = [row[0] for row in cursor.fetchall()]
        
        logging.info(f"Tables and views in database: {', '.join(tables)}")
        
        # Check url_tracking structure
        if 'url_tracking' in tables:
            cursor.execute("PRAGMA table_info(url_tracking)")
            columns = cursor.fetchall()
            
            logging.info("url_tracking table structure:")
            for col in columns:
                logging.info(f"  {col[0]}: {col[1]} ({col[2]}), {'PRIMARY KEY' if col[5] else ''}")
            
            # Check if id column is primary key
            id_is_primary = any(col[1] == 'id' and col[5] for col in columns)
            if not id_is_primary:
                logging.error("id column is not primary key in url_tracking table")
                return False
            
            logging.info("url_tracking table structure is correct")
        else:
            logging.error("url_tracking table does not exist")
            return False
        
        # Check kol_character structure
        if 'kol_character' in tables:
            cursor.execute("PRAGMA table_info(kol_character)")
            columns = cursor.fetchall()
            
            logging.info("kol_character table structure:")
            for col in columns:
                logging.info(f"  {col[0]}: {col[1]} ({col[2]}), {'PRIMARY KEY' if col[5] else ''}")
            
            # Check if url_tracking_id column exists
            url_tracking_id_exists = any(col[1] == 'url_tracking_id' for col in columns)
            if not url_tracking_id_exists:
                logging.error("url_tracking_id column does not exist in kol_character table")
                return False
            
            logging.info("kol_character table structure is correct")
        else:
            logging.error("kol_character table does not exist")
            return False
        
        # Check view
        if 'kol_character_with_url' in tables:
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='view' AND name='kol_character_with_url'")
            view_sql = cursor.fetchone()[0]
            
            logging.info(f"kol_character_with_url view SQL: {view_sql}")
            logging.info("kol_character_with_url view exists")
        else:
            logging.error("kol_character_with_url view does not exist")
            return False
        
        # Check sample data if provided
        if sample_data_sql_path:
            cursor.execute("SELECT COUNT(*) FROM url_tracking")
            url_tracking_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM kol_character")
            kol_character_count = cursor.fetchone()[0]
            
            logging.info(f"url_tracking record count: {url_tracking_count}")
            logging.info(f"kol_character record count: {kol_character_count}")
            
            if url_tracking_count == 0 or kol_character_count == 0:
                logging.error("Sample data was not added correctly")
                return False
            
            logging.info("Sample data verified successfully")
        
        conn.close()
        return True
    
    except Exception as e:
        logging.error(f"Error resetting database: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Reset database structure and verify it')
    parser.add_argument('--db-path', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db',
                        help='Path to SQLite database')
    parser.add_argument('--reset-sql', type=str, default='/home/ubuntu/nitterlocal/reset_database.sql',
                        help='Path to reset SQL file')
    parser.add_argument('--sample-data-sql', type=str, default='/home/ubuntu/nitterlocal/create_sample_data.sql',
                        help='Path to sample data SQL file')
    parser.add_argument('--no-sample-data', action='store_true',
                        help='Do not add sample data')
    
    args = parser.parse_args()
    
    # Reset database
    sample_data_sql_path = None if args.no_sample_data else args.sample_data_sql
    success = reset_database(args.db_path, args.reset_sql, sample_data_sql_path)
    
    if success:
        logging.info("Database reset and verification completed successfully")
        return 0
    else:
        logging.error("Database reset and verification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
