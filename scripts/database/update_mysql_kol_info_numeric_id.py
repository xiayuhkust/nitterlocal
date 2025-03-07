#!/usr/bin/env python3
"""
Script to update the kol_info table in MySQL with data from the url_tracking table in SQLite.
This script retrieves URLs from the SQLite database and maps them to the kol_info table schema in MySQL.
This version handles the case where kol_id in MySQL is a numeric field.

Python 3.6 compatible version for server deployment.
"""

import os
import sys
import logging
import sqlite3
import hashlib
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

def get_urls_from_sqlite(limit=None):
    """Get URLs from the url_tracking table in SQLite"""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        url, 
        description, 
        type, 
        tweet_count,
        user_id,
        subtype
    FROM 
        url_tracking
    """
    
    if limit:
        query += " LIMIT {}".format(limit)
    
    cursor.execute(query)
    
    urls = cursor.fetchall()
    conn.close()
    
    return urls

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

def map_to_kol_info(url_data):
    """Map URL data to kol_info table fields"""
    url, description, url_type, tweet_count, user_id, subtype = url_data
    
    # Extract Twitter handle from URL
    handle = extract_twitter_handle(url)
    if not handle:
        logging.warning("Could not extract handle from URL: {}".format(url))
        return None
    
    # Generate numeric ID from handle
    numeric_id = generate_numeric_id(handle)
    if not numeric_id:
        logging.warning("Could not generate numeric ID for handle: {}".format(handle))
        return None
    
    # Map fields from url_tracking to kol_info
    kol_info = {
        'kol_id': numeric_id,  # Use numeric ID for kol_id
        'kol_name': description or handle,  # Use description as kol_name if available, otherwise use handle
        'kol_screen_name': handle,  # Use handle as kol_screen_name
        'description': description,
        'followers_count': '0',  # Default value
        'fast_followers_count': 0,  # Default value
        'normal_followers_count': 0,  # Default value
        'following_count': 0,  # Default value
        'favourites_count': 0,  # Default value
        'statuses_count': tweet_count or 0,  # Use tweet_count as statuses_count if available
        'first_category': url_type,  # Use type as first_category
        'second_category': subtype,  # Use subtype as second_category
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current time
    }
    
    return kol_info

def insert_or_update_kol_info(mysql_conn, kol_info):
    """Insert or update a record in the kol_info table"""
    cursor = mysql_conn.cursor()
    
    # Check if the record already exists
    cursor.execute(
        "SELECT id FROM kol_info WHERE kol_screen_name = %s",
        (kol_info['kol_screen_name'],)
    )
    
    result = cursor.fetchone()
    
    if result:
        # Update existing record
        update_query = """
        UPDATE kol_info SET
            kol_id = %s,
            kol_name = %s,
            description = %s,
            followers_count = %s,
            fast_followers_count = %s,
            normal_followers_count = %s,
            following_count = %s,
            favourites_count = %s,
            statuses_count = %s,
            first_category = %s,
            second_category = %s
        WHERE kol_screen_name = %s
        """
        
        cursor.execute(
            update_query,
            (
                kol_info['kol_id'],
                kol_info['kol_name'],
                kol_info['description'],
                kol_info['followers_count'],
                kol_info['fast_followers_count'],
                kol_info['normal_followers_count'],
                kol_info['following_count'],
                kol_info['favourites_count'],
                kol_info['statuses_count'],
                kol_info['first_category'],
                kol_info['second_category'],
                kol_info['kol_screen_name']
            )
        )
        
        logging.info("Updated record for kol_screen_name: {}".format(kol_info['kol_screen_name']))
    else:
        # Insert new record
        insert_query = """
        INSERT INTO kol_info (
            kol_id, kol_name, kol_screen_name, description,
            followers_count, fast_followers_count, normal_followers_count,
            following_count, favourites_count, statuses_count,
            first_category, second_category, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        cursor.execute(
            insert_query,
            (
                kol_info['kol_id'],
                kol_info['kol_name'],
                kol_info['kol_screen_name'],
                kol_info['description'],
                kol_info['followers_count'],
                kol_info['fast_followers_count'],
                kol_info['normal_followers_count'],
                kol_info['following_count'],
                kol_info['favourites_count'],
                kol_info['statuses_count'],
                kol_info['first_category'],
                kol_info['second_category'],
                kol_info['created_at']
            )
        )
        
        logging.info("Inserted new record for kol_screen_name: {}".format(kol_info['kol_screen_name']))
    
    mysql_conn.commit()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Update kol_info table in MySQL with data from url_tracking table in SQLite')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to process')
    parser.add_argument('--test', action='store_true', help='Test mode - do not insert or update records in MySQL')
    
    args = parser.parse_args()
    
    print("Starting MySQL update script (Numeric ID version for Python 3.6)")
    logging.info("Starting MySQL update script (Numeric ID version for Python 3.6)")
    
    # Print environment variables (without password)
    print("MySQL Host: {}".format(MYSQL_HOST))
    print("MySQL Port: {}".format(MYSQL_PORT))
    print("MySQL User: {}".format(MYSQL_USER))
    print("MySQL Database: {}".format(MYSQL_DATABASE))
    
    # Get URLs from SQLite
    urls = get_urls_from_sqlite(args.limit)
    print("Got {} URLs from SQLite".format(len(urls)))
    logging.info("Got {} URLs from SQLite".format(len(urls)))
    
    # Connect to MySQL
    if not args.test:
        mysql_conn = get_mysql_connection()
        print("Connected to MySQL database")
        logging.info("Connected to MySQL database")
    
    # Process each URL
    processed_count = 0
    for url_data in urls:
        # Map to kol_info
        kol_info = map_to_kol_info(url_data)
        if not kol_info:
            print("Could not map URL to kol_info for URL: {}".format(url_data[0]))
            logging.error("Could not map URL to kol_info for URL: {}".format(url_data[0]))
            continue
        
        # Insert or update record in MySQL
        if not args.test:
            try:
                insert_or_update_kol_info(mysql_conn, kol_info)
            except Exception as e:
                print("Error inserting/updating record for kol_screen_name {}: {}".format(kol_info['kol_screen_name'], str(e)))
                logging.error("Error inserting/updating record for kol_screen_name {}: {}".format(kol_info['kol_screen_name'], str(e)))
                continue
        else:
            print("Test mode - would insert or update record for kol_screen_name: {}".format(kol_info['kol_screen_name']))
            logging.info("Test mode - would insert or update record for kol_screen_name: {}".format(kol_info['kol_screen_name']))
        
        processed_count += 1
        
        # Log progress every 100 URLs
        if processed_count % 100 == 0:
            print("Processed {}/{}".format(processed_count, len(urls)))
            logging.info("Processed {}/{}".format(processed_count, len(urls)))
    
    print("Processed {} profiles".format(processed_count))
    logging.info("Processed {} profiles".format(processed_count))
    
    # Close MySQL connection
    if not args.test:
        mysql_conn.close()
        print("Closed MySQL connection")
        logging.info("Closed MySQL connection")
    
    print("MySQL update script completed")
    logging.info("MySQL update script completed")

if __name__ == "__main__":
    main()
