#!/usr/bin/env python3
"""
Script to verify KOL information synchronization between SQLite and MySQL databases.
"""

import os
import sys
import logging
import sqlite3
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Path to the SQLite database
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data/local_database.db')

# MySQL connection parameters
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "kol_info")

def get_sqlite_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect(SQLITE_DB_PATH)

def get_mysql_connection():
    """Get a connection to the MySQL database"""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        return conn
    except Exception as e:
        logging.error(f"Error connecting to MySQL database: {str(e)}")
        sys.exit(1)

def extract_handle_from_url(url):
    """Extract Twitter handle from URL"""
    if not url:
        return None
    
    # Remove trailing slash if present
    if url.endswith('/'):
        url = url[:-1]
    
    # Extract handle from URL
    parts = url.split('/')
    if len(parts) > 0:
        handle = parts[-1]
        return handle
    
    return None

def get_sqlite_urls(limit=None):
    """Get URLs from SQLite database"""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    query = "SELECT url, status FROM url_tracking"
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    urls = cursor.fetchall()
    
    conn.close()
    
    return urls

def check_mysql_kol_info(handle, limit=None):
    """Check if a Twitter handle exists in MySQL kol_info table"""
    conn = get_mysql_connection()
    cursor = conn.cursor()
    
    query = "SELECT id, kol_id, kol_name, kol_screen_name FROM kol_info WHERE kol_screen_name = %s"
    cursor.execute(query, (handle,))
    
    result = cursor.fetchone()
    
    conn.close()
    
    return result

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Verify KOL information synchronization')
    parser.add_argument('--limit', type=int, default=20, help='Limit the number of URLs to check')
    
    args = parser.parse_args()
    
    print("Verifying KOL Information Synchronization")
    print("========================================")
    
    # Get URLs from SQLite
    urls = get_sqlite_urls(args.limit)
    
    print(f"\nChecking {len(urls)} URLs from SQLite:")
    print("-------------------------------------")
    
    found_count = 0
    not_found_count = 0
    
    for url, status in urls:
        handle = extract_handle_from_url(url)
        
        if not handle:
            print(f"URL: {url} - Could not extract handle")
            continue
        
        # Check if handle exists in MySQL
        kol_info = check_mysql_kol_info(handle)
        
        if kol_info:
            found_count += 1
            print(f"Handle: {handle} - Found in MySQL")
            print(f"  ID: {kol_info[0]}, KOL ID: {kol_info[1]}, Name: {kol_info[2]}")
            print(f"  Status: ✅ Synchronized")
        else:
            not_found_count += 1
            print(f"Handle: {handle} - Not found in MySQL")
            print(f"  Status: ❌ Not synchronized")
        
        print("-------------------------------------")
    
    # Calculate synchronization percentage
    if len(urls) > 0:
        sync_percentage = (found_count / len(urls)) * 100
        print(f"\nKOL Synchronization: {sync_percentage:.2f}%")
        print(f"Found: {found_count}, Not Found: {not_found_count}, Total: {len(urls)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
