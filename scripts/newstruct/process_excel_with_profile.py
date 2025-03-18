#!/usr/bin/env python3
"""
Integrated script to process Excel data using both scraper and profile methods,
outputting updated url_tracking and kol_character tables.
"""

import os
import sys
import logging
import argparse
import pandas as pd
import sqlite3
import json
import tempfile
import subprocess
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import required modules
try:
    from app.twitter_api_utils import (
        extract_twitter_handle,
        get_user_id_from_twitter_api,
        get_user_id_from_direct_client_call
    )
    from scripts.profile.update_profile_data import ProfileUpdater
    
    # Import URL normalization function
    try:
        from scripts.utils.url_utils import normalize_twitter_url
    except ImportError:
        # Fallback implementation if url_utils is not available
        def normalize_twitter_url(url):
            """
            Normalize Twitter URL to ensure it uses twitter.com domain.
            Converts x.com and nitter.net URLs to twitter.com format.
            """
            if not url:
                return None
            
            try:
                # Check if it's a Twitter, X, or Nitter URL
                if 'twitter.com' in url:
                    return url
                elif 'x.com' in url:
                    return url.replace('x.com', 'twitter.com')
                elif 'nitter.net' in url:
                    return url.replace('nitter.net', 'twitter.com')
                else:
                    return url
            except Exception as e:
                logging.error(f"Error normalizing Twitter URL {url}: {str(e)}")
                return url
    
    logging.info("Successfully imported required modules")
except ImportError as e:
    logging.error(f"Could not import required modules: {str(e)}")
    sys.exit(1)

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
        
        # Normalize the URL to ensure x.com is converted to twitter.com
        normalized_url = normalize_twitter_url(url)
        if normalized_url is None:
            logging.error(f"Failed to normalize URL: {url}")
            return False
        
        # Extract Twitter handle from normalized URL
        handle = extract_twitter_handle(normalized_url)
        
        # Check if URL already exists (either original or normalized)
        cursor.execute("SELECT url FROM url_tracking WHERE url = ? OR url = ?", (url, normalized_url))
        existing_url = cursor.fetchone()
        
        if existing_url:
            # Update existing URL
            cursor.execute(
                "UPDATE url_tracking SET url = ?, type = ?, subtype = ?, user_id = ?, screen_name = ? WHERE url = ?",
                (normalized_url, type_val, subtype, user_id, handle, existing_url[0])
            )
            logging.info(f"Updated URL in tracking: {url} -> {normalized_url} with handle: {handle}")
            return True
        
        # Add new URL (always use normalized URL)
        cursor.execute('''
        INSERT INTO url_tracking (
            url, type, subtype, user_id, screen_name
        ) VALUES (?, ?, ?, ?, ?)
        ''', (
            normalized_url,
            type_val,
            subtype,
            user_id,
            handle
        ))
        
        if url != normalized_url:
            logging.info(f"Normalized URL for storage: {url} -> {normalized_url}")
        
        logging.info(f"Added URL to tracking: {normalized_url} with handle: {handle}")
        return True
    except Exception as e:
        logging.error(f"Error adding URL to tracking: {str(e)}")
        return False

def add_kol_character(conn, kol_data, url_tracking_id=None):
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

