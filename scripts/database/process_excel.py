#!/usr/bin/env python3
"""
Script to process Excel files with KOL character data and store in SQLite database.
This script adds a kol_character table to the SQLite database and processes Excel data.
"""

import os
import sys
import logging
import pandas as pd
import sqlite3
import argparse
from datetime import datetime
from urllib.parse import urlparse

# Add path to app directory to import Twitter utilities
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app'))
try:
    from twitter_utils import get_user_id_from_twitter_handle
except ImportError:
    logging.warning("Could not import twitter_utils, will use fallback method for user IDs")
    get_user_id_from_twitter_handle = None

# Import the centralized Twitter handle utility
try:
    from twitter_handle_utils import extract_twitter_handle
except ImportError:
    logging.warning("Could not import twitter_handle_utils, will use fallback method")
    
    def extract_twitter_handle(url):
        """Fallback Twitter handle extraction function"""
        if not url:
            return None
        
        try:
            # Parse the URL
            parsed_url = urlparse(url)
            
            # Check if it's a Twitter URL
            if 'twitter.com' in parsed_url.netloc:
                domain = 'twitter.com'
            elif 'x.com' in parsed_url.netloc:
                domain = 'x.com'
            else:
                return None
            
            # Extract the handle from the path
            path_parts = parsed_url.path.strip('/').split('/')
            if not path_parts:
                return None
            
            handle = path_parts[0]
            return handle.lower()
        except Exception as e:
            logging.error(f"Error extracting Twitter handle from {url}: {str(e)}")
            return None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_kol_character_table(db_path):
    """Create the kol_character table in SQLite database with foreign key constraint"""
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
        
        # Add foreign key constraint if url_tracking table exists
        if url_tracking_exists:
            try:
                # Check if url_tracking_id column exists
                cursor.execute("PRAGMA table_info(kol_character)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'url_tracking_id' in columns:
                    # Add index on url_tracking_id column
                    cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_kol_character_url_tracking_id ON kol_character (url_tracking_id)
                    ''')
                    
                    # Note: SQLite doesn't support ALTER TABLE ADD CONSTRAINT
                    # We would need to recreate the table to add a proper foreign key
                    # For now, we'll just add the index and handle the relationship in code
                    logging.info("Added index on url_tracking_id column")
                else:
                    logging.warning("url_tracking_id column not found in kol_character table")
            except Exception as e:
                logging.error(f"Error adding foreign key constraint: {str(e)}")
        
        conn.commit()
        conn.close()
        
        logging.info(f"Created kol_character table in {db_path}")
        return True
    except Exception as e:
        logging.error(f"Error creating kol_character table: {str(e)}")
        return False

def add_url_to_tracking(conn, url, type_val="kol", subtype="-", user_id=None):
    """Add a URL to the url_tracking table"""
    try:
        cursor = conn.cursor()
        
        # Extract Twitter handle
        handle = extract_twitter_handle(url)
        
        # Check if URL already exists
        cursor.execute("SELECT url FROM url_tracking WHERE url = ?", (url,))
        if cursor.fetchone():
            # Update existing URL
            cursor.execute(
                "UPDATE url_tracking SET type = ?, subtype = ?, user_id = ?, screen_name = ? WHERE url = ?",
                (type_val, subtype, user_id, handle, url)
            )
            logging.info(f"Updated URL in tracking: {url} with handle: {handle}")
            return True
        
        # Add new URL
        cursor.execute('''
        INSERT INTO url_tracking (
            url, type, subtype, user_id, screen_name
        ) VALUES (?, ?, ?, ?, ?)
        ''', (
            url,
            type_val,
            subtype,
            user_id,
            handle
        ))
        
        logging.info(f"Added URL to tracking: {url} with handle: {handle}")
        return True
    except Exception as e:
        logging.error(f"Error adding URL to tracking: {str(e)}")
        return False

def add_kol_character(conn, kol_data, url_tracking_id=None):
    """Add or update a KOL character record with url_tracking relationship"""
    try:
        cursor = conn.cursor()
        
        # Check if record already exists
        cursor.execute("SELECT id FROM kol_character WHERE kol_screen_name = ?", (kol_data['kol_screen_name'],))
        existing_id = cursor.fetchone()
        
        if existing_id:
            # Update existing record
            update_query = '''
            UPDATE kol_character SET
                kol_id = ?,
                bio = ?,
                lore = ?,
                knowledge = ?,
                postExamples = ?,
                topics = ?,
                style_all = ?,
                style_chat = ?,
                style_post = ?,
                adjectives = ?,
                url_tracking_id = ?
            WHERE kol_screen_name = ?
            '''
            
            cursor.execute(update_query, (
                kol_data['kol_id'],
                kol_data.get('bio', ''),
                kol_data.get('lore', ''),
                kol_data.get('knowledge', ''),
                kol_data.get('postExamples', ''),
                kol_data.get('topics', ''),
                kol_data.get('style_all', ''),
                kol_data.get('style_chat', ''),
                kol_data.get('style_post', ''),
                kol_data.get('adjectives', ''),
                url_tracking_id,
                kol_data['kol_screen_name']
            ))
            
            logging.info(f"Updated KOL character: {kol_data['kol_screen_name']}")
        else:
            # Insert new record
            insert_query = '''
            INSERT INTO kol_character (
                kol_id, kol_screen_name, bio, lore, knowledge, postExamples,
                topics, style_all, style_chat, style_post, adjectives, url_tracking_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            cursor.execute(insert_query, (
                kol_data['kol_id'],
                kol_data['kol_screen_name'],
                kol_data.get('bio', ''),
                kol_data.get('lore', ''),
                kol_data.get('knowledge', ''),
                kol_data.get('postExamples', ''),
                kol_data.get('topics', ''),
                kol_data.get('style_all', ''),
                kol_data.get('style_chat', ''),
                kol_data.get('style_post', ''),
                kol_data.get('adjectives', ''),
                url_tracking_id
            ))
            
            logging.info(f"Added new KOL character: {kol_data['kol_screen_name']}")
        
        return True
    except Exception as e:
        logging.error(f"Error adding KOL character: {str(e)}")
        return False

def process_excel_file(excel_path, db_path):
    """Process an Excel file with KOL character data"""
    try:
        # Read the Excel file
        df = pd.read_excel(excel_path)
        logging.info(f"Read Excel file: {excel_path}")
        
        # Create database connection
        conn = sqlite3.connect(db_path)
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Process each row
        processed_count = 0
        for _, row in df.iterrows():
            try:
                # Get Twitter URL
                url = row.get('Twitter url')
                if pd.isna(url) or not url:
                    logging.warning(f"Skipping row with no Twitter URL: {row}")
                    continue
                
                # Extract Twitter handle
                handle = extract_twitter_handle(url)
                if not handle:
                    logging.warning(f"Could not extract handle from URL: {url}")
                    continue
                
                # Try to get user_id using Twitter utility function
                user_id = None
                if get_user_id_from_twitter_handle:
                    try:
                        user_id = get_user_id_from_twitter_handle(handle)
                        logging.info(f"Got user_id {user_id} for handle {handle}")
                    except Exception as e:
                        logging.error(f"Error getting user_id for handle {handle}: {str(e)}")
                
                # Add URL to tracking with the user_id
                type_val = row.get('first category') if not pd.isna(row.get('first category')) else "kol"
                subtype = row.get('second_category') if not pd.isna(row.get('second_category')) else "-"
                add_url_to_tracking(conn, url, type_val, subtype, user_id)
                
                # Get url_tracking record ID and user_id
                cursor = conn.cursor()
                cursor.execute("SELECT id, user_id FROM url_tracking WHERE url = ?", (url,))
                result = cursor.fetchone()
                
                url_tracking_id = None
                if result:
                    url_tracking_id = result[0]
                    if result[1]:
                        user_id = result[1]
                
                # If user_id is not in url_tracking, try to get it from Twitter API
                if not user_id:
                    # Try to get user_id using Twitter utility function
                    if get_user_id_from_twitter_handle:
                        try:
                            numeric_id = get_user_id_from_twitter_handle(handle)
                            if numeric_id:
                                user_id = numeric_id
                                # Update url_tracking with the obtained user_id
                                cursor.execute(
                                    "UPDATE url_tracking SET user_id = ? WHERE url = ?",
                                    (user_id, url)
                                )
                                logging.info(f"Updated url_tracking with user_id {user_id} for URL {url}")
                            else:
                                user_id = handle
                        except Exception as e:
                            logging.error(f"Error getting user_id for handle {handle}: {str(e)}")
                            user_id = handle
                    else:
                        user_id = handle
                
                # Prepare KOL character data
                kol_data = {
                    'kol_id': user_id,
                    'kol_screen_name': handle,  # Remove @ prefix
                    'bio': str(row.get('bio', ''))[:255] if not pd.isna(row.get('bio')) else '',
                    'lore': str(row.get('lore', ''))[:255] if not pd.isna(row.get('lore')) else '',
                    'knowledge': str(row.get('knowledge', ''))[:255] if not pd.isna(row.get('knowledge')) else '',
                    'postExamples': str(row.get('postExamples', ''))[:255] if not pd.isna(row.get('postExamples')) else '',
                    'topics': str(row.get('topics', ''))[:255] if not pd.isna(row.get('topics')) else '',
                    'style_all': str(row.get('style_all', ''))[:255] if not pd.isna(row.get('style_all')) else '',
                    'style_chat': str(row.get('style_chat', ''))[:255] if not pd.isna(row.get('style_chat')) else '',
                    'style_post': str(row.get('style_post', ''))[:255] if not pd.isna(row.get('style_post')) else '',
                    'adjectives': str(row.get('adjectives', ''))[:255] if not pd.isna(row.get('adjectives')) else ''
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
    """Main function"""
    parser = argparse.ArgumentParser(description='Process Excel files with KOL character data')
    parser.add_argument('--excel', type=str, required=True, help='Path to the Excel file')
    parser.add_argument('--db-path', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db', help='Path to the SQLite database')
    
    args = parser.parse_args()
    
    # Create the kol_character table
    create_kol_character_table(args.db_path)
    
    # Process the Excel file
    process_excel_file(args.excel, args.db_path)

if __name__ == "__main__":
    main()
