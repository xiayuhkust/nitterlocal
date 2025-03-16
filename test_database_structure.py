#!/usr/bin/env python3
"""
Test script to verify the database structure.
"""

import os
import sys
import logging
import sqlite3
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_database_structure(db_path):
    """Check the database structure"""
    try:
        # Check if the database file exists
        if not os.path.exists(db_path):
            logging.error(f"Database file {db_path} does not exist")
            return False
        
        # Connect to the database
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
            
            # Check if screen_name column exists
            screen_name_exists = any(col[1] == 'screen_name' for col in columns)
            if not screen_name_exists:
                logging.error("screen_name column does not exist in url_tracking table")
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
            logging.warning("kol_character_with_url view does not exist")
        
        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        logging.info(f"Indexes in database: {', '.join(indexes)}")
        
        # Check if required indexes exist
        required_indexes = [
            'idx_url_tracking_user_id',
            'idx_url_tracking_screen_name',
            'idx_kol_character_url_tracking_id'
        ]
        
        for idx in required_indexes:
            if idx not in indexes:
                logging.warning(f"Index {idx} does not exist")
        
        # Check sample data if available
        try:
            cursor.execute("SELECT COUNT(*) FROM url_tracking")
            url_tracking_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM kol_character")
            kol_character_count = cursor.fetchone()[0]
            
            logging.info(f"url_tracking record count: {url_tracking_count}")
            logging.info(f"kol_character record count: {kol_character_count}")
            
            if url_tracking_count > 0:
                cursor.execute("SELECT id, url, user_id, screen_name FROM url_tracking LIMIT 3")
                samples = cursor.fetchall()
                logging.info("Sample url_tracking records:")
                for sample in samples:
                    logging.info(f"  id={sample[0]}, url={sample[1]}, user_id={sample[2]}, screen_name={sample[3]}")
            
            if kol_character_count > 0:
                cursor.execute("SELECT id, kol_id, kol_screen_name, url_tracking_id FROM kol_character LIMIT 3")
                samples = cursor.fetchall()
                logging.info("Sample kol_character records:")
                for sample in samples:
                    logging.info(f"  id={sample[0]}, kol_id={sample[1]}, kol_screen_name={sample[2]}, url_tracking_id={sample[3]}")
        except Exception as e:
            logging.warning(f"Error checking sample data: {str(e)}")
        
        # Close connection
        conn.close()
        
        logging.info("Database structure verification completed successfully")
        return True
    
    except Exception as e:
        logging.error(f"Error checking database structure: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Verify database structure')
    parser.add_argument('--db-path', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db',
                        help='Path to SQLite database')
    
    args = parser.parse_args()
    
    # Check database structure
    success = check_database_structure(args.db_path)
    
    if success:
        logging.info("Database structure is correct")
        return 0
    else:
        logging.error("Database structure verification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
