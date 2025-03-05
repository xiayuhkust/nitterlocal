#!/usr/bin/env python3
"""
URL utility functions.
This module provides utility functions for working with URLs.
"""

import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def convert_nitter_to_twitter(url):
    """Convert a nitter URL to a Twitter URL"""
    if not url or 'nitter.net/' not in url:
        return url
    
    try:
        # Replace nitter.net with twitter.com
        return url.replace('nitter.net/', 'twitter.com/')
    except Exception as e:
        logging.error(f"Error converting URL {url}: {str(e)}")
        return url

def extract_twitter_handle(url):
    """Extract Twitter handle from a URL (works with both nitter.net and twitter.com)"""
    if not url:
        return None
    
    try:
        # Parse the URL
        parsed_url = urlparse(url)
        
        # Check if it's a Twitter or Nitter URL
        if 'twitter.com' in parsed_url.netloc:
            domain = 'twitter.com'
        elif 'nitter.net' in parsed_url.netloc:
            domain = 'nitter.net'
        else:
            return None
        
        # Extract the handle from the path
        path_parts = parsed_url.path.strip('/').split('/')
        if not path_parts:
            return None
        
        handle = path_parts[0]
        return handle.lower()
    except Exception as e:
        logging.error(f"Error extracting Twitter handle from {url}: {str(e)}")
        return None
