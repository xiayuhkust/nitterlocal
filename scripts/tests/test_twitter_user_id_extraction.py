#!/usr/bin/env python3
"""
Test script to verify the Twitter user ID extraction methods with direct API call.
"""

import os
import sys
import logging
import subprocess
import json
import tempfile

# Add the project root to the Python path
sys.path.append('/home/ubuntu/nitterlocal')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_direct_twitter_client_call(handle):
    """Test Twitter user ID extraction by directly calling the twitter_client.js script"""
    logging.info(f"Testing direct Twitter client call for handle: {handle}")
    
    try:
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            output_file = temp_file.name
        
        # Get the path to the twitter_client.js script
        client_dir = os.path.join('/home/ubuntu/nitterlocal/src/twitter_client')
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
        
        logging.info(process.stdout)
        
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
            logging.info(f"Got user ID for {handle}: {user_id}")
            return user_id
        else:
            logging.warning(f"Could not get user ID for {handle}")
            return None
            
    except Exception as e:
        logging.error(f"Error testing direct Twitter client call for handle {handle}: {str(e)}")
        return None
    finally:
        # Remove the temporary file
        if 'output_file' in locals() and os.path.exists(output_file):
            os.remove(output_file)

def main():
    """Main function"""
    # Test with the example handle
    handle = "cz_binance"
    user_id = test_direct_twitter_client_call(handle)
    
    # Print the results
    print("\nTwitter User ID Extraction Test Results:")
    print(f"Handle: {handle}")
    print(f"Direct Twitter client call: {user_id}")
    
    # Check if the direct call returned the expected user ID
    expected_user_id = "902926941413453824"
    if user_id == expected_user_id:
        print(f"\nSUCCESS: Direct Twitter client call returned the expected user ID: {expected_user_id}")
    elif user_id:
        print(f"\nWARNING: Direct Twitter client call returned {user_id}, expected {expected_user_id}")
    else:
        print(f"\nERROR: Direct Twitter client call failed to return a user ID")

if __name__ == "__main__":
    main()
