#!/usr/bin/env python3
"""
Script to add URLs from a JSON file to the local database.
Python 3.6 compatible version.
"""

import os
import json
import logging
import argparse
import subprocess
import sys
import sqlite3
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Path to the SQLite database
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data/local_database.db')

def initialize_database():
    """Initialize the local database"""
    try:
        # Get the path to the database initialization script
        init_script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src/database/init_database.sql')
        
        # Connect to the database
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        
        # Read and execute the initialization script
        with open(init_script_path, 'r') as f:
            init_script = f.read()
            cursor.executescript(init_script)
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logging.info("Database initialization complete")
    except Exception as e:
        logging.error("Error initializing database: {}".format(str(e)))
        sys.exit(1)

def clear_urls():
    """Clear existing URLs from the database"""
    try:
        # Connect to the database
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        
        # Delete all records from the url_tracking table
        cursor.execute("DELETE FROM url_tracking")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logging.info("Existing URLs cleared from the database")
    except Exception as e:
        logging.error("Error clearing URLs from the database: {}".format(str(e)))
        sys.exit(1)

def get_twitter_user_id(handle):
    """Get the Twitter user ID for a handle using the Twitter client"""
    try:
        # Since test_user_id.js doesn't exist, we'll use the handle as the user_id
        # In a production environment, you would implement a proper way to get the user ID
        logging.warning("Using handle as user_id for {}".format(handle))
        return handle
    except Exception as e:
        logging.error("Error getting user ID for handle {}: {}".format(handle, str(e)))
        return None

def extract_handle_from_url(url):
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
    
    return handle

def add_url_to_database(url, description, url_type, subtype=None):
    """Add a URL to the database"""
    try:
        # Connect to the database
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        
        # Extract handle from URL
        handle = extract_handle_from_url(url)
        if not handle:
            logging.error("Could not extract handle from URL: {}".format(url))
            conn.close()
            return False
        
        # Get Twitter user ID
        user_id = get_twitter_user_id(handle)
        if not user_id:
            logging.warning("Could not get user ID for handle {}, using handle as user_id".format(handle))
            user_id = handle
        
        # Insert the URL into the database
        cursor.execute(
            "INSERT INTO url_tracking (url, description, type, tweet_count, user_id, subtype) VALUES (?, ?, ?, ?, ?, ?)",
            (url, description, url_type, 0, user_id, subtype)
        )
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logging.info("Added URL {} to database with user_id {}".format(url, user_id))
        return True
    except Exception as e:
        logging.error("Error adding URL {} to database: {}".format(url, str(e)))
        return False

def add_urls_from_json(json_file):
    """Add URLs from a JSON file to the database"""
    try:
        # Read the JSON file
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Check if the JSON has a 'urls' key (new format) or is a direct array (old format)
        if isinstance(data, dict) and 'urls' in data:
            urls = data['urls']
        else:
            urls = data
        
        logging.info("Found {} URLs in {}".format(len(urls), json_file))
        
        # Initialize Twitter scraper
        try:
            # Path to the Twitter scraper module
            scraper_module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src/twitter_client')
            
            # Add the scraper module path to the Python path
            sys.path.insert(0, scraper_module_path)
            
            # Import the Twitter scraper
            from twitter_scraper import TwitterScraper
            
            # Initialize the scraper
            scraper = TwitterScraper()
        except Exception as e:
            logging.error("Error initializing Twitter scraper: {}".format(str(e)))
            scraper = None
        
        # Add each URL to the database
        success_count = 0
        for url_data in urls:
            url = url_data.get('url')
            description = url_data.get('description')
            url_type = url_data.get('type')
            subtype = url_data.get('subtype')
            
            if not url:
                logging.warning("Skipping URL data with no URL: {}".format(url_data))
                continue
            
            if add_url_to_database(url, description, url_type, subtype):
                success_count += 1
        
        logging.info("Added {} URLs to the database".format(success_count))
        return success_count
    except Exception as e:
        logging.error("Error adding URLs from JSON file: {}".format(str(e)))
        return 0

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Add URLs from a JSON file to the local database')
    parser.add_argument('--file', required=True, help='Path to the JSON file containing URLs')
    parser.add_argument('--clear', action='store_true', help='Clear existing URLs from the database')
    
    args = parser.parse_args()
    
    # Check if the JSON file exists
    if not os.path.isfile(args.file):
        logging.error("JSON file not found: {}".format(args.file))
        sys.exit(1)
    
    logging.info("Adding URLs from {} to database at {}".format(args.file, SQLITE_DB_PATH))
    
    # Initialize the database if it doesn't exist
    if not os.path.isfile(SQLITE_DB_PATH):
        logging.info("Initializing local database at {}".format(SQLITE_DB_PATH))
        initialize_database()
    
    # Clear existing URLs if requested
    if args.clear:
        logging.warning("Clearing existing URLs from the database")
        clear_urls()
    
    # Add URLs from the JSON file
    add_urls_from_json(args.file)

if __name__ == "__main__":
    main()
