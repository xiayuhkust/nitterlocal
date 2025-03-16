#!/usr/bin/env python3
"""
Script to get kol_id from kol_character table based on a Twitter URL.
This script:
1. Takes a Twitter URL as input
2. Extracts the screen_name from the URL
3. Queries the kol_character table to find the corresponding kol_id
4. Returns the kol_id if found
"""

import os
import sys
import logging
import argparse
import sqlite3
from urllib.parse import urlparse

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import required modules
from scripts.utils.url_utils import extract_twitter_handle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def get_db_connection(db_path):
    """Get a database connection"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_kol_id_from_url(url, db_path='data/local_database.db'):
    """
    Get kol_id from kol_character table based on a Twitter URL
    
    Args:
        url (str): Twitter URL
        db_path (str): Database path
        
    Returns:
        dict: Result containing kol_id, screen_name, and other information
    """
    logging.info(f"Getting kol_id for URL: {url}")
    
    # Extract screen_name from URL
    screen_name = extract_twitter_handle(url)
    
    if not screen_name:
        logging.error(f"Could not extract screen_name from URL: {url}")
        return {
            'url': url,
            'screen_name': None,
            'kol_id': None,
            'found': False,
            'error': 'Could not extract screen_name from URL'
        }
    
    logging.info(f"Extracted screen_name: {screen_name}")
    
    # Connect to database
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Query kol_character table
        cursor.execute("""
        SELECT * FROM kol_character 
        WHERE kol_screen_name = ? 
        LIMIT 1
        """, (screen_name,))
        
        result = cursor.fetchone()
        
        if result:
            # Convert row to dict
            kol_data = dict(result)
            
            # Return result
            return {
                'url': url,
                'screen_name': screen_name,
                'kol_id': kol_data.get('kol_id'),
                'found': True,
                'kol_data': kol_data
            }
        else:
            # Check if screen_name exists in url_tracking table
            cursor.execute("""
            SELECT * FROM url_tracking 
            WHERE screen_name = ? 
            LIMIT 1
            """, (screen_name,))
            
            url_result = cursor.fetchone()
            
            if url_result:
                url_data = dict(url_result)
                
                return {
                    'url': url,
                    'screen_name': screen_name,
                    'kol_id': None,
                    'found': False,
                    'url_data': url_data,
                    'error': 'Screen name found in url_tracking but not in kol_character'
                }
            else:
                return {
                    'url': url,
                    'screen_name': screen_name,
                    'kol_id': None,
                    'found': False,
                    'error': 'Screen name not found in database'
                }
    except Exception as e:
        logging.error(f"Error querying database: {str(e)}")
        return {
            'url': url,
            'screen_name': screen_name,
            'kol_id': None,
            'found': False,
            'error': str(e)
        }
    finally:
        if conn:
            conn.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Get kol_id from kol_character table based on a Twitter URL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get kol_id for a URL
  python get_kol_id.py https://twitter.com/elonmusk
  
  # Get kol_id for a URL with custom database path
  python get_kol_id.py https://twitter.com/elonmusk --db-path /path/to/database.db
  
  # Get kol_id for a URL with verbose output
  python get_kol_id.py https://twitter.com/elonmusk --verbose
"""
    )
    
    parser.add_argument(
        'url',
        type=str,
        help='Twitter URL'
    )
    
    parser.add_argument(
        '--db-path',
        type=str,
        default='data/local_database.db',
        help='Database path (default: data/local_database.db)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get kol_id
    result = get_kol_id_from_url(args.url, db_path=args.db_path)
    
    # Print result
    if result['found']:
        print(f"URL: {result['url']}")
        print(f"Screen name: {result['screen_name']}")
        print(f"KOL ID: {result['kol_id']}")
        
        if args.verbose:
            print("\nKOL Data:")
            for key, value in result['kol_data'].items():
                print(f"  {key}: {value}")
    else:
        print(f"URL: {result['url']}")
        print(f"Screen name: {result['screen_name']}")
        print(f"Error: {result['error']}")
        
        if 'url_data' in result and args.verbose:
            print("\nURL Data:")
            for key, value in result['url_data'].items():
                print(f"  {key}: {value}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
