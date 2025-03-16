"""
Centralized utilities for Twitter handle extraction and validation.
"""

import re
import logging
from urllib.parse import urlparse
from typing import Optional

def extract_twitter_handle(url: str) -> Optional[str]:
    """
    Extract Twitter handle from a URL (works with both twitter.com and x.com)
    
    Args:
        url: Twitter URL to process
        
    Returns:
        Extracted Twitter handle or None if extraction fails
    """
    if not url:
        return None
    
    try:
        # Parse the URL
        parsed_url = urlparse(url)
        
        # Check if it's a Twitter URL
        if 'twitter.com' in parsed_url.netloc:
            domain = 'twitter.com'
        elif 'x.com' in parsed_url.netloc:
            domain = 'x.com'
        else:
            return None
        
        # Extract the handle from the path
        path_parts = parsed_url.path.strip('/').split('/')
        if not path_parts:
            return None
        
        handle = path_parts[0]
        
        # Clean up the handle (remove @ if present, etc.)
        handle = handle.lower()
        if handle.startswith('@'):
            handle = handle[1:]
            
        # Validate the handle format
        if re.match(r'^[a-zA-Z0-9_]{1,15}$', handle):
            return handle
        else:
            logging.warning(f"Invalid Twitter handle format: {handle}")
            return None
            
    except Exception as e:
        logging.error(f"Error extracting Twitter handle from {url}: {str(e)}")
        return None

def validate_twitter_handle(handle: str) -> bool:
    """
    Validate a Twitter handle format
    
    Args:
        handle: Twitter handle to validate
        
    Returns:
        True if the handle is valid, False otherwise
    """
    if not handle:
        return False
        
    # Remove @ if present
    if handle.startswith('@'):
        handle = handle[1:]
        
    # Check if the handle matches Twitter's requirements
    return bool(re.match(r'^[a-zA-Z0-9_]{1,15}$', handle))
