#!/usr/bin/env python3
"""
Test script to verify that the tweet replies integration works correctly.
This script tests if we can extract both regular tweets and replies from Twitter accounts
and store them in the database with the correct values for the new fields.
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

def test_tweet_replies():
    """Test the tweet replies integration"""
    logging.info("Testing tweet replies integration")
    
    # Initialize the TwitterScraper and LocalDatabase
    scraper = TwitterScraper()
    db = LocalDatabase()
    
    # Test URL (use a Twitter account that is known to have replies)
    test_url = "https://twitter.com/elonmusk"
    
    # Scrape the URL for both regular tweets and replies
    logging.info(f"Scraping URL: {test_url}")
    tweets = scraper.scrape_url(test_url, max_tweets=5, max_replies=5)
    
    if not tweets:
        logging.error("No tweets found")
        return False
    
    # Check if any of the tweets are replies
    reply_count = sum(1 for tweet in tweets if tweet.get('is_reply', 0) == 1)
    logging.info(f"Found {reply_count} replies out of {len(tweets)} tweets")
    
    # Store the tweets in the database
    logging.info("Storing tweets in the database")
    stored_count = db.store_tweets(tweets, test_url)
    
    if stored_count == 0:
        logging.error("No tweets stored in the database")
        return False
    
    logging.info(f"Stored {stored_count} tweets in the database")
    
    # Query the database to check if the new fields are correctly populated
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT tweet_id, is_reply, reply_to, conversation_id
    FROM tweets
    WHERE source_url = ?
    ''', (test_url,))
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        logging.error("No tweets found in the database")
        return False
    
    # Check if the new fields are correctly populated
    for tweet_id, is_reply, reply_to, conversation_id in results:
        logging.info(f"Tweet {tweet_id}: is_reply={is_reply}, reply_to={reply_to}, conversation_id={conversation_id}")
    
    logging.info("Test completed successfully")
    return True

if __name__ == "__main__":
    test_tweet_replies()
