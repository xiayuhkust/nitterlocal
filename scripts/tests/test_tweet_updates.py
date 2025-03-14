#!/usr/bin/env python3
"""
Test script for tweet update functionality.
This script tests the ability to update existing tweets with new metadata.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_tweet_updates():
    """Test the tweet update functionality"""
    logging.info("Testing tweet update functionality")
    
    try:
        # Initialize the database with a test path
        db_path = 'data/test_update_database.db'
        if os.path.exists(db_path):
            os.remove(db_path)
        
        logging.info(f"Creating test database at {db_path}")
        db = LocalDatabase(db_path=db_path)
        
        # Add a test URL
        test_url = 'https://twitter.com/test_account'
        db.add_url(test_url, description="Test Account", url_type="kol")
        
        # Create initial test tweets
        initial_tweets = []
        for i in range(3):
            tweet = {
                'tweet_id': f'test_tweet_{i}',
                'content': f'Test tweet content {i}',
                'author': 'test_account',
                'created_at': datetime.now().isoformat(),
                'likes': 10 + i,
                'retweets': 5 + i,
                'replies': 2 + i,
                'views': 100 + i * 10
            }
            initial_tweets.append(tweet)
        
        # Store initial tweets
        stored_count = db.store_tweets(initial_tweets, test_url)
        logging.info(f"Stored {stored_count} initial tweets")
        
        # Retrieve and verify initial tweets
        initial_stored_tweets = db.get_tweets(source_url=test_url)
        logging.info(f"Retrieved {len(initial_stored_tweets)} initial tweets")
        
        for i, tweet in enumerate(initial_stored_tweets):
            logging.info(f"Initial Tweet {i}: ID={tweet['tweet_id']}, Likes={tweet['likes']}, Retweets={tweet['retweets']}")
        
        # Create updated test tweets with same IDs but different metadata
        updated_tweets = []
        for i in range(3):
            tweet = {
                'tweet_id': f'test_tweet_{i}',
                'content': f'Test tweet content {i}',
                'author': 'test_account',
                'created_at': datetime.now().isoformat(),
                'likes': 20 + i,  # Increased likes
                'retweets': 10 + i,  # Increased retweets
                'replies': 5 + i,  # Increased replies
                'views': 200 + i * 10  # Increased views
            }
            updated_tweets.append(tweet)
        
        # Store updated tweets (should update existing ones)
        updated_count = db.store_tweets(updated_tweets, test_url)
        logging.info(f"Processed {updated_count} updated tweets")
        
        # Retrieve and verify updated tweets
        updated_stored_tweets = db.get_tweets(source_url=test_url)
        logging.info(f"Retrieved {len(updated_stored_tweets)} updated tweets")
        
        for i, tweet in enumerate(updated_stored_tweets):
            logging.info(f"Updated Tweet {i}: ID={tweet['tweet_id']}, Likes={tweet['likes']}, Retweets={tweet['retweets']}")
            
            # Verify that metadata was updated
            assert tweet['likes'] == 20 + i, f"Likes not updated for tweet {i}"
            assert tweet['retweets'] == 10 + i, f"Retweets not updated for tweet {i}"
            assert tweet['replies'] == 5 + i, f"Replies not updated for tweet {i}"
            assert tweet['views'] == 200 + i * 10, f"Views not updated for tweet {i}"
        
        logging.info("Tweet update functionality test passed!")
        return True
        
    except Exception as e:
        logging.error(f"Error testing tweet updates: {str(e)}")
        return False

if __name__ == "__main__":
    test_tweet_updates()
