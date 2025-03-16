#!/usr/bin/env python3
"""
Script to update the kol_tweet table in MySQL with data from the tweets table in SQLite.
This script is designed to work on a server with Python 3.6.

This version is optimized for cross-server synchronization and handles the missing user_id column
by extracting the Twitter handle from the author field.
"""

import os
import sys
import logging
import sqlite3
import argparse
import re
import time
from datetime import datetime, timedelta

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the detailed logger
try:
    from src.utils.detailed_logger import log_data_operation, log_sync_summary
except ImportError:
    # Define fallback functions if the module is not available
    def log_data_operation(operation_type, table_name, record_count, details=None):
        logging.info(f"{operation_type}: {record_count} records in {table_name}")
    
    def log_sync_summary(tables_updated, total_records, duration, success=True):
        logging.info(f"Sync summary: {total_records} records across {len(tables_updated)} tables in {duration:.2f} seconds")

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
    
    query = "SELECT tweet_id, source_url, content, created_at, author, likes, retweets, replies, views, stored_at FROM tweets"
    
    params = []
    
    # Add filter for recent tweets if since_days is specified
    if since_days:
        # Calculate the date N days ago
        since_date = (datetime.now() - timedelta(days=since_days)).strftime('%Y-%m-%d')
        query += " WHERE created_at >= ?"
        params.append(since_date)
    
    # Add limit if specified
    if limit:
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
    
    cursor.execute(query, params)
    
    tweets = cursor.fetchall()
    conn.close()
    
    return tweets

def convert_date_format(date_str):
    """Convert date string from SQLite format to MySQL format"""
    if not date_str:
        return None
    
    # Try different date formats
    formats = [
        # ISO format with timezone
        r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(\.\d+)?([+-]\d{2}:\d{2}|Z)?',
        # Twitter format
        r'(\w{3} \w{3} \d{2} \d{2}:\d{2}:\d{2} [+-]\d{4} \d{4})',
        # Simple date format
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
    ]
    
    for format_pattern in formats:
        match = re.search(format_pattern, date_str)
        if match:
            try:
                if format_pattern == formats[0]:  # ISO format
                    # Extract the date and time parts (up to seconds)
                    date_part = match.group(1)
                    # Convert to MySQL datetime format (YYYY-MM-DD HH:MM:SS)
                    return date_part.replace('T', ' ')
                elif format_pattern == formats[1]:  # Twitter format
                    # Parse Twitter format
                    dt = datetime.strptime(match.group(1), '%a %b %d %H:%M:%S %z %Y')
                    # Convert to MySQL datetime format
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                else:  # Simple date format
                    # Already in MySQL format
                    return match.group(1)
            except Exception as e:
                logging.error("Error converting date {}: {}".format(date_str, str(e)))
    
    logging.warning("Could not parse date: {}".format(date_str))
    return None

def extract_handle_from_author(author):
    """Extract the Twitter handle from the author field"""
    if not author:
        return None
    
    # Remove @ if present
    if author.startswith('@'):
        author = author[1:]
    
    # Remove any additional text after the handle
    # Handles can only contain letters, numbers, and underscores
    match = re.match(r'^([a-zA-Z0-9_]+)', author)
    if match:
        return match.group(1)
    
    return author

def get_numeric_id_for_handle(mysql_conn, handle):
    """Get the numeric ID for a Twitter handle from the kol_info table"""
    if not mysql_conn or not handle:
        return None
    
    cursor = None
    try:
        cursor = mysql_conn.cursor()
        
        # Query the kol_info table for the numeric ID
        cursor.execute(
            "SELECT kol_id FROM kol_info WHERE kol_screen_name = %s OR kol_screen_name = %s",
            (handle, '@' + handle)
        )
        
        result = cursor.fetchone()
        
        if result:
            return result[0]
        else:
            # If not found, try to match by name
            cursor.execute(
                "SELECT kol_id FROM kol_info WHERE kol_name = %s",
                (handle,)
            )
            
            result = cursor.fetchone()
            
            if result:
                return result[0]
            else:
                # Return a default numeric ID based on the handle
                # This is a fallback when the handle is not found in kol_info
                # Using a hash function to generate a consistent numeric ID
                import hashlib
                hash_obj = hashlib.md5(handle.encode())
                # Convert the first 8 bytes of the hash to an integer
                numeric_id = int(hash_obj.hexdigest()[:8], 16)
                return str(numeric_id)
    except Exception as e:
        logging.error(f"Error getting numeric ID for handle {handle}: {str(e)}")
        return None
    finally:
        if cursor:
            cursor.close()

