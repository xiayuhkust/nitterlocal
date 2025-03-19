"""
Simplified Excel processor module for handling Excel files and updating SQLite database.
This module extracts only the necessary parts from the backend processing script.
"""

import os
import sys
import logging
import pandas as pd
import sqlite3
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_kol_character_table(db_path: str) -> bool:
    """Create the kol_character table in SQLite database"""
    try:
        # Ensure the database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Check if url_tracking table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='url_tracking'")
        url_tracking_exists = cursor.fetchone() is not None
        
        # Create the kol_character table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS kol_character (
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
            UNIQUE(kol_screen_name)
        )
        ''')
        
        # Create an index on the kol_screen_name column for faster lookups
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_kol_character_screen_name ON kol_character (kol_screen_name)
        ''')
        
        conn.commit()
        conn.close()
        
        logging.info(f"Created kol_character table in {db_path}")
        return True
    except Exception as e:
        logging.error(f"Error creating kol_character table: {str(e)}")
        return False

def add_url_to_tracking(conn: sqlite3.Connection, url: str, handle: str, type_val: str = "kol", subtype: str = "-") -> bool:
    """Add a URL to the url_tracking table"""
    try:
        cursor = conn.cursor()
        
        # Check if URL already exists
        cursor.execute("SELECT url FROM url_tracking WHERE url = ?", (url,))
        existing_url = cursor.fetchone()
        
        if existing_url:
            # Update existing URL
            cursor.execute(
                "UPDATE url_tracking SET type = ?, subtype = ?, screen_name = ? WHERE url = ?",
                (type_val, subtype, handle, existing_url[0])
            )
            logging.info(f"Updated URL in tracking: {url} with handle: {handle}")
            return True
        
        # Add new URL
        cursor.execute('''
        INSERT INTO url_tracking (
            url, type, subtype, screen_name
        ) VALUES (?, ?, ?, ?)
        ''', (
            url,
            type_val,
            subtype,
            handle
        ))
        
        logging.info(f"Added URL to tracking: {url} with handle: {handle}")
        return True
    except Exception as e:
        logging.error(f"Error adding URL to tracking: {str(e)}")
        return False

def add_kol_character(conn: sqlite3.Connection, kol_data: Dict[str, Any], url_tracking_id: Optional[Any] = None) -> bool:
    """Add or update a KOL character record with url_tracking relationship"""
    try:
        cursor = conn.cursor()
        
        # Check if KOL character already exists
        cursor.execute("SELECT rowid FROM kol_character WHERE kol_screen_name = ?", (kol_data['kol_screen_name'],))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing KOL character
            update_fields = []
            update_values = []
            
            for key, value in kol_data.items():
                if key != 'kol_screen_name':  # Don't update the primary key
                    update_fields.append(f"{key} = ?")
                    update_values.append(value)
            
            # Add url_tracking_id to update if provided
            if url_tracking_id is not None:
                update_fields.append("url_tracking_id = ?")
                update_values.append(url_tracking_id)
            
            update_values.append(kol_data['kol_screen_name'])  # For the WHERE clause
            
            cursor.execute(f'''
            UPDATE kol_character SET {', '.join(update_fields)} WHERE kol_screen_name = ?
            ''', update_values)
            
            logging.info(f"Updated KOL character: {kol_data['kol_screen_name']} with url_tracking_id: {url_tracking_id}")
        else:
            # Add new KOL character
            fields = list(kol_data.keys())
            placeholders = ['?'] * len(fields)
            values = list(kol_data.values())
            
            # Add url_tracking_id if provided
            if url_tracking_id is not None:
                fields.append('url_tracking_id')
                placeholders.append('?')
                values.append(url_tracking_id)
            
            cursor.execute(f'''
            INSERT INTO kol_character ({', '.join(fields)}) VALUES ({', '.join(placeholders)})
            ''', values)
            
            logging.info(f"Added new KOL character: {kol_data['kol_screen_name']} with url_tracking_id: {url_tracking_id}")
        
        conn.commit()
        return True
    
    except Exception as e:
        logging.error(f"Error adding KOL character: {str(e)}")
        return False

def extract_twitter_handle(url: str) -> Optional[str]:
    """Extract Twitter handle from URL"""
    try:
        if not url:
            return None
            
        # Remove trailing slashes
        url = url.rstrip('/')
        
        # Extract handle from URL
        if 'twitter.com' in url or 'x.com' in url:
            parts = url.split('/')
            if len(parts) >= 4:
                handle = parts[3]
                # Remove query parameters if any
                if '?' in handle:
                    handle = handle.split('?')[0]
                return handle
        
        return None
    except Exception as e:
        logging.error(f"Error extracting Twitter handle: {str(e)}")
        return None

