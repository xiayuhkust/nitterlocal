#!/usr/bin/env python3
"""
Script to update profile data in url_tracking table.
This script fetches profile information from Twitter and updates the url_tracking table.
"""

import os
import sys
import logging
import argparse
import sqlite3
import json
import tempfile
import subprocess
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import required modules
try:
    from src.database.url_manager import URLManager
    from app.twitter_api_utils import extract_twitter_handle
except ImportError:
    logging.error("Could not import required modules")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ProfileUpdater:
    """Profile updater for Twitter data"""
    
    def __init__(self, db_path='data/local_database.db'):
        """Initialize the profile updater"""
        logging.info(f"Initializing profile updater with database at {db_path}")
        
        self.db_path = db_path
        self.url_manager = URLManager(db_path=db_path)
        
        # Set the client directory
        self.client_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                      'src/twitter_client')
        
        # Check if the Twitter client exists
        self.client_path = os.path.join(self.client_dir, 'twitter_client.js')
        if not os.path.exists(self.client_path):
            raise ValueError(f"Twitter client {self.client_path} does not exist")
        
        logging.info("Profile updater initialization complete")
    
    def get_profile_data(self, handle):
        """Get profile data for a Twitter handle"""
        logging.info(f"Getting profile data for handle: {handle}")
        
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            output_file = temp_file.name
        
        try:
            # Use the profile client instead of the regular client
            profile_client_path = os.path.join(self.client_dir, 'twitter_profile_client.js')
            
            # Check if the profile client exists, if not, fall back to regular client
            if not os.path.exists(profile_client_path):
                logging.warning(f"Profile client {profile_client_path} does not exist, falling back to regular client")
                profile_client_path = self.client_path
                
                # Run the Twitter client to get profile data
                logging.info(f"Running Twitter client to get profile data for {handle}...")
                process = subprocess.run(
                    ['node', profile_client_path, handle, '1', '0', output_file],
                    cwd=self.client_dir,
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
                
                # Extract profile data from regular client
                profile_data = {
                    'user_id': result.get('userId'),
                    'screen_name': handle,
                    'followers_count': result.get('followersCount', 0),
                    'following_count': result.get('followingCount', 0),
                    'tweet_count': result.get('statusesCount', 0),
                    'profile_image_url': result.get('profileImageUrl', ''),
                    'profile_banner_url': result.get('profileBannerUrl', ''),
                    'verified': 1 if result.get('verified', False) else 0,
                    'location': result.get('location', ''),
                    'description': result.get('description', ''),
                    'created_at': result.get('createdAt', ''),
                    'profile_updated_at': datetime.now().isoformat()
                }
            else:
                # Run the Twitter profile client to get profile data
                logging.info(f"Running Twitter profile client for {handle}...")
                process = subprocess.run(
                    ['node', profile_client_path, handle, output_file],
                    cwd=self.client_dir,
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
                
                # Extract profile data from profile client
                profile = result.get('profile', {})
                
                profile_data = {
                    'user_id': result.get('userId'),
                    'screen_name': handle,
                    'followers_count': profile.get('followersCount', 0),
                    'following_count': profile.get('followingCount', 0) or profile.get('friendsCount', 0),
                    'tweet_count': profile.get('tweetsCount', 0) or profile.get('statusesCount', 0),
                    'profile_image_url': profile.get('avatar', ''),
                    'profile_banner_url': profile.get('banner', ''),
                    'verified': 1 if profile.get('verified', False) or profile.get('isVerified', False) or profile.get('isBlueVerified', False) else 0,
                    'location': profile.get('location', ''),
                    'description': profile.get('biography', ''),
                    'created_at': profile.get('joined', ''),
                    'profile_updated_at': datetime.now().isoformat()
                }
            
            logging.info(f"Got profile data for {handle}: {profile_data}")
            return profile_data
                
        except Exception as e:
            logging.error(f"Error getting profile data for handle {handle}: {str(e)}")
            return None
        finally:
            # Remove the temporary file
            if os.path.exists(output_file):
                os.remove(output_file)
    
    def update_profile_in_db(self, url, profile_data):
        """Update profile data in the database"""
        if not profile_data:
            logging.warning(f"No profile data to update for URL: {url}")
            return False
        
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Try to import normalize_twitter_url function
            try:
                from scripts.utils.url_utils import normalize_twitter_url
                # Normalize the URL to ensure x.com is converted to twitter.com
                normalized_url = normalize_twitter_url(url)
                if normalized_url is None:
                    normalized_url = url
            except ImportError:
                # Fallback implementation if url_utils is not available
                def normalize_twitter_url(url):
                    if not url:
                        return url
                    if 'x.com' in url:
                        return url.replace('x.com', 'twitter.com')
                    return url
                
                normalized_url = normalize_twitter_url(url)
            
            # Update the profile data
            update_fields = []
            update_values = []
            
            for key, value in profile_data.items():
                if key != 'url':  # Skip the URL field
                    update_fields.append(f"{key} = ?")
                    update_values.append(value)
            
            # Try to update using both original and normalized URL
            update_values.append(normalized_url)  # For the WHERE clause
            
            update_query = f'''
            UPDATE url_tracking 
            SET {', '.join(update_fields)}
            WHERE url = ?
            '''
            
            cursor.execute(update_query, update_values)
            
            if cursor.rowcount == 0 and url != normalized_url:
                # If normalized URL didn't work, try the original URL
                update_values[-1] = url
                cursor.execute(update_query, update_values)
            
            if cursor.rowcount == 0:
                # If still no rows affected, try to find by screen_name
                if 'screen_name' in profile_data:
                    screen_name = profile_data['screen_name']
                    update_query = f'''
                    UPDATE url_tracking 
                    SET {', '.join(update_fields)}
                    WHERE screen_name = ?
                    '''
                    update_values[-1] = screen_name
                    cursor.execute(update_query, update_values)
                    
                    if cursor.rowcount > 0:
                        logging.info(f"Updated profile data using screen_name: {screen_name}")
                    else:
                        logging.warning(f"URL {url} and screen_name {screen_name} not found in database")
                        conn.close()
                        return False
                else:
                    logging.warning(f"URL {url} not found in database")
                    conn.close()
                    return False
            
            conn.commit()
            conn.close()
            
            logging.info(f"Updated profile data for URL: {url}")
            return True
            
        except Exception as e:
            logging.error(f"Error updating profile data for URL {url}: {str(e)}")
            return False
    
    def update_profiles(self, urls=None, batch_size=10, sleep_between_urls=2, limit=None):
        """Update profile data for multiple URLs"""
        logging.info("Starting profile update")
        
        try:
            # Get URLs to update
            if not urls:
                urls = self.url_manager.get_urls(status='active', limit=limit)
                
            total_urls = len(urls)
            logging.info(f"Found {total_urls} URLs to update")
            
            # Process URLs
            updated_count = 0
            error_count = 0
            
            for i, url_data in enumerate(urls):
                url = url_data['url']
                logging.info(f"Processing URL {i+1}/{total_urls}: {url}")
                
                # Extract Twitter handle
                handle = extract_twitter_handle(url)
                if not handle:
                    logging.warning(f"Could not extract handle from URL: {url}")
                    error_count += 1
                    continue
                
                # Get profile data
                profile_data = self.get_profile_data(handle)
                if not profile_data:
                    logging.warning(f"Could not get profile data for handle: {handle}")
                    error_count += 1
                    continue
                
                # Update profile in database
                if self.update_profile_in_db(url, profile_data):
                    updated_count += 1
                else:
                    error_count += 1
                
                # Sleep between URLs
                if i < total_urls - 1 and sleep_between_urls > 0:
                    logging.info(f"Sleeping for {sleep_between_urls} seconds")
                    import time
                    time.sleep(sleep_between_urls)
            
            logging.info(f"Profile update completed. Updated {updated_count}/{total_urls} profiles, {error_count} errors")
            
            return {
                'total': total_urls,
                'updated': updated_count,
                'errors': error_count
            }
            
        except Exception as e:
            logging.error(f"Error in profile update: {str(e)}")
            return {
                'error': str(e)
            }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Update profile data in url_tracking table')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to SQLite database')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for URL processing')
    parser.add_argument('--sleep', type=int, default=2, help='Sleep time between URLs (seconds)')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to process')
    
    args = parser.parse_args()
    
    # Initialize and run the profile updater
    updater = ProfileUpdater(db_path=args.db_path)
    result = updater.update_profiles(
        batch_size=args.batch_size,
        sleep_between_urls=args.sleep,
        limit=args.limit
    )
    
    # Print summary
    print("\nProfile Update Summary:")
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Total URLs: {result.get('total', 0)}")
        print(f"Updated: {result.get('updated', 0)}")
        print(f"Errors: {result.get('errors', 0)}")
    
    return 0

if __name__ == "__main__":
    main()
