#!/usr/bin/env python3
"""
Test script to verify we can retrieve all required data for the kol_info table.
This script tests if we can extract profile information from Twitter accounts
and map them correctly to the kol_info table schema.
"""

import os
import sys
import json
import logging
import sqlite3
from datetime import datetime
import subprocess
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Path to the database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data/local_database.db')

def get_connection():
    """Get a connection to the database"""
    return sqlite3.connect(DB_PATH)

def get_sample_urls(limit=5):
    """Get a sample of URLs from the url_tracking table"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get a sample of URLs with different types
    cursor.execute('''
    SELECT url, user_id, type, subtype 
    FROM url_tracking 
    WHERE user_id IS NOT NULL 
    GROUP BY type, subtype 
    LIMIT ?
    ''', (limit,))
    
    urls = cursor.fetchall()
    conn.close()
    
    return urls

def extract_twitter_handle(url):
    """Extract the Twitter handle from a URL"""
    if not url:
        return None
    
    # Remove trailing slash if present
    if url.endswith('/'):
        url = url[:-1]
    
    # Extract the handle from the URL
    parts = url.split('/')
    if len(parts) < 4:
        logging.error(f"Invalid URL format: {url}")
        return None
    
    handle = parts[-1]
    logging.info(f"Extracted handle: {handle}")
    return handle

def get_profile_info(handle, client_dir=None):
    """Get profile information for a Twitter handle using agent-twitter-client"""
    logging.info(f"Getting profile info for handle: {handle}")
    
    # Set the client directory
    if client_dir is None:
        # Use the twitter_client directory
        client_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src/twitter_client')
    
    # Path to the test script
    test_script_path = os.path.join(client_dir, 'test_profile.js')
    
    # Create a temporary file for the output
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
        output_file = temp_file.name
    
    try:
        # Run the test script
        logging.info(f"Running test script for {handle}...")
        process = subprocess.run(
            ['node', test_script_path, handle, output_file],
            cwd=client_dir,
            check=True,
            capture_output=True,
            universal_newlines=True
        )
        
        logging.info(process.stdout)
        
        # Check if the output file exists
        if not os.path.exists(output_file):
            logging.error(f"Output file {output_file} does not exist")
            return None
        
        # Load the profile from the output file
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        return result
        
    except Exception as e:
        logging.error(f"Error getting profile for handle {handle}: {str(e)}")
        return None
    finally:
        # Remove the temporary file
        if os.path.exists(output_file):
            os.remove(output_file)

def map_to_kol_info(profile_data, url_data):
    """Map profile data to kol_info table fields"""
    if not profile_data or not profile_data.get('profile'):
        logging.error("No profile data available")
        return None
    
    profile = profile_data['profile']
    url, user_id, type_val, subtype_val = url_data
    
    # Map fields from profile to kol_info
    kol_info = {
        'kol_id': profile.get('userId') or user_id,
        'kol_name': profile.get('name'),
        'kol_screen_name': f"@{profile.get('username')}" if profile.get('username') else None,
        'description': profile.get('biography'),
        'followers_count': str(profile.get('followersCount')) if profile.get('followersCount') is not None else None,
        'fast_followers_count': None,  # Not directly available
        'normal_followers_count': None,  # Not directly available
        'following_count': profile.get('followingCount'),
        'favourites_count': profile.get('likesCount'),
        'statuses_count': profile.get('statusesCount') or profile.get('tweetsCount'),
        'first_category': type_val,
        'second_category': subtype_val,
        'created_at': profile.get('joined')
    }
    
    return kol_info

def main():
    """Main function"""
    logging.info("Starting test script")
    
    # Get a sample of URLs
    urls = get_sample_urls(5)
    logging.info(f"Got {len(urls)} URLs")
    
    # Process each URL
    results = []
    for url_data in urls:
        url = url_data[0]
        logging.info(f"Processing URL: {url}")
        
        # Extract the Twitter handle
        handle = extract_twitter_handle(url)
        if not handle:
            logging.error(f"Could not extract handle from URL: {url}")
            continue
        
        # Get profile information
        profile_data = get_profile_info(handle)
        if not profile_data:
            logging.error(f"Could not get profile for handle: {handle}")
            continue
        
        # Map to kol_info
        kol_info = map_to_kol_info(profile_data, url_data)
        if not kol_info:
            logging.error(f"Could not map profile to kol_info for handle: {handle}")
            continue
        
        results.append(kol_info)
    
    # Print results
    logging.info(f"Processed {len(results)} profiles")
    for i, result in enumerate(results):
        logging.info(f"Profile {i+1}:")
        for key, value in result.items():
            logging.info(f"  {key}: {value}")
    
    logging.info("Test script completed")

if __name__ == "__main__":
    main()
