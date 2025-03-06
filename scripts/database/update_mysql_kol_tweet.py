#!/usr/bin/env python3
"""
Script to update the kol_tweet table in MySQL with data from the tweets table in SQLite.
This script retrieves tweets from the SQLite database and maps them to the kol_tweet table schema in MySQL.
"""

import os
import sys
import logging
import sqlite3
from datetime import datetime
import argparse

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
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "kol_info")  # Database name confirmed from check_kol_info_table.py

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
        logging.error(f"Error connecting to MySQL database: {str(e)}")
        sys.exit(1)

def get_tweets_from_sqlite(limit=None, since_days=None):
    """Get tweets from the tweets table in SQLite"""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        t.tweet_id, 
        t.user_id, 
        t.content, 
        t.created_at, 
        t.replies, 
        t.likes, 
        t.views, 
        t.retweets
    FROM 
        tweets t
    JOIN 
        url_tracking u ON t.source_url = u.url
    WHERE 
        t.user_id IS NOT NULL
    """
    
    params = []
    
    if since_days:
        query += " AND t.created_at >= datetime('now', '-' || ? || ' days')"
        params.append(since_days)
    
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query, params)
    
    tweets = cursor.fetchall()
    conn.close()
    
    return tweets

def map_to_kol_tweet(tweet_data):
    """Map tweet data to kol_tweet table fields"""
    tweet_id, user_id, content, created_at, replies, likes, views, retweets = tweet_data
    
    # Convert created_at from SQLite format to MySQL datetime format
    mysql_created_at = None
    if created_at:
        try:
            # Handle ISO 8601 format (e.g., "2023-01-14T06:31:58.000Z")
            import re
            
            # Extract the date and time parts (up to seconds)
            match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', created_at)
            if match:
                date_part = match.group(1)
                # Convert to MySQL datetime format (YYYY-MM-DD HH:MM:SS)
                mysql_created_at = date_part.replace('T', ' ')
            else:
                # Try standard SQLite format
                dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                mysql_created_at = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logging.error(f"Error converting date {created_at}: {str(e)}")
    
    # Map fields from tweet to kol_tweet
    kol_tweet = {
        'kol_id': user_id,
        'tweet_id': tweet_id,
        'tweet_text': content,
        'created_at': mysql_created_at,
        'reply_count': replies,
        'favorite_count': likes,  # favorite_count maps to likes as per user's instruction
        'view_count': views,
        'retweet_count': retweets,
        'lang': None  # lang is not available in our data, as per user's instruction, we can leave it empty
    }
    
    return kol_tweet

def insert_or_update_kol_tweet(mysql_conn, kol_tweet):
    """Insert or update a record in the kol_tweet table"""
    cursor = mysql_conn.cursor()
    
    # Check if the record already exists
    cursor.execute(
        "SELECT id FROM kol_tweet WHERE kol_id = %s AND tweet_id = %s",
        (kol_tweet['kol_id'], kol_tweet['tweet_id'])
    )
    
    result = cursor.fetchone()
    
    if result:
        # Update existing record
        update_query = """
        UPDATE kol_tweet SET
            tweet_text = %s,
            created_at = %s,
            reply_count = %s,
            favorite_count = %s,
            view_count = %s,
            retweet_count = %s,
            lang = %s
        WHERE kol_id = %s AND tweet_id = %s
        """
        
        cursor.execute(
            update_query,
            (
                kol_tweet['tweet_text'],
                kol_tweet['created_at'],
                kol_tweet['reply_count'],
                kol_tweet['favorite_count'],
                kol_tweet['view_count'],
                kol_tweet['retweet_count'],
                kol_tweet['lang'],
                kol_tweet['kol_id'],
                kol_tweet['tweet_id']
            )
        )
        
        logging.info(f"Updated record for kol_id: {kol_tweet['kol_id']}, tweet_id: {kol_tweet['tweet_id']}")
    else:
        # Insert new record
        insert_query = """
        INSERT INTO kol_tweet (
            kol_id, tweet_id, tweet_text, created_at,
            reply_count, favorite_count, view_count, retweet_count, lang
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        cursor.execute(
            insert_query,
            (
                kol_tweet['kol_id'],
                kol_tweet['tweet_id'],
                kol_tweet['tweet_text'],
                kol_tweet['created_at'],
                kol_tweet['reply_count'],
                kol_tweet['favorite_count'],
                kol_tweet['view_count'],
                kol_tweet['retweet_count'],
                kol_tweet['lang']
            )
        )
        
        logging.info(f"Inserted new record for kol_id: {kol_tweet['kol_id']}, tweet_id: {kol_tweet['tweet_id']}")
    
    mysql_conn.commit()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Update kol_tweet table in MySQL with data from tweets table in SQLite')
    parser.add_argument('--limit', type=int, help='Limit the number of tweets to process')
    parser.add_argument('--since-days', type=int, help='Only process tweets from the last N days')
    parser.add_argument('--test', action='store_true', help='Test mode - do not insert or update records in MySQL')
    
    args = parser.parse_args()
    
    logging.info("Starting MySQL update script for tweets")
    
    # Get tweets from SQLite
    tweets = get_tweets_from_sqlite(args.limit, args.since_days)
    logging.info(f"Got {len(tweets)} tweets from SQLite")
    
    # Connect to MySQL
    if not args.test:
        mysql_conn = get_mysql_connection()
        logging.info("Connected to MySQL database")
    
    # Process each tweet
    processed_count = 0
    for tweet_data in tweets:
        # Map to kol_tweet
        kol_tweet = map_to_kol_tweet(tweet_data)
        if not kol_tweet:
            logging.error(f"Could not map tweet to kol_tweet for tweet_id: {tweet_data[0]}")
            continue
        
        # Insert or update record in MySQL
        if not args.test:
            insert_or_update_kol_tweet(mysql_conn, kol_tweet)
        else:
            logging.info(f"Test mode - would insert or update record for kol_id: {kol_tweet['kol_id']}, tweet_id: {kol_tweet['tweet_id']}")
        
        processed_count += 1
        
        # Log progress every 100 tweets
        if processed_count % 100 == 0:
            logging.info(f"Processed {processed_count}/{len(tweets)} tweets")
    
    logging.info(f"Processed {processed_count} tweets")
    
    # Close MySQL connection
    if not args.test:
        mysql_conn.close()
        logging.info("Closed MySQL connection")
    
    logging.info("MySQL update script for tweets completed")

if __name__ == "__main__":
    main()
