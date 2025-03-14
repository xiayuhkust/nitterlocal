#!/usr/bin/env python3
"""
Test script for the backend API endpoints.
"""

import os
import sys
import logging
import requests
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_sync_mysql_endpoint():
    """Test the sync-mysql endpoint"""
    try:
        # Prepare form data
        data = {
            'sync_to_mysql': 'true',
            'test_mode': 'true'
        }
        
        # Send request
        logging.info("Testing /api/sync-mysql endpoint...")
        response = requests.post(
            'http://localhost:8000/api/sync-mysql',
            data=data
        )
        
        # Check response
        if response.status_code == 200:
            logging.info("Sync-mysql endpoint test passed")
            logging.info(f"Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            logging.error(f"Error: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        logging.error(f"Error testing sync-mysql endpoint: {str(e)}")
        return False

def test_sync_database_endpoint():
    """Test the sync-database endpoint without a file"""
    try:
        # Prepare form data
        data = {
            'file_id': '',
            'sync_to_mysql': 'true',
            'test_mode': 'true'
        }
        
        # Send request
        logging.info("Testing /api/sync-database endpoint without a file...")
        response = requests.post(
            'http://localhost:8000/api/sync-database',
            data=data
        )
        
        # Check response
        if response.status_code == 200:
            logging.info("Sync-database endpoint test passed")
            logging.info(f"Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            logging.error(f"Error: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        logging.error(f"Error testing sync-database endpoint: {str(e)}")
        return False

def main():
    """Main function"""
    sync_mysql_result = test_sync_mysql_endpoint()
    sync_database_result = test_sync_database_endpoint()
    
    if sync_mysql_result and sync_database_result:
        print("API endpoint tests passed!")
        return 0
    else:
        print("API endpoint tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
