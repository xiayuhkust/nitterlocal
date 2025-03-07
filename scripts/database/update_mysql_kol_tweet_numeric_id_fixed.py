#!/usr/bin/env python3
"""
Script to update the kol_tweet table in MySQL with data from the tweets table in SQLite.
This script retrieves tweets from the SQLite database and maps them to the kol_tweet table schema in MySQL.
This version handles the case where kol_id in MySQL is a numeric field.

Python 3.6 compatible version for server deployment.
"""

import os
import sys
import logging
import sqlite3
import hashlib
import re
from datetime import datetime
import argparse

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

def get_tweets_from_sqlite(limit=None, since_days=None):
    """Get tweets from the tweets table in SQLite"""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        t.tweet_id, 
        t.author, 
        t.content, 
        t.likes, 
        t.retweets, 
        t.replies, 
        t.views,
        t.created_at,
        t.language,
        t.source_url,
        t.user_id
    FROM 
        tweets t
    """
    
    params = []
    
    if since_days:
        # SQLite date format is ISO 8601: YYYY-MM-DD HH:MM:SS
        # We need to use date() function to get the date part
        query += " WHERE date(t.created_at) >= date('now', '-{} days')".format(since_days)
    
    if limit:
        query += " LIMIT {}".format(limit)
    
    cursor.execute(query, params)
    
    tweets = cursor.fetchall()
    conn.close()
    
    return tweets

def extract_twitter_handle(url):
    """Extract the Twitter handle from a URL"""
    if not url:
        return None
    
    # Remove trailing slash if present
    if url.endswith('/'):
        url = url[:-1]
    
    # Extract the last part of the URL path
    parts = url.split('/')
    if len(parts) < 4:
        return None
    
    handle = parts[-1]
    
    # Convert to lowercase for consistency
    handle = handle.lower()
    
    return handle

def generate_numeric_id(handle):
    """Generate a numeric ID from a Twitter handle using a hash function"""
    if not handle:
        return None
    
    # Use the last 15 digits of the hash to ensure it fits in a bigint
    hash_value = int(hashlib.md5(handle.encode()).hexdigest(), 16) % 10**15
    
    return hash_value

def parse_sqlite_date(date_str):
    """Parse a date string from SQLite and convert it to a MySQL-compatible datetime string"""
    if not date_str:
        return None
    
    # SQLite date format is ISO 8601: YYYY-MM-DDTHH:MM:SS.sssZ
    # We need to convert it to MySQL datetime format: YYYY-MM-DD HH:MM:SS
    
    # Remove timezone information if present
    date_str = re.sub(r'[+-]\d{2}:\d{2}$', '', date_str)
    date_str = date_str.replace('Z', '')
    
    # Remove milliseconds if present
    date_str = re.sub(r'\.\d+$', '', date_str)
    
    # Replace 'T' with space
    date_str = date_str.replace('T', ' ')
    
    return date_str

def map_to_kol_tweet(tweet_data):
    """Map tweet data to kol_tweet table fields"""
    tweet_id, author, content, likes, retweets, replies, views, date, language, source_url, user_id = tweet_data
    
    # Extract Twitter handle from source_url or use author
    handle = extract_twitter_handle(source_url) if source_url else author
    if not handle:
        handle = author
    
    # Generate numeric ID from handle
    numeric_id = generate_numeric_id(handle)
    if not numeric_id:
        logging.warning("Could not generate numeric ID for handle: {}".format(handle))
        return None
    
    # Parse date
    parsed_date = parse_sqlite_date(date)
    if not parsed_date:
        logging.warning("Could not parse date: {}".format(date))
        parsed_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Map fields from tweets to kol_tweet
    kol_tweet = {
        'kol_id': numeric_id,  # Use numeric ID for kol_id
        'tweet_id': tweet_id,
        'tweet_text': content,
        'created_at': parsed_date,
        'reply_count': replies or 0,
        'favorite_count': likes or 0,
        'view_count': views or 0,
        'retweet_count': retweets or 0,
        'lang': language or ''
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
        
        logging.info("Updated record for kol_id: {}, tweet_id: {}".format(kol_tweet['kol_id'], kol_tweet['tweet_id']))
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
        
        logging.info("Inserted new record for kol_id: {}, tweet_id: {}".format(kol_tweet['kol_id'], kol_tweet['tweet_id']))
    
    mysql_conn.commit()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Update kol_tweet table in MySQL with data from tweets table in SQLite')
    parser.add_argument('--limit', type=int, help='Limit the number of tweets to process')
    parser.add_argument('--since-days', type=int, help='Only process tweets from the last N days')
    parser.add_argument('--test', action='store_true', help='Test mode - do not insert or update records in MySQL')
    
    args = parser.parse_args()
    
    print("Starting MySQL update script for tweets (Numeric ID version for Python 3.6)")
    logging.info("Starting MySQL update script for tweets (Numeric ID version for Python 3.6)")
    
    # Print environment variables (without password)
    print("MySQL Host: {}".format(MYSQL_HOST))
    print("MySQL Port: {}".format(MYSQL_PORT))
    print("MySQL User: {}".format(MYSQL_USER))
    print("MySQL Database: {}".format(MYSQL_DATABASE))
    print("SQLite Database: {}".format(SQLITE_DB_PATH))
    
    # Get tweets from SQLite
    tweets = get_tweets_from_sqlite(args.limit, args.since_days)
    print("Got {} tweets from SQLite".format(len(tweets)))
    logging.info("Got {} tweets from SQLite".format(len(tweets)))
    
    # Connect to MySQL
    if not args.test:
        mysql_conn = get_mysql_connection()
        print("Connected to MySQL database")
        logging.info("Connected to MySQL database")
    else:
        print("Test mode - not connecting to MySQL database")
        logging.info("Test mode - not connecting to MySQL database")
    
    # Process each tweet
    processed_count = 0
    for tweet_data in tweets:
        # Map to kol_tweet
        kol_tweet = map_to_kol_tweet(tweet_data)
        if not kol_tweet:
            print("Could not map tweet to kol_tweet for tweet_id: {}".format(tweet_data[0]))
            logging.error("Could not map tweet to kol_tweet for tweet_id: {}".format(tweet_data[0]))
            continue
        
        # Insert or update record in MySQL
        if not args.test:
            try:
                insert_or_update_kol_tweet(mysql_conn, kol_tweet)
            except Exception as e:
                print("Error inserting/updating record for kol_id: {}, tweet_id: {}: {}".format(kol_tweet['kol_id'], kol_tweet['tweet_id'], str(e)))
                logging.error("Error inserting/updating record for kol_id: {}, tweet_id: {}: {}".format(kol_tweet['kol_id'], kol_tweet['tweet_id'], str(e)))
                continue
        else:
            print("Test mode - would insert or update record for kol_id: {}, tweet_id: {}".format(kol_tweet['kol_id'], kol_tweet['tweet_id']))
            logging.info("Test mode - would insert or update record for kol_id: {}, tweet_id: {}".format(kol_tweet['kol_id'], kol_tweet['tweet_id']))
        
        processed_count += 1
        
        # Log progress every 100 tweets
        if processed_count % 100 == 0:
            print("Processed {}/{}".format(processed_count, len(tweets)))
            logging.info("Processed {}/{}".format(processed_count, len(tweets)))
    
    print("Processed {} tweets".format(processed_count))
    logging.info("Processed {} tweets".format(processed_count))
    
    # Close MySQL connection
    if not args.test:
        mysql_conn.close()
        print("Closed MySQL connection")
        logging.info("Closed MySQL connection")
    
    print("MySQL update script for tweets completed")
    logging.info("MySQL update script for tweets completed")

if __name__ == "__main__":
    main()
