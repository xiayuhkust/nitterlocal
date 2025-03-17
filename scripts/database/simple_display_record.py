#!/usr/bin/env python3
"""
Simplified script to display url_tracking and kol_character records.
This script uses a simpler approach to avoid SQL join issues.
"""

import os
import sys
import sqlite3
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def display_records(db_path, screen_name=None, url=None):
    """Display records from url_tracking and kol_character tables"""
    if not screen_name and not url:
        logging.error("Either screen_name or url must be provided")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First get the url_tracking record
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
    url_tracking_row = cursor.fetchone()
    
    if not url_tracking_row:
        logging.warning(f"No record found in url_tracking for {'screen_name=' + screen_name if screen_name else 'url=' + url}")
        conn.close()
        return False
    
    # Get column names
    cursor.execute("PRAGMA table_info(url_tracking)")
    url_tracking_columns = [row[1] for row in cursor.fetchall()]
    
    # Display url_tracking results
    print(f"\n=== URL Tracking Record for {'@' + screen_name if screen_name else url} ===")
    
    url_tracking_id = None
    for i, col in enumerate(url_tracking_columns):
        value = url_tracking_row[i]
        print(f"{col}: {value}")
        if col == 'id':
            url_tracking_id = value
    
    # Now get the kol_character record if url_tracking_id exists
    if url_tracking_id:
        cursor.execute("SELECT * FROM kol_character WHERE url_tracking_id = ?", [url_tracking_id])
        kol_character_row = cursor.fetchone()
        
        if kol_character_row:
            # Get column names
            cursor.execute("PRAGMA table_info(kol_character)")
            kol_character_columns = [row[1] for row in cursor.fetchall()]
            
            # Display kol_character results
            print(f"\n=== KOL Character Record for url_tracking_id={url_tracking_id} ===")
            
            for i, col in enumerate(kol_character_columns):
                value = kol_character_row[i]
                print(f"{col}: {value}")
        else:
            print(f"\nNo KOL Character record found for url_tracking_id={url_tracking_id}")
    
    conn.close()
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Display database records for a Twitter handle")
    parser.add_argument("--db-path", default="data/local_database.db", help="Path to the SQLite database")
    parser.add_argument("--screen-name", help="Twitter screen name to look up")
    parser.add_argument("--url", help="Twitter URL to look up")
    
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
    display_records(args.db_path, args.screen_name, args.url)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