def insert_or_update_kol_tweet(mysql_conn, tweet_data):
    """Insert or update a record in the kol_tweet table"""
    cursor = None
    try:
        cursor = mysql_conn.cursor()
        
        # Extract data from the tweet
        tweet_id, source_url, content, created_at, author, likes, retweets, replies, views, stored_at = tweet_data
        
        # Extract the handle from the author field
        handle = extract_handle_from_author(author)
        
        # Get the numeric ID for the handle
        kol_id = get_numeric_id_for_handle(mysql_conn, handle)
        
        if not kol_id:
            logging.warning("Could not get numeric ID for handle: {}".format(handle))
            return
        
        # Convert date format
        mysql_created_at = convert_date_format(created_at)
        
        # Check if the record already exists
        cursor.execute(
            "SELECT id FROM kol_tweet WHERE tweet_id = %s",
            (tweet_id,)
        )
        
        result = cursor.fetchone()
        
        if result:
            # Update existing record
            update_query = """
            UPDATE kol_tweet SET
                kol_id = %s,
                tweet_text = %s,
                created_at = %s,
                reply_count = %s,
                favorite_count = %s,
                view_count = %s,
                retweet_count = %s
            WHERE tweet_id = %s
            """
            
            cursor.execute(
                update_query,
                (
                    kol_id,
                    content,
                    mysql_created_at,
                    replies,
                    likes,
                    views,
                    retweets,
                    tweet_id
                )
            )
            
            logging.info("Updated record for kol_id: {}, tweet_id: {}".format(kol_id, tweet_id))
        else:
            # Insert new record
            insert_query = """
            INSERT INTO kol_tweet (
                kol_id, tweet_id, tweet_text, created_at,
                reply_count, favorite_count, view_count, retweet_count
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            cursor.execute(
                insert_query,
                (
                    kol_id,
                    tweet_id,
                    content,
                    mysql_created_at,
                    replies,
                    likes,
                    views,
                    retweets
                )
            )
            
            logging.info("Inserted new record for kol_id: {}, tweet_id: {}".format(kol_id, tweet_id))
        
        mysql_conn.commit()
    except Exception as e:
        logging.error("Error inserting or updating record for tweet_id {}: {}".format(tweet_id, str(e)))
        if mysql_conn:
            mysql_conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Update kol_tweet table in MySQL with data from tweets table in SQLite')
    parser.add_argument('--limit', type=int, help='Limit the number of tweets to process')
    parser.add_argument('--test', action='store_true', help='Test mode - do not insert or update records in MySQL')
    parser.add_argument('--since-days', type=int, help='Only process tweets from the last N days')
    
    args = parser.parse_args()
    
    print("Starting MySQL update script for tweets")
    logging.info("Starting MySQL update script for tweets")
    
    start_time = time.time()
    
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
    mysql_conn = None
    if not args.test:
        mysql_conn = get_mysql_connection()
        logging.info("Connected to MySQL database")
    else:
        print("Test mode - not connecting to MySQL database")
    
    # Process each tweet
    processed_count = 0
    insert_count = 0
    update_count = 0
    error_count = 0
    
    try:
        for tweet_data in tweets:
            tweet_id = tweet_data[0]
            author = tweet_data[4]
            
            # Extract the handle from the author field
            kol_id = extract_handle_from_author(author)
            
            # Insert or update record in MySQL
            if not args.test and mysql_conn:
                try:
                    # Check if record exists
                    cursor = mysql_conn.cursor()
                    cursor.execute("SELECT id FROM kol_tweet WHERE tweet_id = %s", (tweet_id,))
                    exists = cursor.fetchone()
                    cursor.close()
                    
                    # Track if this is an insert or update
                    is_update = exists is not None
                    
                    # Perform the operation
                    insert_or_update_kol_tweet(mysql_conn, tweet_data)
                    
                    # Ensure all results are consumed to prevent "Unread result found" errors
                    while mysql_conn.unread_result:
                        cursor = mysql_conn.cursor()
                        cursor.fetchall()
                        cursor.close()
                    
                    if is_update:
                        update_count += 1
                    else:
                        insert_count += 1
                except Exception as e:
                    logging.error(f"Error processing tweet {tweet_id}: {str(e)}")
                    error_count += 1
            else:
                print("Test mode - would insert or update record for kol_id: {}, tweet_id: {}".format(kol_id, tweet_id))
                logging.info("Test mode - would insert or update record for kol_id: {}, tweet_id: {}".format(kol_id, tweet_id))
            
            processed_count += 1
    except Exception as e:
        logging.error("Error processing tweets: {}".format(str(e)))
    finally:
        # Close MySQL connection
        if mysql_conn:
            mysql_conn.close()
            logging.info("Closed MySQL connection")
    
    duration = time.time() - start_time
    
    print("Processed {} tweets".format(processed_count))
    logging.info("Processed {} tweets".format(processed_count))
    logging.info("MySQL update script for tweets completed")
    print("MySQL update script for tweets completed")
    
    # Log detailed summary
    if not args.test:
        log_sync_summary(
            ['kol_tweet'], 
            processed_count,
            duration,
            success=(error_count == 0)
        )
        
        # Log detailed operation counts
        log_data_operation(
            'sync_to_mysql', 
            'kol_tweet', 
            processed_count,
            {
                'inserted': insert_count,
                'updated': update_count,
                'errors': error_count,
                'duration_seconds': duration
            }
        )

if __name__ == "__main__":
    main()
