#!/usr/bin/env python3
"""
Script to create a test Excel file with cz_binance data and process it.
This script demonstrates the complete workflow from Excel creation to database storage.
Can also process an existing Excel file with optional row limit.
"""

import os
import sys
import logging
import sqlite3
import pandas as pd
import tempfile
import argparse
from datetime import datetime
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

def create_test_excel():
    """Create a test Excel file with cz_binance data"""
    logging.info("Creating test Excel file with cz_binance data")
    
    # Create a DataFrame with cz_binance data
    data = {
        'Twitter url': ['https://twitter.com/cz_binance'],
        'first category': ['KOL'],
        'second_category': ['-'],
        'bio': ['Binance创始人赵长鹏'],
        'lore': ['Active in crypto since 2017, known for founding Binance'],
        'knowledge': ['Crypto Trading: Expert in blockchain and exchanges'],
        'postExamples': ['BTC testing 70K resistance'],
        'topics': ['Crypto Trading: Shares insights on market trends'],
        'style_all': ['Analytical: Focuses on data and trends'],
        'style_chat': ['Concise: Short, informative replies'],
        'style_post': ['Brief: Quick market updates'],
        'adjectives': ['Analytical, Precise, Practical']
    }
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(data)
    
    # Create a temporary file for the Excel
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
        excel_path = temp_file.name
    
    df.to_excel(excel_path, index=False)
    
    logging.info(f"Created test Excel file at {excel_path}")
    return excel_path

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
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Process Excel files with KOL character data')
    parser.add_argument('--excel', type=str, help='Path to the Excel file (default: create a test Excel file)')
    parser.add_argument('--limit', type=int, help='Limit processing to the first N rows')
    parser.add_argument('--db-path', type=str, 
                        default=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/local_database.db')),
                        help='Path to the SQLite database')
    parser.add_argument('--handle', type=str, default='cz_binance', 
                        help='Twitter handle to display results for (default: cz_binance)')
    
    args = parser.parse_args()
    
    # Set the database path
    db_path = args.db_path
    
    # Set the handle to check
    handle = args.handle
    
    # Use provided Excel file or create a test one
    if args.excel:
        excel_path = args.excel
        is_test_excel = False
        logging.info(f"Using provided Excel file: {excel_path}")
    else:
        excel_path = create_test_excel()
        is_test_excel = True
        logging.info(f"Created test Excel file: {excel_path}")
    
    # Process the Excel file with optional limit
    if not process_excel_file(excel_path, db_path, args.limit):
        logging.error("Failed to process Excel file, exiting")
        return 1
    
    # Display results
    if not display_results(db_path, handle):
        logging.error("Failed to display results, exiting")
        return 1
    
    # Clean up test Excel file if created
    if is_test_excel and os.path.exists(excel_path):
        os.remove(excel_path)
        logging.info(f"Removed test Excel file: {excel_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
