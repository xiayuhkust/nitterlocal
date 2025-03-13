#!/usr/bin/env python3
"""
Test script to verify profile information retrieval for @RaoulGMI
"""
import os
import sys
import json
import logging
import subprocess
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def try_get_profile_info(handle, client_dir=None):
    """Try to get profile information for a Twitter handle using agent-twitter-client"""
    logging.info(f"Trying to get profile info for handle: {handle}")
    
    # Set the client directory
    if client_dir is None:
        # Use the twitter_client directory
        client_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src/twitter_client')
    
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
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
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
    url, type_val, description_val = url_data
    
    # Map fields from profile to kol_info
    kol_info = {
        'kol_id': profile.get('userId'),
        'kol_name': profile.get('name'),
        'kol_screen_name': "@{}".format(profile.get('username')) if profile.get('username') else None,
        'description': profile.get('biography') or description_val,
        'followers_count': str(profile.get('followersCount')) if profile.get('followersCount') is not None else None,
        'fast_followers_count': None,
        'normal_followers_count': None,
        'following_count': profile.get('followingCount'),
        'favourites_count': profile.get('likesCount'),
        'statuses_count': profile.get('statusesCount') or profile.get('tweetsCount'),
        'first_category': type_val,
        'second_category': None,
    }
    
    return kol_info

def main():
    handle = "RaoulGMI"
    url_data = ("https://twitter.com/RaoulGMI", "kol", "加密货币KOL RaoulGMI")
    
    # Get profile data using Node.js
    profile_data = try_get_profile_info(handle)
    
    if profile_data:
        # Map to kol_info
        kol_info = map_to_kol_info(profile_data, url_data)
        
        print(f"Profile data for @{handle}:")
        print(f"User ID: {profile_data.get('userId')}")
        profile = profile_data.get('profile', {})
        print(f"Name: {profile.get('name')}")
        print(f"Username: {profile.get('username')}")
        print(f"Biography: {profile.get('biography')}")
        print(f"Followers Count: {profile.get('followersCount')}")
        print(f"Following Count: {profile.get('followingCount')}")
        print(f"Tweets Count: {profile.get('tweetsCount')}")
        
        print("\nMapped kol_info data:")
        for key, value in kol_info.items():
            print(f"{key}: {value}")
    else:
        print(f"Failed to get profile data for @{handle}")

if __name__ == "__main__":
    main()
