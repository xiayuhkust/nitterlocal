#!/usr/bin/env python3
"""
Test script for user ID functionality in tweets.
This script tests the ability to extract, store, and query user IDs in tweets.
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

def test_tweets_user_id_functionality():
    """Test the user ID functionality in tweets"""
    logging.info("Testing user ID functionality in tweets")
    
    try:
        # Initialize the database with a test path
        db_path = 'data/test_tweets_user_id_database.db'
        if os.path.exists(db_path):
            os.remove(db_path)
        
        logging.info(f"Creating test database at {db_path}")
        db = LocalDatabase(db_path=db_path)
        
        # Add a test URL
        test_url = 'https://twitter.com/elonmusk'
        user_id = '44196397'  # Elon Musk's Twitter user ID
        db.add_url(test_url, description="Elon Musk", url_type="kol", user_id=user_id)
        
        # Create some test tweets with user_id
        test_tweets = [
            {
                'tweet_id': 'tweet1',
                'content': 'Test tweet 1',
                'author': 'elonmusk',
                'created_at': datetime.now().isoformat(),
                'likes': 100,
                'retweets': 50,
                'replies': 20,
                'views': 1000,
                'source_url': test_url,
                'user_id': user_id,
                'hashtags': ['test', 'tweet']
            },
            {
                'tweet_id': 'tweet2',
                'content': 'Test tweet 2',
                'author': 'elonmusk',
                'created_at': datetime.now().isoformat(),
                'likes': 200,
                'retweets': 100,
                'replies': 40,
                'views': 2000,
                'source_url': test_url,
                'user_id': user_id,
                'hashtags': ['test', 'tweet']
            }
        ]
        
        # Store the test tweets
        db.store_tweets(test_tweets, test_url)
        
        # Get the tweets by user_id
        tweets_by_user_id = db.get_tweets(user_id=user_id)
        
        # Verify that tweets were stored with the correct user_id
        if len(tweets_by_user_id) == 0:
            logging.error(f"No tweets found for user ID {user_id}")
            return False
        
        # Verify that all tweets have the correct user_id
        for tweet in tweets_by_user_id:
            if tweet['user_id'] != user_id:
                logging.error(f"Tweet has incorrect user_id: {tweet['user_id']} != {user_id}")
                return False
        
        logging.info(f"Found {len(tweets_by_user_id)} tweets for user ID {user_id}")
        
        # Verify that tweets can still be retrieved by source_url
        tweets_by_url = db.get_tweets(source_url=test_url)
        if len(tweets_by_url) == 0:
            logging.error(f"No tweets found for URL {test_url}")
            return False
        
        logging.info(f"Found {len(tweets_by_url)} tweets for URL {test_url}")
        
        # Verify that the tweets retrieved by user_id and by URL are the same
        if len(tweets_by_user_id) != len(tweets_by_url):
            logging.error(f"Different number of tweets retrieved by user_id ({len(tweets_by_user_id)}) and URL ({len(tweets_by_url)})")
            return False
        
        # Test with real Twitter scraper if possible
        try:
            # Initialize the Twitter scraper
            scraper = TwitterScraper()
            
            # Scrape the URL (this will only work if Twitter credentials are set up)
            real_tweets = scraper.scrape_url(test_url, max_tweets=2)
            
            if real_tweets:
                # Store the real tweets
                db.store_tweets(real_tweets, test_url)
                
                # Verify that the real tweets have user_id
                tweets_by_user_id = db.get_tweets(user_id=user_id)
                for tweet in tweets_by_user_id:
                    if tweet['user_id'] != user_id:
                        logging.warning(f"Real tweet has incorrect user_id: {tweet['user_id']} != {user_id}")
                
                logging.info(f"Stored and verified {len(real_tweets)} real tweets")
        except Exception as e:
            logging.warning(f"Could not test with real Twitter scraper: {str(e)}")
        
        logging.info("User ID functionality in tweets test passed!")
        return True
        
    except Exception as e:
        logging.error(f"Error testing user ID functionality in tweets: {str(e)}")
        return False

if __name__ == "__main__":
    test_tweets_user_id_functionality()