def process_excel_file(excel_path: str, db_path: str) -> int:
    """Process an Excel file with KOL character data and update SQLite database"""
    try:
        # Read the Excel file
        df = pd.read_excel(excel_path)
        logging.info(f"Read Excel file: {excel_path}")
        
        # Create database connection
        conn = sqlite3.connect(db_path)
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Ensure kol_character table exists
        create_kol_character_table(db_path)
        
        # Check if url_tracking table exists and create it if needed
        cursor = conn.cursor()
        
        # Check if url_tracking table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='url_tracking'")
        if cursor.fetchone() is None:
            # Create url_tracking table with required columns
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS url_tracking (
                url TEXT PRIMARY KEY,
                user_id TEXT,
                description TEXT,
                status TEXT DEFAULT 'active',
                last_checked TEXT,
                error_count INTEGER DEFAULT 0,
                tweet_count INTEGER DEFAULT 0,
                type TEXT,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_scraped TEXT,
                last_error TEXT,
                subtype TEXT,
                screen_name TEXT,
                kol_name TEXT
            )
            ''')
            conn.commit()
            logging.info("Created url_tracking table with required columns")
        
        # Process each row
        processed_count = 0
        for _, row in enumerate(df.iterrows()):
            try:
                # Get Twitter URL
                url = row[1].get('Twitter url')
                if pd.isna(url) or not url:
                    logging.warning(f"Skipping row with no Twitter URL: {row}")
                    continue
                
                # Extract Twitter handle
                handle = extract_twitter_handle(url)
                if not handle:
                    logging.warning(f"Could not extract handle from URL: {url}")
                    continue
                
                # Add URL to tracking
                type_val = str(row[1].get('first category')) if not pd.isna(row[1].get('first category')) else "kol"
                subtype = str(row[1].get('second_category')) if not pd.isna(row[1].get('second_category')) else "-"
                add_url_to_tracking(conn, url, handle, type_val, subtype)
                
                # Get url_tracking record ID
                cursor = conn.cursor()
                
                # Check if id column exists in url_tracking table
                cursor.execute("PRAGMA table_info(url_tracking)")
                columns = [row[1] for row in cursor.fetchall()]
                
                url_tracking_id = None
                if 'id' in columns:
                    cursor.execute("SELECT id FROM url_tracking WHERE url = ?", (url,))
                    result = cursor.fetchone()
                    
                    if result:
                        url_tracking_id = result[0]
                else:
                    # If id column doesn't exist, use url as the identifier
                    cursor.execute("SELECT url FROM url_tracking WHERE url = ?", (url,))
                    result = cursor.fetchone()
                    
                    if result:
                        url_tracking_id = result[0]  # Use URL as the ID
                
                # Prepare KOL character data
                kol_data = {
                    'kol_id': handle,  # Use handle as kol_id instead of user_id from Twitter API
                    'kol_screen_name': handle,
                    'bio': str(row[1].get('bio', ''))[:255] if not pd.isna(row[1].get('bio')) else '',
                    'lore': str(row[1].get('lore', ''))[:255] if not pd.isna(row[1].get('lore')) else '',
                    'knowledge': str(row[1].get('knowledge', ''))[:255] if not pd.isna(row[1].get('knowledge')) else '',
                    'postExamples': str(row[1].get('postExamples', '')) if not pd.isna(row[1].get('postExamples')) else '',
                    'topics': str(row[1].get('topics', ''))[:255] if not pd.isna(row[1].get('topics')) else '',
                    'style_all': str(row[1].get('style_all', ''))[:255] if not pd.isna(row[1].get('style_all')) else '',
                    'style_chat': str(row[1].get('style_chat', ''))[:255] if not pd.isna(row[1].get('style_chat')) else '',
                    'style_post': str(row[1].get('style_post', ''))[:255] if not pd.isna(row[1].get('style_post')) else '',
                    'adjectives': str(row[1].get('adjectives', ''))[:255] if not pd.isna(row[1].get('adjectives')) else ''
                }
                
                # Add KOL character with url_tracking relationship
                add_kol_character(conn, kol_data, url_tracking_id)
                
                processed_count += 1
                
            except Exception as e:
                logging.error(f"Error processing row: {str(e)}")
                continue
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logging.info(f"Processed {processed_count} rows from Excel file")
        return processed_count
    except Exception as e:
        logging.error(f"Error processing Excel file: {str(e)}")
        return 0

def main():
    """Main function for standalone usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process Excel files with KOL character data')
    parser.add_argument('--excel', type=str, required=True, help='Path to the Excel file')
    parser.add_argument('--db-path', type=str, default=os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/local_database.db')), help='Path to the SQLite database')
    
    args = parser.parse_args()
    
    # Process the Excel file
    process_excel_file(args.excel, args.db_path)

if __name__ == "__main__":
    main()
