#!/usr/bin/env python3
"""
Test script for reply functionality.
This script tests the ability to extract, store, and query reply tweets.
"""

import os
import sys
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the necessary modules
from src.database.local_database import LocalDatabase
from src.twitter_client.twitter_scraper import TwitterScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_reply_functionality():
    """Test the reply functionality"""
    logging.info("Testing reply functionality")
    
    try:
        # Initialize the database with a test path
        db_path = 'data/test_reply_database.db'
        if os.path.exists(db_path):
            os.remove(db_path)
        
        logging.info(f"Creating test database at {db_path}")
        db = LocalDatabase(db_path=db_path)
        
        # Add a test URL
        test_url = 'https://twitter.com/elonmusk'
        db.add_url(test_url, description="Elon Musk", url_type="kol")
        
        # Initialize the Twitter scraper
        scraper = TwitterScraper()
        
        # Test scraping tweets with replies
        logging.info("Testing tweet and reply scraping")
        tweets_with_replies = scraper.scrape_url_with_replies(test_url, max_tweets=10)
        
        # Count regular tweets and replies
        regular_tweets = [t for t in tweets_with_replies if not t.get('is_reply')]
        reply_tweets = [t for t in tweets_with_replies if t.get('is_reply')]
        
        logging.info(f"Extracted {len(regular_tweets)} regular tweets and {len(reply_tweets)} reply tweets")
        
        # Store the tweets in the database
        db.store_tweets(tweets_with_replies, test_url)
        
        # Test querying all replies
        logging.info("Testing querying all replies")
        all_replies = db.get_replies(limit=100)
        logging.info(f"Found {len(all_replies)} replies in the database")
        
        # Test querying replies by user
        logging.info("Testing querying replies by user")
        user_id = None
        for tweet in tweets_with_replies:
            if tweet.get('user_id'):
                user_id = tweet.get('user_id')
                break
        
        if user_id:
            user_replies = db.get_replies_by_user(user_id=user_id, limit=100)
            logging.info(f"Found {len(user_replies)} replies by user ID {user_id}")
        
        # Test querying replies by author
        author = "elonmusk"
        author_replies = db.get_replies_by_user(author=author, limit=100)
        logging.info(f"Found {len(author_replies)} replies by author {author}")
        
        # Test querying replies to a tweet
        if reply_tweets:
            in_reply_to_status_id = reply_tweets[0].get('in_reply_to_status_id')
            if in_reply_to_status_id:
                logging.info(f"Testing querying replies to tweet {in_reply_to_status_id}")
                replies_to_tweet = db.get_replies_to_tweet(in_reply_to_status_id, limit=100)
                logging.info(f"Found {len(replies_to_tweet)} replies to tweet {in_reply_to_status_id}")
        
        # Test querying conversation
        if reply_tweets:
            conversation_id = reply_tweets[0].get('conversation_id')
            if conversation_id:
                logging.info(f"Testing querying conversation {conversation_id}")
                conversation = db.get_conversation(conversation_id, limit=100)
                logging.info(f"Found {len(conversation)} tweets in conversation {conversation_id}")
        
        # Test getting reply statistics
        if user_id:
            logging.info(f"Testing reply statistics for user ID {user_id}")
            reply_stats = db.get_reply_statistics(user_id=user_id)
            logging.info(f"Reply statistics: {reply_stats}")
        
        logging.info("Reply functionality test completed successfully")
        return True
        
    except Exception as e:
        logging.error(f"Error testing reply functionality: {str(e)}")
        return False

if __name__ == "__main__":
    test_reply_functionality()
