#!/usr/bin/env python3
"""
Script to display complete url_tracking and kol_character records for a specific Twitter handle.
This helps verify the data stored in the database after Excel processing.
"""

import os
import sys
import sqlite3
import logging
import argparse
import pandas as pd
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def display_url_tracking_record(db_path, screen_name=None, url=None):
    """Display complete url_tracking record for a specific screen name or URL"""
    if not screen_name and not url:
        logging.error("Either screen_name or url must be provided")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all column names for url_tracking table
    cursor.execute("PRAGMA table_info(url_tracking)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Build query
    query = "SELECT * FROM url_tracking WHERE "
    params = []
    
    if screen_name:
        query += "screen_name = ? COLLATE NOCASE"
        params = [screen_name]
    else:
        query += "url LIKE ? COLLATE NOCASE"
        params = [f"%{url}%"]
    
    # Execute query
    cursor.execute(query, params)
    row = cursor.fetchone()
    
    if not row:
        logging.warning(f"No record found in url_tracking for {'screen_name=' + screen_name if screen_name else 'url=' + url}")
        conn.close()
        return False
    
    # Display results
    print(f"\n=== URL Tracking Record for {'@' + screen_name if screen_name else url} ===")
    url_tracking_id = None
    
    for i, col in enumerate(columns):
        value = row[i]
        print(f"{col}: {value}")
        if col == 'id':
            url_tracking_id = value
    
    conn.close()
    return url_tracking_id

def display_kol_character_record(db_path, url_tracking_id):
    """Display complete kol_character record for a specific url_tracking_id"""
    if not url_tracking_id:
        logging.error("url_tracking_id must be provided")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all column names for kol_character table
    cursor.execute("PRAGMA table_info(kol_character)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Build query
    query = "SELECT * FROM kol_character WHERE url_tracking_id = ?"
    params = [url_tracking_id]
    
    # Execute query
    cursor.execute(query, params)
    row = cursor.fetchone()
    
    if not row:
        logging.warning(f"No record found in kol_character for url_tracking_id={url_tracking_id}")
        conn.close()
        return False
    
    # Display results
    print(f"\n=== KOL Character Record for url_tracking_id={url_tracking_id} ===")
    
    for i, col in enumerate(columns):
        value = row[i]
        print(f"{col}: {value}")
    
    conn.close()
    return True

def display_joined_record(db_path, screen_name=None, url=None):
    """Display joined record from url_tracking and kol_character tables"""
    if not screen_name and not url:
        logging.error("Either screen_name or url must be provided")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First get the url_tracking record
    url_tracking_query = "SELECT * FROM url_tracking WHERE "
    params = []
    
    if screen_name:
        url_tracking_query += "screen_name = ? COLLATE NOCASE"
        params = [screen_name]
    else:
        url_tracking_query += "url LIKE ? COLLATE NOCASE"
        params = [f"%{url}%"]
    
    # Execute query for url_tracking
    cursor.execute(url_tracking_query, params)
    url_tracking_row = cursor.fetchone()
    
    if not url_tracking_row:
        logging.warning(f"No record found in url_tracking for {'screen_name=' + screen_name if screen_name else 'url=' + url}")
        conn.close()
        return False
    
    # Get url_tracking column names
    cursor.execute("PRAGMA table_info(url_tracking)")
    url_tracking_columns = [row[1] for row in cursor.fetchall()]
    
    # Create a dictionary for url_tracking data
    url_tracking_data = {url_tracking_columns[i]: url_tracking_row[i] for i in range(len(url_tracking_columns))}
    
    # Get the url_tracking_id (try 'id' first, then fall back to using the URL)
    url_tracking_id = url_tracking_data.get('id')
    
    # If id column doesn't exist, use the URL as the identifier
    if url_tracking_id is None:
        url_tracking_id = url_tracking_data.get('url')
        logging.info(f"No 'id' column found, using URL as identifier: {url_tracking_id}")
    
    # Now get the kol_character record
    kol_character_data = {}
    if url_tracking_id is not None:
        # Try to find by url_tracking_id first
        cursor.execute("SELECT * FROM kol_character WHERE url_tracking_id = ?", [url_tracking_id])
        kol_character_row = cursor.fetchone()
        
        # If not found and we have a screen_name, try to find by screen_name
        if not kol_character_row and screen_name:
            cursor.execute("SELECT * FROM kol_character WHERE kol_screen_name = ? COLLATE NOCASE", [screen_name])
            kol_character_row = cursor.fetchone()
            if kol_character_row:
                logging.info(f"Found kol_character record by screen_name: {screen_name}")

        
        if kol_character_row:
            # Get kol_character column names
            cursor.execute("PRAGMA table_info(kol_character)")
            kol_character_columns = [row[1] for row in cursor.fetchall()]
            
            # Create a dictionary for kol_character data
            kol_character_data = {kol_character_columns[i]: kol_character_row[i] for i in range(len(kol_character_columns))}
    
    # Display results
    print(f"\n=== Joined Record for {'@' + screen_name if screen_name else url} ===")
    
    # Display url_tracking columns
    print("\n--- URL Tracking Fields ---")
    for col, value in url_tracking_data.items():
        print(f"{col}: {value}")
    
    # Display kol_character columns
    print("\n--- KOL Character Fields ---")
    if kol_character_data:
        for col, value in kol_character_data.items():
            print(f"{col}: {value}")
    else:
        print("No KOL character data found for this record")
    
    conn.close()
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Display complete database records for a Twitter handle")
    parser.add_argument("--db-path", default="data/local_database.db", help="Path to the SQLite database")
    parser.add_argument("--screen-name", help="Twitter screen name to look up")
    parser.add_argument("--url", help="Twitter URL to look up")
    parser.add_argument("--format", choices=["separate", "joined"], default="joined", 
                        help="Display format: separate tables or joined record")
    
    args = parser.parse_args()
    
    # Check if the database exists
    if not os.path.exists(args.db_path):
        logging.error(f"Database file not found: {args.db_path}")
        return 1
    
    # Check if either screen_name or url is provided
    if not args.screen_name and not args.url:
        logging.error("Either --screen-name or --url must be provided")
        return 1
    
    # Display records
    if args.format == "separate":
        url_tracking_id = display_url_tracking_record(args.db_path, args.screen_name, args.url)
        if url_tracking_id:
            display_kol_character_record(args.db_path, url_tracking_id)
    else:
        display_joined_record(args.db_path, args.screen_name, args.url)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
