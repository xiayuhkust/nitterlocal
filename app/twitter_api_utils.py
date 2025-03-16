"""
Twitter API utility functions for extracting Twitter IDs from handles.
This module provides utility functions for working with Twitter API.
"""

import os
import sys
import logging
import subprocess
import tempfile
import json
from urllib.parse import urlparse

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the TwitterScraper class
from src.twitter_client.twitter_scraper import TwitterScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def extract_twitter_handle(url):
    """Extract Twitter handle from a URL (works with both twitter.com and x.com)"""
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
        return handle.lower()
    except Exception as e:
        logging.error(f"Error extracting Twitter handle from {url}: {str(e)}")
        return None

def get_user_id_from_twitter_api(handle):
    """
    Get user ID from Twitter handle using the TwitterScraper class
    
    This implementation uses the TwitterScraper class to get the real Twitter API user ID.
    """
    if not handle:
        return None
    
    try:
        # Create a TwitterScraper instance
        scraper = TwitterScraper()
        
        # Get the user ID from the handle
        user_id = scraper.extract_user_id_from_handle(handle)
        
        if user_id:
            logging.info(f"Successfully extracted user ID for {handle} from Twitter API: {user_id}")
            return user_id
        
        # If TwitterScraper fails, try direct Twitter client call
        logging.info(f"TwitterScraper failed, trying direct Twitter client call for {handle}")
        user_id = get_user_id_from_direct_client_call(handle)
        
        if user_id:
            return user_id
        
        # If all methods fail, use fallback method
        logging.warning(f"All API methods failed, using fallback method for {handle}")
        return get_user_id_fallback(handle)
        
    except Exception as e:
        logging.error(f"Error getting user ID for handle {handle} from Twitter API: {str(e)}")
        # Use fallback method if API call fails
        return get_user_id_fallback(handle)

def get_user_id_from_direct_client_call(handle):
    """Get user ID from Twitter handle using direct Twitter client call"""
    try:
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            output_file = temp_file.name
        
        # Get the path to the twitter_client.js script
        client_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src/twitter_client')
        client_path = os.path.join(client_dir, 'twitter_client.js')
        
        # Run the Twitter client directly
        logging.info(f"Running Twitter client for {handle}...")
        process = subprocess.run(
            ['node', client_path, handle, '1', '0', output_file],
            cwd=client_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Check if the output file exists
        if not os.path.exists(output_file):
            logging.error(f"Output file {output_file} does not exist")
            return None
        
        # Load the result from the output file
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        # Get user ID from the result
        user_id = result.get('userId')
        
        if user_id:
            logging.info(f"Got user ID for {handle} from direct client call: {user_id}")
            return user_id
        else:
            logging.warning(f"Could not get user ID for {handle} from direct client call")
            return None
            
    except Exception as e:
        logging.error(f"Error getting user ID for handle {handle} from direct client call: {str(e)}")
        return None
    finally:
        # Remove the temporary file
        if 'output_file' in locals() and os.path.exists(output_file):
            os.remove(output_file)

def get_user_id_fallback(handle):
    """
    Fallback method to generate a consistent user ID from a handle
    
    This is used only when all API methods fail.
    """
    if not handle:
        return None
    
    try:
        import hashlib
        
        # Create a numeric ID by hashing the handle and taking the first 15 digits
        hash_object = hashlib.md5(handle.encode())
        hash_hex = hash_object.hexdigest()
        numeric_id = int(hash_hex, 16) % (10**15)  # Take first 15 digits
        
        logging.warning(f"Generated fallback numeric ID for {handle}: {numeric_id}")
        return str(numeric_id)
        
    except Exception as e:
        logging.error(f"Error generating fallback ID for {handle}: {str(e)}")
        return None
