#!/usr/bin/env python3
"""
Script to clean database tables based on Excel file data.
This script:
1. Reads Twitter URLs from Excel file
2. Deletes records in url_tracking where URL is not in Excel (with URL normalization)
3. Updates screen_name field in url_tracking for remaining records
4. Deletes records in tweets where author is not in url_tracking's screen_name
5. Deletes records in kol_character where kol_screen_name is not in url_tracking's screen_name
"""

import os
import sys
import logging
import pandas as pd
import sqlite3
import argparse
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def extract_twitter_handle(url):
    """Extract Twitter handle from a URL (works with both twitter.com and x.com)"""
    if not url:
        return None
    
    try:
        # Parse the URL
        parsed_url = urlparse(url)
        
        # Check if it's a Twitter URL
        if 'twitter.com' in parsed_url.netloc or 'x.com' in parsed_url.netloc:
            # Extract the handle from the path
            path_parts = parsed_url.path.strip('/').split('/')
            if not path_parts:
                return None
            
            handle = path_parts[0]
            return handle.lower()
        else:
            return None
    except Exception as e:
        logging.error(f"Error extracting Twitter handle from {url}: {str(e)}")
        return None

def normalize_twitter_url(url):
    """Normalize Twitter URL to handle both twitter.com and x.com domains"""
    if not url:
        return None
    
    try:
        # Extract handle
        handle = extract_twitter_handle(url)
        if not handle:
            return url  # Return original if we can't extract handle
        
        # Return both possible URLs
        return [f"https://twitter.com/{handle}", f"https://x.com/{handle}"]
    except Exception as e:
        logging.error(f"Error normalizing Twitter URL {url}: {str(e)}")
        return [url]  # Return original in case of error

def update_screen_names(conn):
    """Update screen_name field in url_tracking table for all records"""
    try:
        cursor = conn.cursor()
        
        # Get all URLs from url_tracking
        cursor.execute("SELECT url FROM url_tracking")
        urls = cursor.fetchall()
        
        updated_count = 0
        for (url,) in urls:
            # Extract handle from URL
            handle = extract_twitter_handle(url)
            if handle:
                # Update screen_name field
                cursor.execute(
                    "UPDATE url_tracking SET screen_name = ? WHERE url = ?",
                    (handle, url)
                )
                updated_count += 1
        
        conn.commit()
        logging.info(f"Updated screen_name for {updated_count} records in url_tracking")
        return updated_count
    except Exception as e:
        logging.error(f"Error updating screen_names: {str(e)}")
        return 0

