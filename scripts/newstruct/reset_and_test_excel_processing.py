#!/usr/bin/env python3
"""
Script to reset the database and test Excel processing from scratch.
This script demonstrates the complete workflow from Excel processing to database storage,
focusing on tweet_count data.
"""

import os
import sys
import logging
import sqlite3
import pandas as pd
import tempfile
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

def reset_database(db_path):
    """Reset the database by dropping and recreating tables"""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Drop url_tracking and kol_character tables
        cursor.execute("DROP TABLE IF EXISTS kol_character")
        cursor.execute("DROP TABLE IF EXISTS url_tracking")
        
        # Create url_tracking table
        cursor.execute('''
        CREATE TABLE url_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            user_id TEXT,
            description TEXT,
            status TEXT DEFAULT 'active',
            last_checked TIMESTAMP,
            error_count INTEGER DEFAULT 0,
            tweet_count INTEGER DEFAULT 0,
            type TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_scraped TIMESTAMP,
            last_error TEXT,
            subtype TEXT DEFAULT '-',
            screen_name TEXT,
            followers_count INTEGER,
            following_count INTEGER,
            profile_image_url TEXT,
            profile_banner_url TEXT,
            verified INTEGER,
            location TEXT,
            created_at TEXT,
            profile_updated_at TIMESTAMP
        )
        ''')
        
        # Create kol_character table
        cursor.execute('''
        CREATE TABLE kol_character (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kol_id TEXT,
            kol_screen_name TEXT NOT NULL,
            bio TEXT,
            lore TEXT,
            knowledge TEXT,
            postExamples TEXT,
            topics TEXT,
            style_all TEXT,
            style_chat TEXT,
            style_post TEXT,
            adjectives TEXT,
            url_tracking_id INTEGER,
            FOREIGN KEY (url_tracking_id) REFERENCES url_tracking(id)
        )
        ''')
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_url_tracking_screen_name ON url_tracking(screen_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_url_tracking_user_id ON url_tracking(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kol_character_screen_name ON kol_character(kol_screen_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kol_character_url_tracking_id ON kol_character(url_tracking_id)")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logging.info(f"Reset database at {db_path}")
        return True
    except Exception as e:
        logging.error(f"Error resetting database: {str(e)}")
        return False

def create_test_excel(output_path=None):
    """Create a test Excel file with Twitter profile data"""
    logging.info("Creating test Excel file")
    
    # Create a DataFrame with cz_binance data
    data = {
        'Twitter url': ['https://twitter.com/cz_binance'],
        'first category': ['KOL'],
        'second_category': ['-'],
        'bio': ['Founder of Binance, crypto exchange leader'],
        'lore': ['Born in China, started crypto in 2013, founded Binance in 2017']
    }
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(data)
    
    # Create a temporary file for the Excel if no output path is provided
    if not output_path:
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            output_path = temp_file.name
    
    df.to_excel(output_path, index=False)
    
    logging.info(f"Created test Excel file at {output_path}")
    return output_path

def process_excel_file(excel_path, db_path):
    """Process an Excel file with KOL character data"""
    logging.info(f"Processing Excel file: {excel_path}")
    
    try:
        # Import the process_excel_with_profile function
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
        from process_excel_with_profile import process_excel_file as process_excel
        
        # Process the Excel file
        process_excel(excel_path, db_path)
        
        logging.info(f"Processed Excel file: {excel_path}")
        return True
    except Exception as e:
        logging.error(f"Error processing Excel file: {str(e)}")
        return False

def display_results(db_path, handle):
    """Display the results of Excel processing for a specific handle"""
    logging.info(f"Displaying results for handle: {handle}")
    
    try:
        # Import the display_url_tracking_record function
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
        from display_url_tracking_record import display_joined_record
        
        # Display the results
        display_joined_record(db_path, handle)
        
        return True
    except Exception as e:
        logging.error(f"Error displaying results: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Reset database and test Excel processing from scratch')
    parser.add_argument('--db-path', type=str, default='data/test_database.db', help='Path to the SQLite database')
    parser.add_argument('--excel-path', type=str, help='Path to the Excel file (will be created if not provided)')
    parser.add_argument('--handle', type=str, default='cz_binance', help='Twitter handle to check')
    parser.add_argument('--no-backup', action='store_true', help='Skip database backup')
    parser.add_argument('--no-reset', action='store_true', help='Skip database reset')
    
    args = parser.parse_args()
    
    # Resolve database path
    db_path = os.path.abspath(args.db_path)
    
    # Create database backup
    if not args.no_backup:
        backup_path = backup_database(db_path)
        if not backup_path:
            logging.warning("Failed to create database backup, proceeding without backup")
    
    # Reset database
    if not args.no_reset:
        if not reset_database(db_path):
            logging.error("Failed to reset database, exiting")
            return 1
    
    # Create test Excel file
    excel_path = args.excel_path
    if not excel_path:
        excel_path = create_test_excel()
    
    # Process Excel file
    if not process_excel_file(excel_path, db_path):
        logging.error("Failed to process Excel file, exiting")
        return 1
    
    # Display results
    if not display_results(db_path, args.handle):
        logging.error("Failed to display results, exiting")
        return 1
    
    # Clean up
    if not args.excel_path and os.path.exists(excel_path):
        os.remove(excel_path)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
