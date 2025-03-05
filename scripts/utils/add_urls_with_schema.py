#!/usr/bin/env python3
"""
Script to add URLs to the database.
This script adds URLs from a JSON file to the database.
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

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import the database module
from src.database.local_database import LocalDatabase
from scripts.utils.ensure_schema import ensure_schema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def extract_twitter_handle(url):
    """Extract Twitter handle from a nitter URL"""
    if not url or 'nitter.net/' not in url:
        return None
    
    try:
        # Extract the handle from the URL
        parts = url.split('nitter.net/')
        if len(parts) > 1:
            handle = parts[1].split('?')[0].strip('/')
            if handle:
                return handle.lower()
    except Exception as e:
        logging.error(f"Error extracting Twitter handle from {url}: {str(e)}")
    
    return None

def get_user_id_from_twitter_handle(handle):
    """Get user ID from Twitter handle using Twitter API or scraping"""
    if not handle:
        return None
    
    try:
        # Try to get user ID from Twitter handle using a simple scraping approach
        url = f"https://nitter.net/{handle}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logging.warning(f"Failed to fetch {url}: {response.status_code}")
            return None
        
        # Try to extract user ID from the page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for user ID in the page
        # This is a simplified approach and may not work for all cases
        # A more robust approach would be to use the Twitter API
        user_id = None
        
        # Try to find user ID in the page content
        page_text = soup.get_text()
        user_id_match = re.search(r'user_id=(\d+)', page_text)
        if user_id_match:
            user_id = user_id_match.group(1)
        
        if not user_id:
            # Try another approach - look for data attributes
            profile_div = soup.select_one('div.profile-card')
            if profile_div:
                user_id = profile_div.get('data-user-id')
        
        if not user_id:
            # As a fallback, use the handle as the user ID
            user_id = handle
        
        return user_id
        
    except Exception as e:
        logging.error(f"Error getting user ID for handle {handle}: {str(e)}")
        return None

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
    logging.info(f"Adding URLs from {file_path} to database at {db_path}")
    
    try:
        # Ensure the database schema is correct
        ensure_schema(db_path)
        
        # Load URLs from file
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if 'urls' not in data:
            logging.error(f"Invalid JSON format: {file_path}")
            return False
        
        urls = data['urls']
        logging.info(f"Found {len(urls)} URLs in {file_path}")
        
        # Initialize the database
        db = LocalDatabase(db_path=db_path)
        
        # Clear existing URLs if requested
        if clear_existing:
            logging.warning("Clearing existing URLs from the database")
            conn = db.get_connection()
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
                # Extract Twitter handle and get user ID
                handle = extract_twitter_handle(url_data)
                user_id = get_user_id_from_twitter_handle(handle) if handle else None
                
                result = db.add_url(url_data, user_id=user_id)
                if result:
                    added_count += 1
            elif isinstance(url_data, dict) and 'url' in url_data:
                # URL with metadata
                # Extract Twitter handle and get user ID
                handle = extract_twitter_handle(url_data['url'])
                
                # Use existing user_id if available, otherwise get it from the handle
                user_id = url_data.get('user_id')
                if not user_id and handle:
                    user_id = get_user_id_from_twitter_handle(handle)
                
                # Determine subtype
                subtype = determine_subtype(url_data)
                
                # Add URL to database
                result = db.add_url(
                    url_data['url'],
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
                        cursor.execute("UPDATE url_tracking SET subtype = ? WHERE url = ?", (subtype, url_data['url']))
                        conn.commit()
                        conn.close()
            else:
                logging.warning(f"Invalid URL format: {url_data}")
        
        logging.info(f"Added {added_count} URLs to the database")
        
        return True
        
    except Exception as e:
        logging.error(f"Error adding URLs from {file_path}: {str(e)}")
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
