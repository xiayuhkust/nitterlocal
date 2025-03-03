#!/usr/bin/env python3
"""
Test script for hashtag functionality.
This script tests the ability to extract, store, and query hashtags.
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
from src.twitter_client.twitter_scraper import TwitterScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_hashtag_functionality():
    """Test the hashtag functionality"""
    logging.info("Testing hashtag functionality")
    
    try:
        # Initialize the database with a test path
        db_path = 'data/test_hashtags_database.db'
        if os.path.exists(db_path):
            os.remove(db_path)
        
        logging.info(f"Creating test database at {db_path}")
        db = LocalDatabase(db_path=db_path)
        
        # Add a test URL
        test_url = 'https://twitter.com/test_account'
        db.add_url(test_url, description="Test Account", url_type="kol")
        
        # Create test tweets with hashtags
        test_tweets = []
        for i in range(3):
            tweet = {
                'tweet_id': f'test_tweet_{i}',
                'content': f'Test tweet content {i} with #test and #hashtag{i}',
                'author': 'test_account',
                'created_at': datetime.now().isoformat(),
                'likes': 10 + i,
                'retweets': 5 + i,
                'replies': 2 + i,
                'views': 100 + i * 10,
                'hashtags': ['test', f'hashtag{i}']
            }
            test_tweets.append(tweet)
        
        # Store test tweets
        stored_count = db.store_tweets(test_tweets, test_url)
        logging.info(f"Stored {stored_count} test tweets with hashtags")
        
        # Test getting tweets by hashtag
        test_hashtag_tweets = db.get_tweets_by_hashtag('test')
        logging.info(f"Retrieved {len(test_hashtag_tweets)} tweets with hashtag #test")
        assert len(test_hashtag_tweets) == 3, f"Expected 3 tweets with hashtag #test, got {len(test_hashtag_tweets)}"
        
        # Test getting popular hashtags
        popular_hashtags = db.get_popular_hashtags()
        logging.info(f"Retrieved {len(popular_hashtags)} popular hashtags")
        assert len(popular_hashtags) >= 4, f"Expected at least 4 hashtags, got {len(popular_hashtags)}"
        
        logging.info("Hashtag functionality test passed!")
        return True
        
    except Exception as e:
        logging.error(f"Error testing hashtag functionality: {str(e)}")
        return False

if __name__ == "__main__":
    test_hashtag_functionality()
