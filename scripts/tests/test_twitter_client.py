#!/usr/bin/env python3
"""
Test script for the Twitter client implementation.
This script tests the Twitter client's ability to extract tweets from a Twitter account.
"""

import os
import sys
import logging
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the Twitter scraper
from src.twitter_client.twitter_scraper import TwitterScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_twitter_client():
    """Test the Twitter client implementation"""
    logging.info("Testing Twitter client implementation")
    
    try:
        # Initialize the Twitter scraper
        scraper = TwitterScraper()
        
        # Test URLs
        test_urls = [
            'https://twitter.com/0xPolygon',
            'https://twitter.com/elonmusk'
        ]
        
        for url in test_urls:
            logging.info(f"Testing URL: {url}")
            
            # Extract username from URL
            username = scraper.extract_username_from_url(url)
            logging.info(f"Extracted username: {username}")
            
            # Scrape tweets from URL
            tweets = scraper.scrape_url(url, max_tweets=10)
            
            if tweets:
                logging.info(f"Successfully extracted {len(tweets)} tweets from {url}")
                
                # Save tweets to a JSON file for inspection
                output_file = f"{username}_test_tweets.json"
                with open(output_file, 'w') as f:
                    json.dump(tweets, f, indent=2)
                
                logging.info(f"Saved tweets to {output_file}")
                
                # Print the first tweet
                if len(tweets) > 0:
                    logging.info(f"First tweet: {tweets[0]['content'][:100]}...")
            else:
                logging.warning(f"No tweets extracted from {url}")
        
        logging.info("Twitter client implementation tests completed")
        
    except Exception as e:
        logging.error(f"Error testing Twitter client: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    test_twitter_client()