def process_excel_file(excel_path, db_path):
    """Process an Excel file with KOL character data using both scraper and profile methods"""
    try:
        # Read the Excel file
        df = pd.read_excel(excel_path)
        logging.info(f"Read Excel file: {excel_path}")
        
        # Create database connection
        conn = sqlite3.connect(db_path)
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Create profile updater
        profile_updater = ProfileUpdater(db_path=db_path)
        
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
                
                # Try to get user_id using Twitter API
                try:
                    # First try direct client call (most reliable method)
                    user_id = get_user_id_from_direct_client_call(handle)
                    if user_id:
                        logging.info(f"Got user_id {user_id} for handle {handle} from direct client call")
                    else:
                        # Fall back to Twitter API method
                        user_id = get_user_id_from_twitter_api(handle)
                        logging.info(f"Got user_id {user_id} for handle {handle} from Twitter API")
                except Exception as e:
                    logging.error(f"Error getting user_id for handle {handle}: {str(e)}")
                    user_id = None
                
                # Add URL to tracking with the user_id
                type_val = str(row[1].get('first category')) if not pd.isna(row[1].get('first category')) else "kol"
                subtype = str(row[1].get('second_category')) if not pd.isna(row[1].get('second_category')) else "-"
                add_url_to_tracking(conn, url, type_val, subtype, user_id)
                
                # Get url_tracking record ID and user_id
                cursor = conn.cursor()
                
                # Check if id column exists in url_tracking table
                cursor.execute("PRAGMA table_info(url_tracking)")
                columns = [row[1] for row in cursor.fetchall()]
                
                url_tracking_id = None
                if 'id' in columns:
                    cursor.execute("SELECT id, user_id FROM url_tracking WHERE url = ?", (url,))
                    result = cursor.fetchone()
                    
                    if result:
                        url_tracking_id = result[0]
                        if result[1]:
                            user_id = result[1]
                else:
                    # If id column doesn't exist, use url as the identifier
                    cursor.execute("SELECT url, user_id FROM url_tracking WHERE url = ?", (url,))
                    result = cursor.fetchone()
                    
                    if result:
                        url_tracking_id = result[0]  # Use URL as the ID
                        if result[1]:
                            user_id = result[1]
                
                # If user_id is still not available, try one more time with direct client call
                if not user_id:
                    try:
                        # Try direct client call as a last resort
                        user_id = get_user_id_from_direct_client_call(handle)
                        if user_id:
                            # Update url_tracking with the obtained user_id
                            cursor.execute(
                                "UPDATE url_tracking SET user_id = ? WHERE url = ?",
                                (user_id, url)
                            )
                            logging.info(f"Updated url_tracking with user_id {user_id} for URL {url}")
                        else:
                            # If all methods fail, use handle as user_id
                            user_id = handle
                    except Exception as e:
                        logging.error(f"Error getting user_id for handle {handle} (final attempt): {str(e)}")
                        user_id = handle
                
                # Prepare KOL character data
                kol_data = {
                    'kol_id': user_id,
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
                
                # Get profile data using profile method
                profile_data = profile_updater.get_profile_data(handle)
                if profile_data:
                    # Update profile data in url_tracking table
                    profile_updater.update_profile_in_db(url, profile_data)
                    logging.info(f"Updated profile data for URL: {url}")
                else:
                    logging.warning(f"Could not get profile data for handle: {handle}")
                
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

def display_results(db_path, handle):
    """Display the results of Excel processing for a specific handle"""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get data from url_tracking table
        cursor.execute("SELECT * FROM url_tracking WHERE screen_name = ?", (handle,))
        url_record = cursor.fetchone()
        
        if url_record:
            # Convert SQLite row to dictionary
            url_data = {}
            for idx, col in enumerate(cursor.description):
                url_data[col[0]] = url_record[idx]
            
            print(f"\n=== Data for {handle} in url_tracking table ===")
            
            # Display basic fields
            basic_fields = ['url', 'user_id', 'status', 'type', 'subtype', 'screen_name', 'kol_name']
            for field in basic_fields:
                if field in url_data:
                    print(f"{field}: {url_data[field]}")
            
            # Display profile fields
            print("\n=== Profile Data in url_tracking table ===")
            profile_fields = [
                'followers_count', 'following_count', 'tweet_count',
                'profile_image_url', 'profile_banner_url', 'verified',
                'location', 'description', 'created_at', 'profile_updated_at'
            ]
            for field in profile_fields:
                if field in url_data and url_data[field] is not None:
                    print(f"{field}: {url_data[field]}")
            
            # Get data from kol_character table using screen_name
            cursor.execute("SELECT * FROM kol_character WHERE kol_screen_name = ?", (handle,))
            kol_record = cursor.fetchone()
            
            if kol_record:
                print(f"\n=== Data for {handle} in kol_character table ===")
                # Convert SQLite row to dictionary
                kol_data = {}
                for idx, col in enumerate(cursor.description):
                    kol_data[col[0]] = kol_record[idx]
                
                for key, value in kol_data.items():
                    print(f"{key}: {value}")
            else:
                print("\nNo corresponding record found in kol_character table")
        else:
            print(f"\nTarget handle not found in url_tracking table: {handle}")
            
    except Exception as e:
        logging.error(f"Error displaying results: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Process Excel files with KOL character data using both scraper and profile methods')
    parser.add_argument('--excel', type=str, required=True, help='Path to the Excel file')
    parser.add_argument('--db-path', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db', help='Path to the SQLite database')
    parser.add_argument('--display', type=str, help='Display results for a specific handle')
    
    args = parser.parse_args()
    
    # Create the kol_character table
    create_kol_character_table(args.db_path)
    
    # Process the Excel file
    process_excel_file(args.excel, args.db_path)
    
    # Display results if requested
    if args.display:
        display_results(args.db_path, args.display)

if __name__ == "__main__":
    main()
