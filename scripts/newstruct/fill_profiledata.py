#!/usr/bin/env python3
"""
Script to fill profile data (tweet_count, followers_count, etc.) for Twitter URLs.
This script retrieves profile data from Twitter and updates the url_tracking table.
"""

import os
import sys
import logging
import sqlite3
import argparse
import subprocess
import json
import tempfile
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ProfileUpdater:
    """Class to update profile data for Twitter URLs"""
    
    def __init__(self, db_path):
        """Initialize the profile updater"""
        self.db_path = db_path
        logging.info(f"Initializing profile updater with database at {db_path}")
        
        # Ensure the database exists
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found at {db_path}")
        
        # Store the database path but don't create a connection yet
        # Each method will create its own connection when needed
        
        logging.info("Profile updater initialization complete")
    
    # This method is no longer needed as we don't maintain a persistent connection
    # def close(self):
    #     """Close the database connection"""
    #     if hasattr(self, 'conn') and self.conn:
    #         self.conn.close()
    
    def _run_twitter_profile_client(self, handle):
        """Run the Twitter profile client to get profile data"""
        logging.info(f"Running Twitter profile client for {handle}...")
        
        # Path to the Twitter profile client
        client_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/twitter_client/twitter_profile_client.js'))
        
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            output_path = temp_file.name
        
        # Run the Twitter profile client with output file
        try:
            result = subprocess.run(['node', client_path, handle, output_path], capture_output=True, text=True, check=True)
            
            # Read the JSON output from the file
            with open(output_path, 'r') as f:
                profile_data = json.load(f)
            
            # Clean up
            os.remove(output_path)
            
            return profile_data
        except subprocess.CalledProcessError as e:
            logging.error(f"Error running Twitter profile client: {e}")
            logging.error(f"Stderr: {e.stderr}")
            return None
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing Twitter profile client output: {e}")
            return None
        except FileNotFoundError as e:
            logging.error(f"Output file not found: {e}")
            return None
    
    def get_profile_data(self, handle):
        """Get profile data for a Twitter handle"""
        logging.info(f"Getting profile data for handle: {handle}")
        
        # Run the Twitter profile client
        profile_data = self._run_twitter_profile_client(handle)
        
        if profile_data:
            # Extract profile data
            profile = profile_data.get('profile', {})
            
            # Create a dictionary with profile data
            result = {
                'user_id': profile_data.get('userId'),
                'screen_name': handle,
                'followers_count': profile.get('followersCount', 0),
                'following_count': profile.get('followingCount', 0) or profile.get('friendsCount', 0),
                'tweet_count': profile.get('tweetsCount', 0) or profile.get('statusesCount', 0),
                'profile_image_url': profile.get('avatar'),
                'profile_banner_url': profile.get('banner'),
                'verified': 1 if profile.get('isVerified') else 0,
                'location': profile.get('location', ''),
                'description': profile.get('biography', ''),
                'created_at': profile.get('joined'),
                'kol_name': profile.get('name', ''),  # Add the name attribute
                'profile_updated_at': datetime.now().isoformat()
            }
            
            logging.info(f"Got profile data for {handle}: {result}")
            
            return result
        else:
            logging.error(f"Failed to get profile data for {handle}")
            return None
    
    def update_profile_in_db(self, url, profile_data):
        """Update profile data in the database"""
        if not profile_data:
            logging.error(f"No profile data to update for URL: {url}")
            return False
        
        try:
            # Create a new connection in this thread
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build update query with only columns that exist in the table
            # Based on the schema check, we know the available columns
            valid_columns = ['url', 'user_id', 'description', 'status', 'last_checked', 
                            'error_count', 'tweet_count', 'type', 'added_at', 
                            'last_scraped', 'last_error', 'subtype', 'kol_name',
                            'screen_name', 'followers_count', 'following_count',
                            'profile_image_url', 'profile_banner_url', 'verified',
                            'location', 'created_at', 'profile_updated_at']
            
            update_fields = []
            update_values = []
            
            for key, value in profile_data.items():
                # Skip the URL field and any fields not in the valid_columns list
                if key != 'url' and key in valid_columns:
                    update_fields.append(f"{key} = ?")
                    update_values.append(value)
            
            # If we have no valid fields to update, return
            if not update_fields:
                logging.warning(f"No valid fields to update for URL: {url}")
                conn.close()
                return False
                
            # Add URL for WHERE clause
            update_values.append(url)
            
            # Execute update query
            update_query = f'''
            UPDATE url_tracking 
            SET {', '.join(update_fields)}
            WHERE url = ?
            '''
            
            cursor.execute(update_query, update_values)
            conn.commit()
            conn.close()
            
            logging.info(f"Updated profile data for URL: {url}")
            return True
        except sqlite3.Error as e:
            logging.error(f"Error updating profile data for URL {url}: {e}")
            return False
    
    def update_profile_by_handle(self, handle):
        """Update profile data for a Twitter handle"""
        try:
            # Create a new connection in this thread
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get URL from handle
            # Note: The url_tracking table doesn't have a screen_name column
            # We need to extract the handle from the URL instead
            cursor.execute("SELECT url FROM url_tracking WHERE url LIKE ? COLLATE NOCASE", (f"%twitter.com/{handle}%",))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                url = result['url']
                
                # Get profile data
                profile_data = self.get_profile_data(handle)
                
                # Update profile data in database
                if profile_data:
                    return self.update_profile_in_db(url, profile_data)
            else:
                logging.error(f"No URL found for handle: {handle}")
                return False
        except Exception as e:
            logging.error(f"Error updating profile for handle {handle}: {str(e)}")
            return False
    
    def update_profile_by_url(self, url):
        """Update profile data for a Twitter URL"""
        # Extract handle from URL
        handle = self._extract_handle_from_url(url)
        
        if handle:
            # Get profile data
            profile_data = self.get_profile_data(handle)
            
            # Update profile data in database
            if profile_data:
                return self.update_profile_in_db(url, profile_data)
        else:
            logging.error(f"Could not extract handle from URL: {url}")
            return False
    
    def _extract_handle_from_url(self, url):
        """Extract handle from Twitter URL"""
        if not url:
            return None
        
        # Remove trailing slash if present
        if url.endswith('/'):
            url = url[:-1]
        
        # Extract handle from URL
        parts = url.split('/')
        if len(parts) > 3:
            return parts[-1]
        
        return None
    
    def update_all_profiles(self, limit=None):
        """Update profile data for all Twitter URLs"""
        try:
            # Create a new connection in this thread
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all URLs from url_tracking table
            query = "SELECT url FROM url_tracking"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            results = cursor.fetchall()
            conn.close()
            
            success_count = 0
            error_count = 0
            
            for result in results:
                url = result['url']
                
                # Extract handle from URL
                handle = self._extract_handle_from_url(url)
                
                if handle:
                    # Update profile data
                    if self.update_profile_by_handle(handle):
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    logging.error(f"Could not extract handle from URL: {url}")
                    error_count += 1
            
            logging.info(f"Updated {success_count} profiles, {error_count} errors")
            return success_count, error_count
        except Exception as e:
            logging.error(f"Error updating all profiles: {str(e)}")
            return 0, 0

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Fill profile data for Twitter URLs')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the SQLite database')
    parser.add_argument('--handle', type=str, help='Twitter handle to update')
    parser.add_argument('--url', type=str, help='Twitter URL to update')
    parser.add_argument('--all', action='store_true', help='Update all profiles')
    parser.add_argument('--limit', type=int, help='Limit the number of profiles to update')
    
    args = parser.parse_args()
    
    # Resolve database path
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', args.db_path))
    
    # Initialize profile updater
    try:
        updater = ProfileUpdater(db_path)
        
        if args.handle:
            # Update profile by handle
            if updater.update_profile_by_handle(args.handle):
                print(f"Successfully updated profile for handle: {args.handle}")
            else:
                print(f"Failed to update profile for handle: {args.handle}")
        elif args.url:
            # Update profile by URL
            if updater.update_profile_by_url(args.url):
                print(f"Successfully updated profile for URL: {args.url}")
            else:
                print(f"Failed to update profile for URL: {args.url}")
        elif args.all:
            # Update all profiles
            success_count, error_count = updater.update_all_profiles(args.limit)
            print(f"Updated {success_count} profiles, {error_count} errors")
        else:
            parser.print_help()
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return 1
    # Remove this block since we no longer need to close the connection
    # finally:
    #     if 'updater' in locals():
    #         updater.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
