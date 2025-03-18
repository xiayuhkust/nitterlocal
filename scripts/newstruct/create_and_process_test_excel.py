#!/usr/bin/env python3
"""
Script to process Excel files containing Twitter URLs.
This script processes Excel files and updates the database with Twitter handle information.
"""

import os
import sys
import logging
import sqlite3
import pandas as pd
import argparse
import tempfile
from urllib.parse import urlparse

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import Twitter utilities
try:
    from app.twitter_utils import extract_twitter_handle, process_twitter_urls
    logging.info("Successfully imported Twitter utilities")
except ImportError:
    logging.warning("Could not import Twitter utilities, using fallback functions")
    
    # Fallback Twitter handle extraction function
    def extract_twitter_handle(url):
        """Extract Twitter handle from a URL"""
        if not url:
            return None
        
        try:
            # Parse the URL
            parsed_url = urlparse(url)
            
            # Extract the handle from the path
            path_parts = parsed_url.path.strip('/').split('/')
            if not path_parts:
                return None
            
            handle = path_parts[0]
            return handle.lower()
        except Exception as e:
            logging.error(f"Error extracting Twitter handle from {url}: {str(e)}")
            return None
    
    # Fallback process_twitter_urls function
    def process_twitter_urls(urls):
        """Process Twitter URLs to extract handles"""
        if not urls:
            return []
        
        # Split URLs by comma, newline, or semicolon
        if isinstance(urls, str):
            url_list = [u.strip() for u in urls.replace('\n', ',').replace(';', ',').split(',')]
        else:
            url_list = urls
        
        # Filter out empty strings
        url_list = [u for u in url_list if u]
        
        # Extract handles
        handles = []
        for url in url_list:
            handle = extract_twitter_handle(url)
            if handle:
                handles.append(handle)
        
        return handles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def process_excel_file(excel_path, db_path, limit=None):
    """Process an Excel file with KOL character data"""
    logging.info(f"Processing Excel file: {excel_path} with limit: {limit}")
    
    try:
        # Import the process_excel_with_profile function
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
        from process_excel_with_profile import process_excel_file as process_excel
        
        # Check if url_tracking table exists and create it if needed
        conn = sqlite3.connect(db_path)
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
        else:
            # Check if screen_name column exists
            cursor.execute("PRAGMA table_info(url_tracking)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Add screen_name column if it doesn't exist
            if 'screen_name' not in columns:
                cursor.execute("ALTER TABLE url_tracking ADD COLUMN screen_name TEXT")
                conn.commit()
                logging.info("Added screen_name column to url_tracking table")
            
            # Add kol_name column if it doesn't exist
            if 'kol_name' not in columns:
                cursor.execute("ALTER TABLE url_tracking ADD COLUMN kol_name TEXT")
                conn.commit()
                logging.info("Added kol_name column to url_tracking table")
        
        conn.close()
        
        # Read the Excel file to apply limit if specified
        if limit is not None:
            df = pd.read_excel(excel_path)
            # Apply limit to the DataFrame
            df = df.head(limit)
            # Create a temporary file with limited rows
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
                limited_excel_path = temp_file.name
            df.to_excel(limited_excel_path, index=False)
            logging.info(f"Created limited Excel file with {len(df)} rows at {limited_excel_path}")
            # Process the limited Excel file
            process_excel(limited_excel_path, db_path)
            # Clean up the temporary file
            if os.path.exists(limited_excel_path):
                os.remove(limited_excel_path)
        else:
            # Process the entire Excel file
            process_excel(excel_path, db_path)
        
        logging.info(f"Processed Excel file: {excel_path}")
        return True
    except Exception as e:
        logging.error(f"Error processing Excel file: {str(e)}")
        return False

def main():
    """Main function"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Process Excel files with KOL character data')
    parser.add_argument('--excel', type=str, required=True, help='Path to the Excel file')
    parser.add_argument('--limit', type=int, help='Limit processing to the first N rows')
    parser.add_argument('--db-path', type=str, 
                        default=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/local_database.db')),
                        help='Path to the SQLite database')
    
    args = parser.parse_args()
    
    # Set the database path
    db_path = args.db_path
    
    # Process the Excel file with optional limit
    if not process_excel_file(args.excel, db_path, args.limit):
        logging.error("Failed to process Excel file, exiting")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
