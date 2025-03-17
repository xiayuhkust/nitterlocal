#!/usr/bin/env python3
"""
Test script to verify that extract_twitter_handle function works with both twitter.com and x.com domains,
and that x.com URLs are properly converted to twitter.com format before scraping.
"""

import os
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import the functions to test
from scripts.utils.url_utils import extract_twitter_handle, normalize_twitter_url
from app.twitter_api_utils import get_user_id_from_twitter_api, get_user_id_from_direct_client_call

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_extract_twitter_handle():
    """Test extract_twitter_handle function with various URL formats"""
    test_cases = [
        # Twitter.com URLs
        ("https://twitter.com/cz_binance", "cz_binance"),
        ("https://twitter.com/cz_binance/", "cz_binance"),
        ("https://twitter.com/cz_binance?ref=source", "cz_binance"),
        ("https://twitter.com/cz_binance/status/1234567890", "cz_binance"),
        
        # X.com URLs
        ("https://x.com/cz_binance", "cz_binance"),
        ("https://x.com/cz_binance/", "cz_binance"),
        ("https://x.com/cz_binance?ref=source", "cz_binance"),
        ("https://x.com/cz_binance/status/1234567890", "cz_binance"),
        
        # Nitter.net URLs
        ("https://nitter.net/cz_binance", "cz_binance"),
        ("https://nitter.net/cz_binance/", "cz_binance"),
        ("https://nitter.net/cz_binance?ref=source", "cz_binance"),
        ("https://nitter.net/cz_binance/status/1234567890", "cz_binance"),
        
        # Invalid URLs
        ("https://example.com/cz_binance", None),
        ("", None),
        (None, None)
    ]
    
    success_count = 0
    for url, expected_handle in test_cases:
        handle = extract_twitter_handle(url)
        if handle == expected_handle:
            success_count += 1
            logging.info(f"✅ {url} -> {handle}")
        else:
            logging.error(f"❌ {url} -> {handle} (expected {expected_handle})")
    
    logging.info(f"Passed {success_count}/{len(test_cases)} test cases")
    return success_count == len(test_cases)

def test_normalize_twitter_url():
    """Test normalize_twitter_url function to ensure x.com URLs are converted to twitter.com format"""
    test_cases = [
        # X.com URLs should be converted to twitter.com
        ("https://x.com/cz_binance", "https://twitter.com/cz_binance"),
        ("https://x.com/cz_binance/", "https://twitter.com/cz_binance"),
        ("https://x.com/cz_binance?ref=source", "https://twitter.com/cz_binance"),
        ("https://x.com/cz_binance/status/1234567890", "https://twitter.com/cz_binance/status/1234567890"),
        
        # Twitter.com URLs should remain unchanged
        ("https://twitter.com/cz_binance", "https://twitter.com/cz_binance"),
        ("https://twitter.com/cz_binance/", "https://twitter.com/cz_binance"),
        ("https://twitter.com/cz_binance?ref=source", "https://twitter.com/cz_binance"),
        ("https://twitter.com/cz_binance/status/1234567890", "https://twitter.com/cz_binance/status/1234567890"),
        
        # Nitter.net URLs should be converted to twitter.com
        ("https://nitter.net/cz_binance", "https://twitter.com/cz_binance"),
        
        # Invalid URLs should return None
        ("https://example.com/cz_binance", None),
        ("", None),
        (None, None)
    ]
    
    success_count = 0
    for url, expected_normalized_url in test_cases:
        normalized_url = normalize_twitter_url(url)
        if normalized_url == expected_normalized_url:
            success_count += 1
            logging.info(f"✅ {url} -> {normalized_url}")
        else:
            logging.error(f"❌ {url} -> {normalized_url} (expected {expected_normalized_url})")
    
    logging.info(f"Passed {success_count}/{len(test_cases)} test cases")
    return success_count == len(test_cases)

def test_user_id_extraction():
    """Test user ID extraction with both twitter.com and x.com URLs"""
    test_cases = [
        ("https://twitter.com/cz_binance", "902926941413453824"),
        ("https://x.com/cz_binance", "902926941413453824")
    ]
    
    success_count = 0
    for url, expected_id in test_cases:
        # First normalize the URL to ensure x.com is converted to twitter.com
        normalized_url = normalize_twitter_url(url)
        handle = extract_twitter_handle(normalized_url)
        
        logging.info(f"Testing user ID extraction for {url} (normalized to {normalized_url})")
        user_id = get_user_id_from_direct_client_call(handle)
        
        if user_id == expected_id:
            success_count += 1
            logging.info(f"✅ {url} -> {user_id}")
        else:
            logging.warning(f"❓ {url} -> {user_id} (expected {expected_id})")
            
            # Try fallback method
            logging.info(f"Trying API method for {handle}...")
            api_user_id = get_user_id_from_twitter_api(handle)
            logging.info(f"API method result: {api_user_id}")
            
            if api_user_id == expected_id:
                success_count += 1
                logging.info(f"✅ {url} -> {api_user_id} (using API method)")
            else:
                logging.error(f"❌ {url} -> Failed with both methods")
    
    logging.info(f"Passed {success_count}/{len(test_cases)} test cases")
    return success_count == len(test_cases)

def main():
    """Main function"""
    logging.info("Testing extract_twitter_handle function...")
    handle_test_result = test_extract_twitter_handle()
    
    logging.info("\nTesting normalize_twitter_url function...")
    normalize_test_result = test_normalize_twitter_url()
    
    logging.info("\nTesting user ID extraction...")
    user_id_test_result = test_user_id_extraction()
    
    if handle_test_result and normalize_test_result and user_id_test_result:
        logging.info("\n✅ All tests passed!")
        return 0
    else:
        logging.error("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
