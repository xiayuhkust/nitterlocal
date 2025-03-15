#!/usr/bin/env python3
"""
Script to check the latest tweets in the local SQLite database.
This script helps diagnose synchronization issues by showing the most recent tweets.
"""

import os
import sys
import sqlite3
from datetime import datetime

# Path to the SQLite database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data/local_database.db')

def check_latest_tweets(limit=10):
    """Check the latest tweets in the local database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Database path: {DB_PATH}")
    print("\n=== Latest {limit} Tweets ===")
    
    cursor.execute(f"SELECT tweet_id, created_at, author FROM tweets ORDER BY created_at DESC LIMIT {limit}")
    rows = cursor.fetchall()
    
    if not rows:
        print("No tweets found in the database.")
    else:
        for row in rows:
            print(f"Tweet ID: {row[0]}")
            print(f"Created At: {row[1]}")
            print(f"Author: {row[2]}")
            print("-" * 40)
    
    print("\n=== Tweet Count ===")
    cursor.execute("SELECT COUNT(*) FROM tweets")
    count = cursor.fetchone()[0]
    print(f"Total tweets in database: {count}")
    
    print("\n=== Tweets by Date (Last 7 Days) ===")
    cursor.execute("SELECT DATE(created_at) as date, COUNT(*) as count FROM tweets GROUP BY date ORDER BY date DESC LIMIT 7")
    date_counts = cursor.fetchall()
    
    if not date_counts:
        print("No date information available.")
    else:
        for date_count in date_counts:
            print(f"{date_count[0]}: {date_count[1]} tweets")
    
    conn.close()

if __name__ == "__main__":
    check_latest_tweets()
