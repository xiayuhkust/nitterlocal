#!/usr/bin/env python3
"""
Test script to verify the Twitter user ID extraction methods.
"""

import os
import sys
import logging

# Add the project root to the Python path
sys.path.append('/home/ubuntu/nitterlocal')

# Import the TwitterScraper class
from src.twitter_client.twitter_scraper import TwitterScraper

# Import the twitter_utils functions
sys.path.append('/home/ubuntu/nitterlocal/app')
from twitter_utils import get_user_id_from_twitter_handle, extract_twitter_handle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_twitter_user_id_extraction(handle):
    """Test different methods of Twitter user ID extraction"""
    logging.info(f"Testing Twitter user ID extraction for handle: {handle}")
    
    # Method 1: Using twitter_utils.get_user_id_from_twitter_handle (current method)
    try:
        utils_user_id = get_user_id_from_twitter_handle(handle)
        logging.info(f"Method 1 (twitter_utils): {utils_user_id}")
    except Exception as e:
        logging.error(f"Error with Method 1: {str(e)}")
        utils_user_id = None
    
    # Method 2: Using TwitterScraper.extract_user_id_from_handle (correct method)
    try:
        scraper = TwitterScraper()
        scraper_user_id = scraper.extract_user_id_from_handle(handle)
        logging.info(f"Method 2 (TwitterScraper): {scraper_user_id}")
    except Exception as e:
        logging.error(f"Error with Method 2: {str(e)}")
        scraper_user_id = None
    
    # Compare the results
    if utils_user_id == scraper_user_id:
        logging.info(f"Both methods returned the same user ID: {utils_user_id}")
    else:
        logging.warning(f"Methods returned different user IDs:")
        logging.warning(f"  Method 1 (twitter_utils): {utils_user_id}")
        logging.warning(f"  Method 2 (TwitterScraper): {scraper_user_id}")
    
    return {
        "handle": handle,
        "utils_user_id": utils_user_id,
        "scraper_user_id": scraper_user_id
    }

def main():
    """Main function"""
    # Test with the example handle
    handle = "cz_binance"
    result = test_twitter_user_id_extraction(handle)
    
    # Print the results
    print("\nTwitter User ID Extraction Test Results:")
    print(f"Handle: {result['handle']}")
    print(f"Method 1 (twitter_utils): {result['utils_user_id']}")
    print(f"Method 2 (TwitterScraper): {result['scraper_user_id']}")
    
    # Check if the scraper method returned the expected user ID
    expected_user_id = "902926941413453824"
    if result['scraper_user_id'] == expected_user_id:
        print(f"\nSUCCESS: TwitterScraper returned the expected user ID: {expected_user_id}")
    else:
        print(f"\nWARNING: TwitterScraper returned {result['scraper_user_id']}, expected {expected_user_id}")
    
    # Check if the utils method returned the incorrect user ID
    if result['utils_user_id'] != expected_user_id:
        print(f"CONFIRMED: twitter_utils returned incorrect user ID: {result['utils_user_id']}")
    else:
        print(f"UNEXPECTED: twitter_utils returned correct user ID: {result['utils_user_id']}")

if __name__ == "__main__":
    main()
