#!/usr/bin/env python3
"""
Test script for the database implementation.
This script tests the database module's ability to store and retrieve tweets.
"""

import os
import sys
import logging
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the database module
from src.database.local_database import LocalDatabase
from src.database.url_manager import URLManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_database():
    """Test the database implementation"""
    logging.info("Testing database implementation")
    
    try:
        # Initialize the database with a test path
        db_path = 'data/test_database.db'
        if os.path.exists(db_path):
            os.remove(db_path)
        
        logging.info(f"Creating test database at {db_path}")
        db = LocalDatabase(db_path=db_path)
        url_manager = URLManager(db_path=db_path)
        
        # Test URL management
        logging.info("Testing URL management")
        
        # Add URLs
        urls_to_add = [
            ('https://twitter.com/0xPolygon', 'Polygon', 'kol'),
            ('https://twitter.com/elonmusk', 'Elon Musk', 'kol'),
            ('https://twitter.com/vitalikbuterin', 'Vitalik Buterin', 'kol')
        ]
        
        for url, description, url_type in urls_to_add:
            result = db.add_url(url, description=description, url_type=url_type)
            logging.info(f"Added URL {url}: {result}")
        
        # Get URLs
        urls = db.get_urls(status='active')
        logging.info(f"Found {len(urls)} active URLs")
        
        # Test URL status update
        url_to_update = 'https://twitter.com/0xPolygon'
        result = url_manager.update_url_status(url_to_update, 'processing')
        logging.info(f"Updated URL status for {url_to_update}: {result}")
        
        # Test tweet storage
        logging.info("Testing tweet storage")
        
        # Create test tweets
        test_tweets = []
        for i in range(5):
            tweet = {
                'tweet_id': f'123456789{i}',
                'content': f'Test tweet content {i}',
                'author': '0xPolygon',
                'created_at': datetime.now().isoformat(),
                'likes': 10 + i,
                'retweets': 5 + i,
                'replies': 2 + i,
                'views': 100 + i * 10
            }
            test_tweets.append(tweet)
        
        # Store tweets
        stored_count = db.store_tweets(test_tweets, 'https://twitter.com/0xPolygon')
        logging.info(f"Stored {stored_count} tweets for 0xPolygon")
        
        # Create more test tweets for another URL
        more_test_tweets = []
        for i in range(3):
            tweet = {
                'tweet_id': f'987654321{i}',
                'content': f'Another test tweet content {i}',
                'author': 'elonmusk',
                'created_at': datetime.now().isoformat(),
                'likes': 100 + i,
                'retweets': 50 + i,
                'replies': 20 + i,
                'views': 1000 + i * 100
            }
            more_test_tweets.append(tweet)
        
        # Store more tweets
        stored_count = db.store_tweets(more_test_tweets, 'https://twitter.com/elonmusk')
        logging.info(f"Stored {stored_count} tweets for elonmusk")
        
        # Test tweet retrieval
        logging.info("Testing tweet retrieval")
        
        # Get tweets for a specific URL
        polygon_tweets = db.get_tweets(source_url='https://twitter.com/0xPolygon')
        logging.info(f"Retrieved {len(polygon_tweets)} tweets for 0xPolygon")
        
        # Get tweets for another URL
        elon_tweets = db.get_tweets(source_url='https://twitter.com/elonmusk')
        logging.info(f"Retrieved {len(elon_tweets)} tweets for elonmusk")
        
        # Get all tweets
        all_tweets = db.get_tweets()
        logging.info(f"Retrieved {len(all_tweets)} tweets in total")
        
        # Test URL tweet count update
        url_manager.update_tweet_count('https://twitter.com/0xPolygon', 5)
        url_manager.update_last_scraped('https://twitter.com/0xPolygon')
        
        # Test statistics generation
        logging.info("Testing statistics generation")
        stats = db.generate_stats()
        logging.info(f"Statistics: {stats}")
        
        # Save statistics to a file for inspection
        with open('data/test_stats.json', 'w') as f:
            json.dump(stats, f, indent=2)
        
        logging.info("Database implementation tests completed successfully")
        
    except Exception as e:
        logging.error(f"Error testing database: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    test_database()
