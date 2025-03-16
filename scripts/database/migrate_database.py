#!/usr/bin/env python3
"""
Migration script to update the database structure.

This script adds the url_tracking_id column to the kol_character table
and establishes relationships between existing records.
"""

import os
import sys
import logging
import sqlite3
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def migrate_database(db_path, test_mode=False):
    """Migrate the database to the new structure"""
    try:
        start_time = datetime.now()
        logging.info(f"Starting database migration at {start_time.isoformat()}")
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Check if tables exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kol_character'")
        kol_character_exists = cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='url_tracking'")
        url_tracking_exists = cursor.fetchone() is not None
        
        if not kol_character_exists:
            logging.error("kol_character table does not exist, cannot migrate")
            return False
        
        if not url_tracking_exists:
            logging.error("url_tracking table does not exist, cannot migrate")
            return False
        
        # Check if url_tracking_id column exists in kol_character
        cursor.execute("PRAGMA table_info(kol_character)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'url_tracking_id' not in columns:
            logging.info("Adding url_tracking_id column to kol_character table")
            
            if not test_mode:
                # Add url_tracking_id column
                cursor.execute("ALTER TABLE kol_character ADD COLUMN url_tracking_id INTEGER")
                
                # Create index on url_tracking_id
                cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_kol_character_url_tracking_id 
                ON kol_character (url_tracking_id)
                ''')
                
                conn.commit()
                logging.info("Added url_tracking_id column and index")
            else:
                logging.info("Test mode: Would add url_tracking_id column and index")
        else:
            logging.info("url_tracking_id column already exists in kol_character table")
        
        # Establish relationships between existing records
        logging.info("Establishing relationships between existing records")
        
        # Get all kol_character records
        cursor.execute("SELECT id, kol_id, kol_screen_name FROM kol_character WHERE url_tracking_id IS NULL")
        kol_records = cursor.fetchall()
        
        if not kol_records:
            logging.info("No kol_character records found that need updating")
            return True
        
        logging.info(f"Found {len(kol_records)} kol_character records to update")
        
        # Process each record
        updated_count = 0
        for kol_record in kol_records:
            kol_id = kol_record['kol_id']
            kol_screen_name = kol_record['kol_screen_name']
            
            # Try to find matching url_tracking record by user_id
            if kol_id:
                cursor.execute("SELECT id FROM url_tracking WHERE user_id = ?", (kol_id,))
                url_tracking_record = cursor.fetchone()
                
                if url_tracking_record:
                    url_tracking_id = url_tracking_record['id']
                    
                    if not test_mode:
                        cursor.execute(
                            "UPDATE kol_character SET url_tracking_id = ? WHERE id = ?",
                            (url_tracking_id, kol_record['id'])
                        )
                        updated_count += 1
                        logging.info(f"Updated kol_character record {kol_record['id']} with url_tracking_id {url_tracking_id} (matched by user_id)")
                    else:
                        logging.info(f"Test mode: Would update kol_character record {kol_record['id']} with url_tracking_id {url_tracking_id} (matched by user_id)")
                    continue
            
            # If no match by user_id, try by screen_name
            if kol_screen_name:
                cursor.execute("SELECT id FROM url_tracking WHERE screen_name = ?", (kol_screen_name,))
                url_tracking_record = cursor.fetchone()
                
                if url_tracking_record:
                    url_tracking_id = url_tracking_record['id']
                    
                    if not test_mode:
                        cursor.execute(
                            "UPDATE kol_character SET url_tracking_id = ? WHERE id = ?",
                            (url_tracking_id, kol_record['id'])
                        )
                        updated_count += 1
                        logging.info(f"Updated kol_character record {kol_record['id']} with url_tracking_id {url_tracking_id} (matched by screen_name)")
                    else:
                        logging.info(f"Test mode: Would update kol_character record {kol_record['id']} with url_tracking_id {url_tracking_id} (matched by screen_name)")
                    continue
            
            logging.warning(f"Could not find matching url_tracking record for kol_character record {kol_record['id']} (kol_id: {kol_id}, kol_screen_name: {kol_screen_name})")
        
        if not test_mode:
            conn.commit()
        
        # Create a view to help with debugging and analysis
        if not test_mode:
            try:
                cursor.execute('''
                CREATE VIEW IF NOT EXISTS kol_character_with_url AS
                SELECT 
                    k.id, k.kol_id, k.kol_screen_name, k.bio, k.lore, k.knowledge,
                    k.postExamples, k.topics, k.style_all, k.style_chat, k.style_post,
                    k.adjectives, k.url_tracking_id,
                    u.url, u.type, u.subtype, u.user_id, u.screen_name
                FROM 
                    kol_character k
                LEFT JOIN 
                    url_tracking u ON k.url_tracking_id = u.id
                ''')
                conn.commit()
                logging.info("Created kol_character_with_url view")
            except Exception as e:
                logging.error(f"Error creating view: {str(e)}")
        else:
            logging.info("Test mode: Would create kol_character_with_url view")
        
        # Close connection
        conn.close()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logging.info(f"Migration completed in {duration:.2f} seconds")
        if not test_mode:
            logging.info(f"Updated {updated_count} kol_character records with url_tracking_id")
        else:
            logging.info(f"Test mode: Would update {updated_count} kol_character records with url_tracking_id")
        
        return True
    
    except Exception as e:
        logging.error(f"Error migrating database: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Migrate database to new structure')
    parser.add_argument('--db-path', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db',
                        help='Path to SQLite database')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no actual changes)')
    
    args = parser.parse_args()
    
    # Migrate database
    success = migrate_database(args.db_path, args.test)
    
    if success:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
