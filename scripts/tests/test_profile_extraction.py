#!/usr/bin/env python3
"""
Test script to verify profile data extraction for Twitter handles.
"""

import os
import sys
import logging
import json
import subprocess
import tempfile

# Add the project root to the Python path
sys.path.append('/home/ubuntu/nitterlocal')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_profile_extraction(handle):
    """Test profile data extraction for a Twitter handle"""
    logging.info(f"Testing profile data extraction for handle: {handle}")
    
    # Set the client directory
    client_dir = os.path.join('/home/ubuntu/nitterlocal', 'src/twitter_client')
    
    # Create a temporary file for the output
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
        output_file = temp_file.name
    
    try:
        # Check if the profile client exists
        profile_client_path = os.path.join(client_dir, 'twitter_profile_client.js')
        if not os.path.exists(profile_client_path):
            logging.error(f"Profile client {profile_client_path} does not exist")
            return False
        
        # Run the Twitter profile client
        logging.info(f"Running Twitter profile client for {handle}...")
        process = subprocess.run(
            ['node', profile_client_path, handle, output_file],
            cwd=client_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Check if the output file exists
        if not os.path.exists(output_file):
            logging.error(f"Output file {output_file} does not exist")
            return False
        
        # Load the result from the output file
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        # Print the profile data
        print(f"\n=== Profile Data for {handle} ===")
        print(json.dumps(result, indent=2))
        
        # Check if profile data is present
        if result.get('profile'):
            profile = result['profile']
            print(f"\n=== Key Profile Metrics ===")
            print(f"User ID: {result.get('userId')}")
            print(f"Followers Count: {profile.get('followersCount')}")
            print(f"Following Count: {profile.get('followingCount') or profile.get('friendsCount')}")
            print(f"Tweets Count: {profile.get('tweetsCount') or profile.get('statusesCount')}")
            print(f"Profile Image: {profile.get('avatar')}")
            print(f"Profile Banner: {profile.get('banner')}")
            print(f"Verified: {profile.get('isVerified') or profile.get('isBlueVerified')}")
            print(f"Location: {profile.get('location')}")
            print(f"Biography: {profile.get('biography')}")
            print(f"Joined: {profile.get('joined')}")
            
            return True
        else:
            logging.error(f"No profile data found for {handle}")
            return False
            
    except Exception as e:
        logging.error(f"Error testing profile extraction for {handle}: {str(e)}")
        return False
    finally:
        # Remove the temporary file
        if os.path.exists(output_file):
            os.remove(output_file)

def main():
    """Main function"""
    # Test profile extraction for cz_binance
    test_profile_extraction("cz_binance")

if __name__ == "__main__":
    main()
