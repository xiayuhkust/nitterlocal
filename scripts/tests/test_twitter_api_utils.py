#!/usr/bin/env python3
"""
Test script to verify the Twitter API utility functions.
"""

import os
import sys
import logging

# Add the project root to the Python path
sys.path.append('/home/ubuntu/nitterlocal')

# Import the Twitter API utility functions
sys.path.append('/home/ubuntu/nitterlocal/app')
from twitter_api_utils import (
    extract_twitter_handle,
    get_user_id_from_twitter_api,
    get_user_id_from_direct_client_call,
    get_user_id_fallback
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_twitter_api_utils(handle, expected_user_id=None):
    """Test the Twitter API utility functions"""
    logging.info(f"Testing Twitter API utility functions for handle: {handle}")
    
    # Test extract_twitter_handle
    url = f"https://twitter.com/{handle}"
    extracted_handle = extract_twitter_handle(url)
    logging.info(f"Extracted handle from {url}: {extracted_handle}")
    
    # Test with x.com URL
    x_url = f"https://x.com/{handle}"
    x_extracted_handle = extract_twitter_handle(x_url)
    logging.info(f"Extracted handle from {x_url}: {x_extracted_handle}")
    
    # Test get_user_id_from_twitter_api
    api_user_id = get_user_id_from_twitter_api(handle)
    logging.info(f"User ID from Twitter API: {api_user_id}")
    
    # Test get_user_id_from_direct_client_call
    direct_user_id = get_user_id_from_direct_client_call(handle)
    logging.info(f"User ID from direct client call: {direct_user_id}")
    
    # Test get_user_id_fallback
    fallback_user_id = get_user_id_fallback(handle)
    logging.info(f"User ID from fallback method: {fallback_user_id}")
    
    # Compare with expected user ID
    if expected_user_id:
        if api_user_id == expected_user_id:
            logging.info(f"SUCCESS: API user ID matches expected: {expected_user_id}")
        else:
            logging.warning(f"WARNING: API user ID {api_user_id} does not match expected: {expected_user_id}")
        
        if direct_user_id == expected_user_id:
            logging.info(f"SUCCESS: Direct client user ID matches expected: {expected_user_id}")
        else:
            logging.warning(f"WARNING: Direct client user ID {direct_user_id} does not match expected: {expected_user_id}")
    
    return {
        "handle": handle,
        "extracted_handle": extracted_handle,
        "x_extracted_handle": x_extracted_handle,
        "api_user_id": api_user_id,
        "direct_user_id": direct_user_id,
        "fallback_user_id": fallback_user_id,
        "expected_user_id": expected_user_id
    }

def main():
    """Main function"""
    # Test with the example handle
    handle = "cz_binance"
    expected_user_id = "902926941413453824"
    
    result = test_twitter_api_utils(handle, expected_user_id)
    
    # Print the results
    print("\nTwitter API Utility Test Results:")
    print(f"Handle: {result['handle']}")
    print(f"Extracted handle from twitter.com: {result['extracted_handle']}")
    print(f"Extracted handle from x.com: {result['x_extracted_handle']}")
    print(f"User ID from Twitter API: {result['api_user_id']}")
    print(f"User ID from direct client call: {result['direct_user_id']}")
    print(f"User ID from fallback method: {result['fallback_user_id']}")
    print(f"Expected user ID: {result['expected_user_id']}")
    
    # Check if any method returned the expected user ID
    if result['api_user_id'] == expected_user_id or result['direct_user_id'] == expected_user_id:
        print(f"\nSUCCESS: At least one method returned the expected user ID: {expected_user_id}")
    else:
        print(f"\nWARNING: No method returned the expected user ID: {expected_user_id}")
        
    # Check if the fallback method returned a different user ID
    if result['fallback_user_id'] != expected_user_id:
        print(f"CONFIRMED: Fallback method returned incorrect user ID: {result['fallback_user_id']}")
    else:
        print(f"UNEXPECTED: Fallback method returned correct user ID: {result['fallback_user_id']}")

if __name__ == "__main__":
    main()
