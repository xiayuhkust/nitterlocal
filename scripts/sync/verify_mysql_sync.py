#!/usr/bin/env python3
"""
Script to verify the synchronization between SQLite and MySQL databases.
This script checks if data from SQLite has been successfully transferred to MySQL.
"""

import os
import sys
import logging
import sqlite3
import argparse
from datetime import datetime, timedelta

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Try to import dotenv for environment variable management
try:
    from dotenv import load_dotenv
    # Load environment variables from .env file if it exists
    load_dotenv()
    logging.info("Loaded environment variables from .env file")
except ImportError:
    logging.info("python-dotenv not installed, using environment variables directly")
    pass

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
    except ImportError:
        logging.error("MySQL Connector for Python is not installed. Please install it with 'pip install mysql-connector-python'")
        sys.exit(1)
    except Exception as e:
        logging.error("Error connecting to MySQL database: {}".format(str(e)))
        sys.exit(1)

def get_sqlite_stats():
    """Get statistics from the SQLite database"""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # Get URL count
    cursor.execute("SELECT COUNT(*) FROM url_tracking")
    url_count = cursor.fetchone()[0]
    
    # Get tweet count
    cursor.execute("SELECT COUNT(*) FROM tweets")
    tweet_count = cursor.fetchone()[0]
    
    # Get recent tweet count (last 24 hours)
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("SELECT COUNT(*) FROM tweets WHERE created_at > ?", (yesterday_str,))
    recent_tweet_count = cursor.fetchone()[0]
    
    # Get unique author count
    cursor.execute("SELECT COUNT(DISTINCT author) FROM tweets")
    author_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'url_count': url_count,
        'tweet_count': tweet_count,
        'recent_tweet_count': recent_tweet_count,
        'author_count': author_count
    }

def get_mysql_stats():
    """Get statistics from the MySQL database"""
    conn = get_mysql_connection()
    cursor = conn.cursor()
    
    # Get KOL count
    cursor.execute("SELECT COUNT(*) FROM kol_info")
    kol_count = cursor.fetchone()[0]
    
    # Get tweet count
    cursor.execute("SELECT COUNT(*) FROM kol_tweet")
    tweet_count = cursor.fetchone()[0]
    
    # Get recent tweet count (last 24 hours)
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("SELECT COUNT(*) FROM kol_tweet WHERE created_at > %s", (yesterday_str,))
    recent_tweet_count = cursor.fetchone()[0]
    
    # Get unique kol_id count
    cursor.execute("SELECT COUNT(DISTINCT kol_id) FROM kol_tweet")
    kol_id_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'kol_count': kol_count,
        'tweet_count': tweet_count,
        'recent_tweet_count': recent_tweet_count,
        'kol_id_count': kol_id_count
    }

def verify_tweet_sync(limit=5):
    """Verify that tweets from SQLite have been synchronized to MySQL"""
    sqlite_conn = get_sqlite_connection()
    sqlite_cursor = sqlite_conn.cursor()
    
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor()
    
    # Get recent tweets from SQLite - using tweet_id instead of id
    sqlite_cursor.execute(
        "SELECT tweet_id, author, content, created_at FROM tweets ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
    
    sqlite_tweets = sqlite_cursor.fetchall()
    
    print("\nRecent Tweets in SQLite:")
    print("------------------------")
    for tweet in sqlite_tweets:
        tweet_id, author, content, created_at = tweet
        print(f"ID: {tweet_id}, Author: {author}, Date: {created_at}")
        print(f"Content: {content[:50]}..." if len(content) > 50 else f"Content: {content}")
        print()
        
        # Check if this tweet exists in MySQL - using tweet_text instead of content
        mysql_cursor.execute(
            "SELECT id, kol_id, tweet_text, created_at FROM kol_tweet WHERE tweet_id = %s",
            (tweet_id,)
        )
        
        mysql_tweet = mysql_cursor.fetchone()
        
        if mysql_tweet:
            mysql_id, mysql_kol_id, mysql_content, mysql_created_at = mysql_tweet
            print("Found in MySQL:")
            print(f"ID: {mysql_id}, KOL ID: {mysql_kol_id}, Date: {mysql_created_at}")
            print(f"Content: {mysql_content[:50]}..." if len(mysql_content) > 50 else f"Content: {mysql_content}")
            print("Sync Status: ✅ Synchronized")
        else:
            print("Not found in MySQL")
            print("Sync Status: ❌ Not synchronized")
        
        print("------------------------")
    
    sqlite_conn.close()
    mysql_conn.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Verify synchronization between SQLite and MySQL databases')
    parser.add_argument('--tweets', action='store_true', help='Verify tweet synchronization')
    parser.add_argument('--limit', type=int, default=5, help='Limit the number of tweets to check')
    
    args = parser.parse_args()
    
    print("Verifying database synchronization")
    print("==================================")
    
    # Get statistics from both databases
    sqlite_stats = get_sqlite_stats()
    mysql_stats = get_mysql_stats()
    
    print("\nSQLite Database Statistics:")
    print(f"URLs: {sqlite_stats['url_count']}")
    print(f"Tweets: {sqlite_stats['tweet_count']}")
    print(f"Recent Tweets (24h): {sqlite_stats['recent_tweet_count']}")
    print(f"Unique Authors: {sqlite_stats['author_count']}")
    
    print("\nMySQL Database Statistics:")
    print(f"KOLs: {mysql_stats['kol_count']}")
    print(f"Tweets: {mysql_stats['tweet_count']}")
    print(f"Recent Tweets (24h): {mysql_stats['recent_tweet_count']}")
    print(f"Unique KOL IDs: {mysql_stats['kol_id_count']}")
    
    # Calculate synchronization percentage
    if sqlite_stats['tweet_count'] > 0:
        sync_percentage = (mysql_stats['tweet_count'] / sqlite_stats['tweet_count']) * 100
        print(f"\nTweet Synchronization: {sync_percentage:.2f}%")
    else:
        print("\nNo tweets in SQLite database")
    
    if sqlite_stats['author_count'] > 0:
        kol_sync_percentage = (mysql_stats['kol_id_count'] / sqlite_stats['author_count']) * 100
        print(f"KOL Synchronization: {kol_sync_percentage:.2f}%")
    else:
        print("No authors in SQLite database")
    
    # Verify tweet synchronization if requested
    if args.tweets:
        verify_tweet_sync(args.limit)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
