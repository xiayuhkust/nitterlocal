#!/usr/bin/env python3
"""
Script to display url_tracking and kol_character data from the SQLite database.
This helps verify that URL normalization is working correctly.
"""

import os
import sys
import sqlite3
import logging
import argparse

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def display_url_tracking_data(db_path, limit=10, filter_term=None):
    """Display url_tracking data from the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Build query
    query = "SELECT id, url, screen_name, user_id, followers_count, following_count, tweet_count FROM url_tracking"
    params = []
    
    if filter_term:
        query += " WHERE url LIKE ? OR screen_name LIKE ?"
        params = [f"%{filter_term}%", f"%{filter_term}%"]
    
    query += f" LIMIT {limit}"
    
    # Execute query
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Display results
    print("\n=== URL Tracking Data ===")
    if rows:
        print(f"{'ID':<5} {'URL':<40} {'Screen Name':<20} {'User ID':<25} {'Followers':<10} {'Following':<10} {'Tweets':<10}")
        print("-" * 120)
        for row in rows:
            id, url, screen_name, user_id, followers, following, tweets = row
            print(f"{id:<5} {url[:38]:<40} {screen_name[:18]:<20} {str(user_id)[:23]:<25} {str(followers)[:8]:<10} {str(following)[:8]:<10} {str(tweets)[:8]:<10}")
        
        print(f"\nShowing {len(rows)} of {cursor.execute('SELECT COUNT(*) FROM url_tracking').fetchone()[0]} records")
    else:
        print("No records found in url_tracking table")
    
    conn.close()

def display_kol_character_data(db_path, limit=10, filter_term=None):
    """Display kol_character data from the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Build query
    query = "SELECT id, kol_id, kol_screen_name, bio, url_tracking_id FROM kol_character"
    params = []
    
    if filter_term:
        query += " WHERE kol_screen_name LIKE ?"
        params = [f"%{filter_term}%"]
    
    query += f" LIMIT {limit}"
    
    # Execute query
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Display results
    print("\n=== KOL Character Data ===")
    if rows:
        print(f"{'ID':<5} {'KOL ID':<25} {'Screen Name':<20} {'Bio':<50} {'URL Tracking ID':<15}")
        print("-" * 120)
        for row in rows:
            id, kol_id, screen_name, bio, url_tracking_id = row
            print(f"{id:<5} {str(kol_id)[:23]:<25} {screen_name[:18]:<20} {bio[:48]:<50} {str(url_tracking_id):<15}")
        
        print(f"\nShowing {len(rows)} of {cursor.execute('SELECT COUNT(*) FROM kol_character').fetchone()[0]} records")
    else:
        print("No records found in kol_character table")
    
    conn.close()

def display_joined_data(db_path, limit=10, filter_term=None):
    """Display joined data from url_tracking and kol_character tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Build query
    query = """
    SELECT 
        u.id as url_id,
        u.url, 
        u.screen_name, 
        u.user_id, 
        k.id as kol_id,
        k.kol_screen_name, 
        k.bio
    FROM url_tracking u
    LEFT JOIN kol_character k ON u.id = k.url_tracking_id
    """
    params = []
    
    if filter_term:
        query += " WHERE u.url LIKE ? OR u.screen_name LIKE ? OR k.kol_screen_name LIKE ?"
        params = [f"%{filter_term}%", f"%{filter_term}%", f"%{filter_term}%"]
    
    query += f" LIMIT {limit}"
    
    # Execute query
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Display results
    print("\n=== Joined URL Tracking and KOL Character Data ===")
    if rows:
        print(f"{'URL ID':<7} {'URL':<40} {'Screen Name':<20} {'User ID':<25} {'KOL ID':<7} {'KOL Screen Name':<20} {'Bio':<40}")
        print("-" * 160)
        for row in rows:
            url_id, url, screen_name, user_id, kol_id, kol_screen_name, bio = row
            kol_screen_name = kol_screen_name or "N/A"
            bio = bio or "N/A"
            print(f"{url_id:<7} {url[:38]:<40} {screen_name[:18]:<20} {str(user_id)[:23]:<25} {str(kol_id):<7} {kol_screen_name[:18]:<20} {bio[:38]:<40}")
        
        print(f"\nShowing {len(rows)} of {cursor.execute('SELECT COUNT(*) FROM url_tracking').fetchone()[0]} records")
    else:
        print("No joined records found")
    
    conn.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Display data from the SQLite database")
    parser.add_argument("--db-path", default="data/local_database.db", help="Path to the SQLite database")
    parser.add_argument("--limit", type=int, default=10, help="Limit the number of records to display")
    parser.add_argument("--filter", help="Filter term to search for in URLs and screen names")
    parser.add_argument("--table", choices=["url", "kol", "joined", "all"], default="all", 
                        help="Table to display: url_tracking, kol_character, joined data, or all")
    
    args = parser.parse_args()
    
    # Check if the database exists
    if not os.path.exists(args.db_path):
        logging.error(f"Database file not found: {args.db_path}")
        return 1
    
    # Display the requested data
    if args.table == "url" or args.table == "all":
        display_url_tracking_data(args.db_path, args.limit, args.filter)
    
    if args.table == "kol" or args.table == "all":
        display_kol_character_data(args.db_path, args.limit, args.filter)
    
    if args.table == "joined" or args.table == "all":
        display_joined_data(args.db_path, args.limit, args.filter)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
