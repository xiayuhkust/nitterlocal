#!/usr/bin/env python3
"""
Test script for the TwitterScraper.
This script tests that the TwitterScraper can extract usernames from Twitter URLs.
"""

import os
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Import the TwitterScraper
from src.twitter_client.twitter_scraper import TwitterScraper

def test_extract_username():
    """Test that the TwitterScraper can extract usernames from Twitter URLs"""
    scraper = TwitterScraper()
    
    # Test with Twitter URLs
    twitter_urls = [
        "https://twitter.com/cz_binance",
        "https://twitter.com/VitalikButerin",
        "https://twitter.com/SBF_FTX"
    ]
    
    for url in twitter_urls:
        username = scraper.extract_username_from_url(url)
        logging.info(f"URL: {url}, Username: {username}")
        
        if not username:
            logging.error(f"Failed to extract username from {url}")
            return False
    
    logging.info("Successfully extracted usernames from Twitter URLs")
    return True

def main():
    """Main function"""
    if test_extract_username():
        logging.info("TwitterScraper tests passed")
        return 0
    else:
        logging.error("TwitterScraper tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
