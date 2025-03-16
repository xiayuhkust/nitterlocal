#!/usr/bin/env python3
"""
Script to add screen_name field to url_tracking table and populate it from URLs.

This script:
1. Adds a screen_name column to the url_tracking table if it doesn't exist
2. Extracts Twitter handles from URLs and updates the screen_name field
3. Provides detailed logging of the update process
"""

import os
import sys
import time
import logging
import sqlite3
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_sqlite_connection(db_path='/home/ubuntu/nitterlocal/data/local_database.db'):
    """Get a connection to the SQLite database"""
    try:
        # Connect to SQLite
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        return conn
    
    except Exception as e:
        logging.error(f"Error connecting to SQLite: {str(e)}")
        raise

def add_screen_name_column(conn):
    """Add screen_name column to url_tracking table if it doesn't exist"""
    cursor = conn.cursor()
    
    # Check if screen_name column exists
    cursor.execute("PRAGMA table_info(url_tracking)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'screen_name' not in columns:
        logging.info("Adding screen_name column to url_tracking table")
        cursor.execute("ALTER TABLE url_tracking ADD COLUMN screen_name TEXT")
        conn.commit()
        logging.info("Added screen_name column to url_tracking table")
    else:
        logging.info("screen_name column already exists in url_tracking table")
    
    return 'screen_name' in columns

def extract_handle_from_url(url):
    """Extract Twitter handle from URL"""
    if not url:
        return None
    
    try:
        # Handle both twitter.com and x.com domains
        if 'twitter.com/' in url:
            parts = url.split('twitter.com/')
        elif 'x.com/' in url:
            parts = url.split('x.com/')
        else:
            return None
        
        if len(parts) > 1:
            handle = parts[1].split('/')[0].split('?')[0]
            # Clean up the handle (remove @ if present)
            if handle.startswith('@'):
                handle = handle[1:]
            return handle
    except Exception as e:
        logging.error(f"Error extracting handle from URL {url}: {str(e)}")
    
    return None

def update_screen_names(conn, test_mode=False, verbose=False):
    """Update screen_name field in url_tracking table based on URLs"""
    cursor = conn.cursor()
    
    # Get all records from url_tracking
    cursor.execute("SELECT url FROM url_tracking")
    rows = cursor.fetchall()
    
    total_rows = len(rows)
    logging.info(f"Found {total_rows} records in url_tracking table")
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for row in rows:
        url = row['url']
        
        # Extract handle from URL
        handle = extract_handle_from_url(url)
        
        if handle:
            if not test_mode:
                try:
                    cursor.execute(
                        "UPDATE url_tracking SET screen_name = ? WHERE url = ?",
                        (handle, url)
                    )
                    updated_count += 1
                    
                    if verbose:
                        logging.info(f"Updated screen_name to '{handle}' for URL: {url}")
                except Exception as e:
                    logging.error(f"Error updating screen_name for URL {url}: {str(e)}")
                    error_count += 1
            else:
                if verbose:
                    logging.info(f"Would update screen_name to '{handle}' for URL: {url}")
                updated_count += 1
        else:
            if verbose:
                logging.info(f"Could not extract handle from URL: {url}")
            skipped_count += 1
    
    if not test_mode:
        conn.commit()
    
    logging.info(f"Updated {updated_count} records with screen_name")
    logging.info(f"Skipped {skipped_count} records (no handle found)")
    logging.info(f"Encountered {error_count} errors")
    
    return updated_count, skipped_count, error_count

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Add and populate screen_name field in url_tracking table')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no actual changes)')
    parser.add_argument('--db-path', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db',
                        help='Path to SQLite database')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    try:
        start_time = time.time()
        logging.info(f"Starting screen_name update at {datetime.now().isoformat()}")
        
        # Connect to SQLite
        conn = get_sqlite_connection(args.db_path)
        
        # Add screen_name column if it doesn't exist
        column_existed = add_screen_name_column(conn)
        
        # Update screen_name field
        updated, skipped, errors = update_screen_names(conn, args.test, args.verbose)
        
        # Close connection
        conn.close()
        
        # Calculate duration
        duration = time.time() - start_time
        
        logging.info(f"Screen name update completed in {duration:.2f} seconds")
        logging.info(f"Column existed before: {column_existed}")
        logging.info(f"Updated {updated} records, skipped {skipped} records, encountered {errors} errors")
        
        return 0
    
    except Exception as e:
        logging.error(f"Error in screen_name update: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
