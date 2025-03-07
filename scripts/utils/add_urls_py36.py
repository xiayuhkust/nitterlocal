#!/usr/bin/env python3
"""
Script to add URLs to the database.
This script adds URLs from a JSON file to the database.
Python 3.6 compatible version.
"""

import os
import sys
import logging
import json
import argparse
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import the database module
from src.database.local_database import LocalDatabase
from scripts.utils.url_utils import convert_nitter_to_twitter, extract_twitter_handle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_user_id_from_twitter_handle(handle):
    """Get user ID from Twitter handle without using TwitterScraper"""
    if not handle:
        return None
    
    # Use the handle as the user ID
    # This avoids making HTTP requests to Twitter which can cause timeouts
    logging.info("Using handle as user ID: {}".format(handle))
    return handle

def determine_subtype(url_data):
    """Determine the subtype of a URL based on its type and other metadata"""
    url_type = url_data.get('type', 'kol')
    
    # For KOL type, subtype is null
    if url_type == 'kol':
        return None
    
    # For institution type, check if it's an exchange or meme
    if url_type == 'institution':
        # Check if subtype is already specified
        if 'subtype' in url_data and url_data['subtype']:
            return url_data['subtype']
        
        # Check if it's from CoinMarketCap exchanges
        if url_data.get('coinmarketcap_url') and 'coinmarketcap.com/exchanges/' in url_data.get('coinmarketcap_url', ''):
            return 'exchange'
        
        # Check if it's from CoinMarketCap memes
        if url_data.get('coinmarketcap_url') and 'coinmarketcap.com/view/memes/' in url_data.get('coinmarketcap_url', ''):
            return 'meme'
    
    # Default to null
    return None

def add_urls_from_file(file_path, db_path='data/local_database.db', clear_existing=False):
    """Add URLs from a JSON file to the database"""
    logging.info("Adding URLs from {} to database at {}".format(file_path, db_path))
    
    try:
        # Load URLs from file
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Extract URLs from the data
        if isinstance(data, dict) and 'urls' in data:
            urls = data['urls']
        elif isinstance(data, list):
            urls = data
        else:
            logging.error("Invalid data format in {}".format(file_path))
            return False
        
        logging.info("Found {} URLs in {}".format(len(urls), file_path))
        
        # Initialize the database
        db = LocalDatabase(db_path=db_path)
        
        # Clear existing URLs if requested
        if clear_existing:
            logging.warning("Clearing existing URLs from the database")
            conn = db.get_connection()
            # Set a timeout for the operation
            conn.execute("PRAGMA busy_timeout = 10000")  # 10 seconds timeout
            cursor = conn.cursor()
            cursor.execute("DELETE FROM url_tracking")
            conn.commit()
            conn.close()
            logging.info("Existing URLs cleared from the database")
        
        # Add URLs to the database
        added_count = 0
        for url_data in urls:
            if isinstance(url_data, str):
                # Simple URL string
                # Convert to Twitter URL if it's a Nitter URL
                url = convert_nitter_to_twitter(url_data)
                
                # Extract Twitter handle and get user ID
                handle = extract_twitter_handle(url)
                user_id = get_user_id_from_twitter_handle(handle) if handle else None
                
                result = db.add_url(url, user_id=user_id)
                if result:
                    added_count += 1
            elif isinstance(url_data, dict) and 'url' in url_data:
                # URL with metadata
                # Convert to Twitter URL if it's a Nitter URL
                url = convert_nitter_to_twitter(url_data['url'])
                
                # Extract Twitter handle and get user ID
                handle = extract_twitter_handle(url)
                
                # Use existing user_id if available, otherwise get it from the handle
                user_id = url_data.get('user_id')
                if not user_id and handle:
                    user_id = get_user_id_from_twitter_handle(handle)
                
                # Determine subtype
                subtype = determine_subtype(url_data)
                
                # Add URL to database
                result = db.add_url(
                    url,
                    description=url_data.get('description', ''),
                    url_type=url_data.get('type', 'kol'),
                    user_id=user_id,
                    subtype=subtype
                )
                
                if result:
                    added_count += 1
                    
                    # Update subtype if needed
                    if subtype:
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE url_tracking SET subtype = ? WHERE url = ?", (subtype, url))
                        conn.commit()
                        conn.close()
            else:
                logging.warning("Invalid URL format: {}".format(url_data))
        
        logging.info("Added {} URLs to the database".format(added_count))
        
        return True
    except Exception as e:
        logging.error("Error adding URLs from {}: {}".format(file_path, str(e)))
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Add URLs to the database')
    parser.add_argument('--file', type=str, required=True, help='Path to the JSON file containing URLs')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    parser.add_argument('--clear', action='store_true', help='Clear existing URLs before adding new ones')
    
    args = parser.parse_args()
    
    # Add URLs from file
    add_urls_from_file(args.file, db_path=args.db_path, clear_existing=args.clear)

if __name__ == "__main__":
    main()
