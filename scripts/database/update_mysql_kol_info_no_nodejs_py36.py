#!/usr/bin/env python3
"""
Script to update the kol_info table in MySQL with data from the url_tracking table in SQLite.
This script does not require Node.js or Twitter client functionality to work.
It will sync basic URL information to MySQL even when Twitter profile data is not available.

Python 3.6 compatible version for server deployment with mysql-connector-python-8.0.29.
"""

import os
import sys
import json
import logging
import sqlite3
import tempfile
import subprocess
from datetime import datetime
import argparse
import re

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
        # Use an older version of mysql-connector-python that's compatible with Python 3.6
        # pip install mysql-connector-python==8.0.29
        import mysql.connector
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            use_pure=True  # Use the pure Python implementation to avoid C extension issues
        )
        return conn
    except ImportError:
        logging.error("MySQL Connector for Python is not installed. Please install it with 'pip install mysql-connector-python==8.0.29'")
        sys.exit(1)
    except Exception as e:
        logging.error("Error connecting to MySQL database: {}".format(str(e)))
        sys.exit(1)

def extract_twitter_handle(url):
    """Extract the Twitter handle from a URL"""
    if not url:
        return None
    
    # Remove trailing slash if present
    if url.endswith('/'):
        url = url[:-1]
    
    # Extract the handle from the URL
    parts = url.split('/')
    if len(parts) < 4:
        logging.error("Invalid URL format: {}".format(url))
        return None
    
    handle = parts[-1]
    return handle

def try_get_profile_info(handle, client_dir=None):
    """Try to get profile information for a Twitter handle using agent-twitter-client"""
    logging.info("Trying to get profile info for handle: {}".format(handle))
    
    # Set the client directory
    if client_dir is None:
        # Use the twitter_client directory
        client_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src/twitter_client')
    
    # Path to the test script
    test_script_path = os.path.join(client_dir, 'test_profile.js')
    
    # Create a temporary file for the output
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
        output_file = temp_file.name
    
    try:
        # Run the test script
        logging.info("Running test script for {}...".format(handle))
        process = subprocess.run(
            ['node', test_script_path, handle, output_file],
            cwd=client_dir,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True  # This is equivalent to text=True in Python 3.7+
        )
        
        # Check if the output file exists
        if not os.path.exists(output_file):
            logging.error("Output file {} does not exist".format(output_file))
            return None
        
        # Load the profile from the output file
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        return result
        
    except Exception as e:
        logging.error("Error getting profile for handle {}: {}".format(handle, str(e)))
        return None
    finally:
        # Remove the temporary file
        if os.path.exists(output_file):
            os.remove(output_file)

def get_basic_profile_info(handle):
    """Get basic profile information for a Twitter handle without using Node.js"""
    logging.info("Using basic profile info for handle: {}".format(handle))
    
    # Create a basic profile with the handle as the user ID
    # This is a fallback when Node.js is not available or fails
    profile = {
        "profile": {
            "userId": handle,  # Using handle as userId as a fallback
            "name": handle,
            "username": handle,
            "biography": None,
            "followersCount": None,
            "followingCount": None,
            "likesCount": None,
            "statusesCount": None,
            "tweetsCount": None,
            "joined": None
        }
    }
    
    return profile

def map_to_kol_info(profile_data, url_data):
    """Map profile data to kol_info table fields"""
    if not profile_data or not profile_data.get('profile'):
        logging.error("No profile data available")
        return None
    
    profile = profile_data['profile']
    url, type_val, description_val = url_data
    
    # Convert joined date from ISO 8601 format to MySQL datetime format
    created_at = None
    if profile.get('joined'):
        try:
            # Parse the ISO 8601 date
            # Remove the milliseconds and timezone part
            iso_date = profile.get('joined')
            # Extract the date and time parts (up to seconds)
            match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', iso_date)
            if match:
                date_part = match.group(1)
                # Convert to MySQL datetime format (YYYY-MM-DD HH:MM:SS)
                created_at = date_part.replace('T', ' ')
            else:
                logging.warning("Could not parse date: {}".format(iso_date))
        except Exception as e:
            logging.error("Error converting date: {}".format(str(e)))
    
    # Map fields from profile to kol_info
    kol_info = {
        'kol_id': profile.get('userId'),
        'kol_name': profile.get('name'),
        'kol_screen_name': "@{}".format(profile.get('username')) if profile.get('username') else None,
        'description': profile.get('biography') or description_val,  # Use description from URL if biography is not available
        'followers_count': str(profile.get('followersCount')) if profile.get('followersCount') is not None else None,
        'fast_followers_count': None,  # Not directly available
        'normal_followers_count': None,  # Not directly available
        'following_count': profile.get('followingCount'),
        'favourites_count': profile.get('likesCount'),
        'statuses_count': profile.get('statusesCount') or profile.get('tweetsCount'),
        'first_category': type_val,
        'second_category': None,  # No subtype column in the table
        'created_at': created_at
    }
    
    return kol_info

