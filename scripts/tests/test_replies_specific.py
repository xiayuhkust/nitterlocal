#!/usr/bin/env python3
"""
Test script to specifically verify that the tweet replies integration works correctly.
This script tests if we can extract replies from Twitter accounts and store them in the database
with the correct values for the new fields.
"""

import os
import sys
import logging
import sqlite3
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the required modules
from src.twitter_client.twitter_scraper import TwitterScraper
from src.database.local_database import LocalDatabase

def test_tweet_replies_specific():
    """Test the tweet replies integration with accounts known to have replies"""
    logging.info("Testing tweet replies integration with specific accounts")
    
    # Initialize the TwitterScraper and LocalDatabase
    scraper = TwitterScraper()
    db = LocalDatabase()
    
    # Test URLs (use Twitter accounts that are known to have replies)
    test_urls = [
        "https://twitter.com/binance",
        "https://twitter.com/coinbase",
        "https://twitter.com/krakenfx"
    ]
    
    for test_url in test_urls:
        logging.info(f"Testing URL: {test_url}")
        
        # Scrape the URL for both regular tweets and replies
        logging.info(f"Scraping URL: {test_url}")
        tweets = scraper.scrape_url(test_url, max_tweets=5, max_replies=15)
        
        if not tweets:
            logging.error(f"No tweets found for {test_url}")
            continue
        
        # Check if any of the tweets are replies
        reply_count = sum(1 for tweet in tweets if tweet.get('is_reply', 0) == 1)
        logging.info(f"Found {reply_count} replies out of {len(tweets)} tweets")
        
        if reply_count == 0:
            logging.warning(f"No replies found for {test_url}")
            continue
        
        # Store the tweets in the database
        logging.info("Storing tweets in the database")
        stored_count = db.store_tweets(tweets, test_url)
        
        if stored_count == 0:
            logging.error("No tweets stored in the database")
            continue
        
        logging.info(f"Stored {stored_count} tweets in the database")
        
        # Query the database to check if the new fields are correctly populated
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT tweet_id, is_reply, reply_to, conversation_id
        FROM tweets
        WHERE source_url = ? AND is_reply = 1
        ''', (test_url,))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            logging.error(f"No replies found in the database for {test_url}")
            continue
        
        # Check if the new fields are correctly populated
        logging.info(f"Found {len(results)} replies in the database for {test_url}")
        for tweet_id, is_reply, reply_to, conversation_id in results:
            logging.info(f"Reply tweet {tweet_id}: is_reply={is_reply}, reply_to={reply_to}, conversation_id={conversation_id}")
        
        # Test successful for this URL
        logging.info(f"Test completed successfully for {test_url}")
        return True
    
    logging.error("No replies found for any of the test URLs")
    return False

if __name__ == "__main__":
    test_tweet_replies_specific()
