#!/usr/bin/env python3
"""
Script to check the latest tweets in the MySQL database.
This script helps diagnose synchronization issues by showing the most recent tweets in MySQL.
"""

import os
import sys
import mysql.connector
from datetime import datetime

# MySQL connection parameters
MYSQL_HOST = os.environ.get("MYSQL_HOST", "43.135.26.222")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "kol_info")

def get_mysql_connection():
    """Get a connection to the MySQL database"""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        return conn
    except Exception as e:
        print(f"Error connecting to MySQL: {str(e)}")
        sys.exit(1)

def check_latest_tweets(limit=10):
    """Check the latest tweets in the MySQL database"""
    conn = get_mysql_connection()
    cursor = conn.cursor()
    
    print(f"MySQL Host: {MYSQL_HOST}")
    print(f"MySQL Database: {MYSQL_DATABASE}")
    print("\n=== Latest {limit} Tweets in MySQL ===")
    
    cursor.execute(f"""
    SELECT tweet_id, created_at, kol_id 
    FROM kol_tweet 
    ORDER BY created_at DESC 
    LIMIT {limit}
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("No tweets found in the MySQL database.")
    else:
        for row in rows:
            print(f"Tweet ID: {row[0]}")
            print(f"Created At: {row[1]}")
            print(f"KOL ID: {row[2]}")
            print("-" * 40)
    
    print("\n=== Tweet Count in MySQL ===")
    cursor.execute("SELECT COUNT(*) FROM kol_tweet")
    count = cursor.fetchone()[0]
    print(f"Total tweets in MySQL database: {count}")
    
    print("\n=== Tweets by Date in MySQL (Last 7 Days) ===")
    cursor.execute("""
    SELECT DATE(created_at) as date, COUNT(*) as count 
    FROM kol_tweet 
    GROUP BY date 
    ORDER BY date DESC 
    LIMIT 7
    """)
    
    date_counts = cursor.fetchall()
    
    if not date_counts:
        print("No date information available in MySQL.")
    else:
        for date_count in date_counts:
            print(f"{date_count[0]}: {date_count[1]} tweets")
    
    conn.close()

if __name__ == "__main__":
    check_latest_tweets()
