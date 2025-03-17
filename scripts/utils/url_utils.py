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

def normalize_twitter_url(url):
    """
    Normalize Twitter URL to ensure it uses twitter.com domain.
    Converts x.com and nitter.net URLs to twitter.com format.
    This is necessary because the core scraper only supports twitter.com URLs.
    """
    if not url:
        return None
    
    try:
        # Parse the URL
        parsed_url = urlparse(url)
        
        # Check if it's a Twitter, X, or Nitter URL
        if 'twitter.com' in parsed_url.netloc or 'x.com' in parsed_url.netloc or 'nitter.net' in parsed_url.netloc:
            # Extract the handle from the path
            path_parts = parsed_url.path.strip('/').split('/')
            if not path_parts or not path_parts[0]:
                return url
            
            handle = path_parts[0]
            
            # Extract the rest of the path (if any)
            rest_of_path = '/'.join(path_parts[1:]) if len(path_parts) > 1 else ''
            
            # Reconstruct the URL with twitter.com domain
            normalized_url = f"https://twitter.com/{handle}"
            if rest_of_path:
                normalized_url += f"/{rest_of_path}"
            
            # Add query parameters if present but remove ref parameters
            if parsed_url.query:
                # For test compatibility, remove ref parameters
                query_params = []
                for param in parsed_url.query.split('&'):
                    if not param.startswith('ref='):
                        query_params.append(param)
                
                if query_params:
                    normalized_url += f"?{'&'.join(query_params)}"
            
            return normalized_url
        else:
            # Not a Twitter URL, return the original URL
            return url
    except Exception as e:
        logging.error(f"Error normalizing Twitter URL {url}: {str(e)}")
        return url

def extract_twitter_handle(url):
    """Extract Twitter handle from a URL (works with twitter.com, x.com, and nitter.net)"""
    if not url:
        return None
    
    try:
        # Parse the URL
        parsed_url = urlparse(url)
        
        # Check if it's a Twitter, X, or Nitter URL
        if 'twitter.com' in parsed_url.netloc:
            domain = 'twitter.com'
        elif 'x.com' in parsed_url.netloc:
            domain = 'x.com'
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
