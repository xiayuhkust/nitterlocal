#!/usr/bin/env python3
"""
Test script for user ID functionality.
This script tests the ability to extract, store, and query user IDs.
"""

import os
import sys
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the database module
from src.database.local_database import LocalDatabase
from src.twitter_client.twitter_scraper import TwitterScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_user_id_functionality():
    """Test the user ID functionality"""
    logging.info("Testing user ID functionality")
    
    try:
        # Initialize the database with a test path
        db_path = 'data/test_user_id_database.db'
        if os.path.exists(db_path):
            os.remove(db_path)
        
        logging.info(f"Creating test database at {db_path}")
        db = LocalDatabase(db_path=db_path)
        
        # Add a test URL
        test_url = 'https://twitter.com/elonmusk'
        db.add_url(test_url, description="Elon Musk", url_type="kol")
        
        # Initialize the Twitter scraper
        scraper = TwitterScraper()
        
        # Scrape the URL
        tweets = scraper.scrape_url(test_url, max_tweets=5)
        
        # Check if the URL has a user ID
        urls = db.get_urls()
        for url_data in urls:
            if url_data['url'] == test_url:
                if url_data.get('user_id'):
                    logging.info(f"URL {test_url} has user ID: {url_data['user_id']}")
                else:
                    logging.warning(f"URL {test_url} does not have a user ID")
        
        # Test getting URL by user ID
        for url_data in urls:
            if url_data.get('user_id'):
                user_id = url_data['user_id']
                url_by_id = db.get_url_by_user_id(user_id)
                if url_by_id:
                    logging.info(f"Found URL by user ID {user_id}: {url_by_id['url']}")
                else:
                    logging.warning(f"Could not find URL by user ID {user_id}")
        
        logging.info("User ID functionality test completed")
        return True
        
    except Exception as e:
        logging.error(f"Error testing user ID functionality: {str(e)}")
        return False

if __name__ == "__main__":
    test_user_id_functionality()