def insert_or_update_kol_info(mysql_conn, kol_info):
    """Insert or update a record in the kol_info table"""
    cursor = mysql_conn.cursor()
    
    # Check if the record already exists
    cursor.execute(
        "SELECT id FROM kol_info WHERE kol_id = %s",
        (kol_info['kol_id'],)
    )
    
    result = cursor.fetchone()
    
    if result:
        # Update existing record
        update_query = """
        UPDATE kol_info SET
            kol_name = %s,
            kol_screen_name = %s,
            description = %s,
            followers_count = %s,
            fast_followers_count = %s,
            normal_followers_count = %s,
            following_count = %s,
            favourites_count = %s,
            statuses_count = %s,
            first_category = %s,
            second_category = %s,
            created_at = %s
        WHERE kol_id = %s
        """
        
        cursor.execute(
            update_query,
            (
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
                kol_info['created_at'],
                kol_info['kol_id']
            )
        )
        
        logging.info("Updated record for kol_id: {}".format(kol_info['kol_id']))
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
        
        logging.info("Inserted new record for kol_id: {}".format(kol_info['kol_id']))
    
    mysql_conn.commit()

def get_urls_from_sqlite(limit=None):
    """Get URLs from the url_tracking table in SQLite"""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # Modified query to match the actual schema of url_tracking table
    query = "SELECT url, type, description FROM url_tracking"
    
    if limit:
        query += " LIMIT {}".format(limit)
    
    cursor.execute(query)
    
    urls = cursor.fetchall()
    conn.close()
    
    return urls

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Update kol_info table in MySQL with data from url_tracking table in SQLite')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to process')
    parser.add_argument('--test', action='store_true', help='Test mode - do not insert or update records in MySQL')
    parser.add_argument('--no-nodejs', action='store_true', help='Do not try to use Node.js for profile info')
    
    args = parser.parse_args()
    
    print("Starting MySQL update script (Node.js independent version for Python 3.6)")
    logging.info("Starting MySQL update script (Node.js independent version for Python 3.6)")
    
    # Print environment variables (without password)
    print("MySQL Host: {}".format(MYSQL_HOST))
    print("MySQL Port: {}".format(MYSQL_PORT))
    print("MySQL User: {}".format(MYSQL_USER))
    print("MySQL Database: {}".format(MYSQL_DATABASE))
    
    # Get URLs from SQLite
    urls = get_urls_from_sqlite(args.limit)
    logging.info("Got {} URLs from SQLite".format(len(urls)))
    
    # Connect to MySQL
    if not args.test:
        try:
            mysql_conn = get_mysql_connection()
            logging.info("Connected to MySQL database")
        except Exception as e:
            logging.error("Failed to connect to MySQL: {}".format(str(e)))
            sys.exit(1)
    
    # Process each URL
    processed_count = 0
    for url_data in urls:
        url = url_data[0]
        logging.info("Processing URL: {}".format(url))
        
        # Extract the Twitter handle
        handle = extract_twitter_handle(url)
        if not handle:
            logging.error("Could not extract handle from URL: {}".format(url))
            continue
        
        # Get profile information
        profile_data = None
        if not args.no_nodejs:
            # Try to get profile information using Node.js
            profile_data = try_get_profile_info(handle)
        
        # If Node.js failed or --no-nodejs flag is set, use basic profile info
        if not profile_data:
            logging.info("Using basic profile info for handle: {}".format(handle))
            profile_data = get_basic_profile_info(handle)
        
        # Map to kol_info
        kol_info = map_to_kol_info(profile_data, url_data)
        if not kol_info:
            logging.error("Could not map profile to kol_info for handle: {}".format(handle))
            continue
        
        # Insert or update record in MySQL
        if not args.test:
            try:
                insert_or_update_kol_info(mysql_conn, kol_info)
            except Exception as e:
                logging.error("Error inserting/updating record for kol_id {}: {}".format(kol_info['kol_id'], str(e)))
                continue
        else:
            logging.info("Test mode - would insert or update record for kol_id: {}".format(kol_info['kol_id']))
        
        processed_count += 1
    
    logging.info("Processed {} profiles".format(processed_count))
    
    # Close MySQL connection
    if not args.test and 'mysql_conn' in locals():
        mysql_conn.close()
        logging.info("Closed MySQL connection")
    
    logging.info("MySQL update script completed")

if __name__ == "__main__":
    main()