def clean_database(excel_path, db_path):
    """Clean database tables based on Excel file data"""
    try:
        # Read the Excel file
        df = pd.read_excel(excel_path)
        logging.info(f"Read Excel file: {excel_path} with {len(df)} rows")
        
        # Check if Twitter URL column exists
        twitter_col = 'Twitter url'
        if twitter_col not in df.columns:
            logging.error(f"Column '{twitter_col}' not found in Excel file")
            return False
        
        # Extract Twitter URLs from Excel and normalize them
        excel_urls_raw = df[twitter_col].dropna().tolist()
        excel_handles = [extract_twitter_handle(url) for url in excel_urls_raw]
        excel_handles = [h for h in excel_handles if h]  # Remove None values
        
        # Create normalized URLs for both twitter.com and x.com
        excel_urls = []
        for handle in excel_handles:
            excel_urls.append(f"https://twitter.com/{handle}")
            excel_urls.append(f"https://x.com/{handle}")
        
        logging.info(f"Found {len(excel_urls_raw)} Twitter URLs in Excel file")
        logging.info(f"Extracted {len(excel_handles)} valid Twitter handles")
        logging.info(f"Generated {len(excel_urls)} normalized URLs for comparison")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Update screen_name field in url_tracking
        update_screen_names(conn)
        
        # Get all URLs from url_tracking for logging
        cursor.execute("SELECT url FROM url_tracking")
        db_urls = [row[0] for row in cursor.fetchall()]
        logging.info(f"Found {len(db_urls)} URLs in url_tracking table")
        
        # Log some sample URLs from both sources for debugging
        logging.info(f"Sample Excel URLs: {excel_urls[:5]}")
        logging.info(f"Sample DB URLs: {db_urls[:5] if db_urls else []}")
        
        # 1. Delete records in url_tracking where URL is not in Excel
        cursor.execute("SELECT COUNT(*) FROM url_tracking")
        before_count = cursor.fetchone()[0]
        
        # Create a placeholder string for the SQL query
        placeholders = ','.join(['?'] * len(excel_urls))
        
        # Only execute if we have URLs to keep
        if excel_urls:
            cursor.execute(
                f"DELETE FROM url_tracking WHERE url NOT IN ({placeholders})",
                excel_urls
            )
        
        cursor.execute("SELECT COUNT(*) FROM url_tracking")
        after_count = cursor.fetchone()[0]
        
        deleted_count = before_count - after_count
        logging.info(f"Deleted {deleted_count} records from url_tracking (before: {before_count}, after: {after_count})")
        
        # Get remaining screen_names from url_tracking
        cursor.execute("SELECT screen_name FROM url_tracking WHERE screen_name IS NOT NULL")
        valid_screen_names = [row[0] for row in cursor.fetchall() if row[0]]
        logging.info(f"Found {len(valid_screen_names)} valid screen_names in url_tracking")
        
        # 2. Delete records in tweets where author is not in url_tracking's screen_name
        cursor.execute("SELECT COUNT(*) FROM tweets")
        before_count = cursor.fetchone()[0]
        
        if valid_screen_names:
            placeholders = ','.join(['?'] * len(valid_screen_names))
            cursor.execute(
                f"DELETE FROM tweets WHERE author NOT IN ({placeholders})",
                valid_screen_names
            )
        else:
            # If no valid screen names, don't delete everything - log a warning
            logging.warning("No valid screen_names found in url_tracking, skipping tweets deletion")
        
        cursor.execute("SELECT COUNT(*) FROM tweets")
        after_count = cursor.fetchone()[0]
        
        deleted_count = before_count - after_count
        logging.info(f"Deleted {deleted_count} records from tweets (before: {before_count}, after: {after_count})")
        
        # 3. Delete records in kol_character where kol_screen_name is not in url_tracking's screen_name
        cursor.execute("SELECT COUNT(*) FROM kol_character")
        before_count = cursor.fetchone()[0]
        
        if valid_screen_names and before_count > 0:
            placeholders = ','.join(['?'] * len(valid_screen_names))
            cursor.execute(
                f"DELETE FROM kol_character WHERE kol_screen_name NOT IN ({placeholders})",
                valid_screen_names
            )
        else:
            # If no valid screen names or no records, log a warning
            logging.warning("No valid screen_names found in url_tracking or no records in kol_character, skipping kol_character deletion")
        
        cursor.execute("SELECT COUNT(*) FROM kol_character")
        after_count = cursor.fetchone()[0]
        
        deleted_count = before_count - after_count
        logging.info(f"Deleted {deleted_count} records from kol_character (before: {before_count}, after: {after_count})")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logging.info("Database cleaning completed successfully")
        return True
    except Exception as e:
        logging.error(f"Error cleaning database: {str(e)}")
        return False

def backup_tables(db_path):
    """Backup tables before cleaning"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Backup url_tracking table
        cursor.execute("CREATE TABLE IF NOT EXISTS url_tracking_backup AS SELECT * FROM url_tracking")
        
        # Backup tweets table
        cursor.execute("CREATE TABLE IF NOT EXISTS tweets_backup AS SELECT * FROM tweets")
        
        # Create kol_character table if it doesn't exist
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
            UNIQUE(kol_screen_name)
        )
        ''')
        
        # Backup kol_character table
        cursor.execute("CREATE TABLE IF NOT EXISTS kol_character_backup AS SELECT * FROM kol_character")
        
        conn.commit()
        conn.close()
        
        logging.info("Tables backed up successfully")
        return True
    except Exception as e:
        logging.error(f"Error backing up tables: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Clean database tables based on Excel file data')
    parser.add_argument('--excel', type=str, help='Path to the Excel file')
    parser.add_argument('--db-path', type=str, help='Path to the SQLite database')
    parser.add_argument('--backup', action='store_true', help='Backup tables before cleaning')
    
    args = parser.parse_args()
    
    # Default paths
    excel_path = args.excel if args.excel else '/home/ubuntu/attachments/5d1276b2-78dc-49dc-b222-b11d9f4d9039/kol+characte_.xlsx'
    db_path = args.db_path if args.db_path else '/home/ubuntu/repos/nitterlocal/data/local_database.db'
    
    # Backup tables if requested
    if args.backup:
        backup_tables(db_path)
    
    # Clean database
    clean_database(excel_path, db_path)

if __name__ == "__main__":
    main()
