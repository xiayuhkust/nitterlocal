#!/usr/bin/env python3
"""
Test script to verify that normalize_twitter_url function works correctly
and properly converts x.com URLs to twitter.com format before scraping.
"""

import os
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import the functions to test
try:
    from scripts.utils.url_utils import normalize_twitter_url, extract_twitter_handle
    logging.info("Successfully imported url_utils functions")
except ImportError:
    logging.error("Could not import url_utils functions")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_normalize_twitter_url():
    """Test normalize_twitter_url function with various URL formats"""
    test_cases = [
        # Twitter.com URLs should remain unchanged
        ("https://twitter.com/cz_binance", "https://twitter.com/cz_binance"),
        ("https://twitter.com/cz_binance/", "https://twitter.com/cz_binance"),
        ("https://twitter.com/cz_binance?ref=source", "https://twitter.com/cz_binance"),
        ("https://twitter.com/cz_binance/status/1234567890", "https://twitter.com/cz_binance/status/1234567890"),
        
        # X.com URLs should be converted to twitter.com
        ("https://x.com/cz_binance", "https://twitter.com/cz_binance"),
        ("https://x.com/cz_binance/", "https://twitter.com/cz_binance"),
        ("https://x.com/cz_binance?ref=source", "https://twitter.com/cz_binance"),
        ("https://x.com/cz_binance/status/1234567890", "https://twitter.com/cz_binance/status/1234567890"),
        
        # Nitter.net URLs should be converted to twitter.com
        ("https://nitter.net/cz_binance", "https://twitter.com/cz_binance"),
        ("https://nitter.net/cz_binance/", "https://twitter.com/cz_binance"),
        
        # Invalid URLs should return the original URL
        ("https://example.com/cz_binance", "https://example.com/cz_binance"),
        
        # Empty or None URLs should return None
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
    
    logging.info(f"Passed {success_count}/{len(test_cases)} test cases for normalize_twitter_url")
    return success_count == len(test_cases)

def test_extract_twitter_handle():
    """Test extract_twitter_handle function with various URL formats"""
    test_cases = [
        # Twitter.com URLs
        ("https://twitter.com/cz_binance", "cz_binance"),
        ("https://twitter.com/cz_binance/", "cz_binance"),
        ("https://twitter.com/cz_binance?ref=source", "cz_binance"),
        ("https://twitter.com/cz_binance/status/1234567890", "cz_binance"),
        
        # X.com URLs should be normalized and then handle extracted
        ("https://x.com/cz_binance", "cz_binance"),
        ("https://x.com/cz_binance/", "cz_binance"),
        ("https://x.com/cz_binance?ref=source", "cz_binance"),
        ("https://x.com/cz_binance/status/1234567890", "cz_binance"),
        
        # Nitter.net URLs should be normalized and then handle extracted
        ("https://nitter.net/cz_binance", "cz_binance"),
        ("https://nitter.net/cz_binance/", "cz_binance"),
        
        # Invalid URLs should return None
        ("https://example.com/cz_binance", None),
        
        # Empty or None URLs should return None
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
    
    logging.info(f"Passed {success_count}/{len(test_cases)} test cases for extract_twitter_handle")
    return success_count == len(test_cases)

def test_combined_workflow():
    """Test the combined workflow of normalizing URLs and extracting handles"""
    test_cases = [
        # Twitter.com URLs
        ("https://twitter.com/cz_binance", "https://twitter.com/cz_binance", "cz_binance"),
        
        # X.com URLs should be normalized to twitter.com
        ("https://x.com/cz_binance", "https://twitter.com/cz_binance", "cz_binance"),
        
        # Nitter.net URLs should be normalized to twitter.com
        ("https://nitter.net/cz_binance", "https://twitter.com/cz_binance", "cz_binance"),
    ]
    
    success_count = 0
    for url, expected_normalized_url, expected_handle in test_cases:
        normalized_url = normalize_twitter_url(url)
        handle = extract_twitter_handle(url)
        
        if normalized_url == expected_normalized_url and handle == expected_handle:
            success_count += 1
            logging.info(f"✅ {url} -> {normalized_url} -> {handle}")
        else:
            logging.error(f"❌ {url} -> {normalized_url} (expected {expected_normalized_url}) -> {handle} (expected {expected_handle})")
    
    logging.info(f"Passed {success_count}/{len(test_cases)} test cases for combined workflow")
    return success_count == len(test_cases)

def main():
    """Main function"""
    logging.info("Testing normalize_twitter_url function...")
    normalize_test_result = test_normalize_twitter_url()
    
    logging.info("\nTesting extract_twitter_handle function...")
    handle_test_result = test_extract_twitter_handle()
    
    logging.info("\nTesting combined workflow...")
    combined_test_result = test_combined_workflow()
    
    if normalize_test_result and handle_test_result and combined_test_result:
        logging.info("\n✅ All tests passed!")
        return 0
    else:
        logging.error("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
