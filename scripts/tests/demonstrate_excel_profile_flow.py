#!/usr/bin/env python3
"""
Script to demonstrate the complete data flow from Excel processing to database storage,
focusing on tweet_count and profile data.
"""

import os
import sys
import logging
import argparse
import sqlite3
import pandas as pd
import tempfile
import subprocess
import json
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_test_excel(output_path, use_x_domain=False):
    """Create a test Excel file with Twitter profile data"""
    try:
        # Create a DataFrame with test data
        data = {
            'Twitter url': [f"https://{'x' if use_x_domain else 'twitter'}.com/cz_binance"],
            'first category': ['KOL'],
            'second_category': ['-'],
            'bio': ['Binance创始人赵长鹏'],
            'lore': ['Active in crypto since 2017'],
            'knowledge': ['Crypto Trading: Expert in TA and price action'],
            'postExamples': ['BTC testing 70K resistance'],
            'topics': ['Crypto Trading: Shares TA insights'],
            'style_all': ['Analytical: Focuses on charts and data'],
            'style_chat': ['Concise: Short, sharp replies'],
            'style_post': ['Brief: Quick market updates'],
            'adjectives': ['Analytical, Precise, Practical']
        }
        
        df = pd.DataFrame(data)
        
        # Save to Excel
        df.to_excel(output_path, index=False)
        
        logging.info(f"Created test Excel file at {output_path}")
        return True
    
    except Exception as e:
        logging.error(f"Error creating test Excel file: {str(e)}")
        return False

def get_profile_data(handle):
    """Get profile data for a Twitter handle using the Twitter profile client"""
    try:
        # Set the client directory
        client_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                 'src/twitter_client')
        
        # Check if the profile client exists
        profile_client_path = os.path.join(client_dir, 'twitter_profile_client.js')
        
        if not os.path.exists(profile_client_path):
            logging.error(f"Profile client {profile_client_path} does not exist")
            return None
        
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            output_file = temp_file.name
        
        # Run the Twitter profile client to get profile data
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
        
        # Remove the temporary file
        if os.path.exists(output_file):
            os.remove(output_file)
        
        return profile_data
    
    except Exception as e:
        logging.error(f"Error getting profile data for handle {handle}: {str(e)}")
        return None

def update_profile_in_db(db_path, url, profile_data):
    """Update profile data in the database"""
    if not profile_data:
        logging.warning(f"No profile data to update for URL: {url}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Normalize the URL to ensure x.com is converted to twitter.com
        normalized_url = url
        if 'x.com' in url:
            normalized_url = url.replace('x.com', 'twitter.com')
        
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
        
        logging.info(f"Executing update query: {update_query}")
        logging.info(f"Update values: {update_values}")
        
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

def check_database_before_update(db_path, handle):
    """Check the database before updating profile data"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get profile data for the handle
        cursor.execute("SELECT * FROM url_tracking WHERE screen_name = ?", (handle,))
        record = cursor.fetchone()
        
        if not record:
            print(f"\nNo record found for handle: {handle}")
            conn.close()
            return False
        
        # Get column names
        cursor.execute("PRAGMA table_info(url_tracking)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Create a dictionary of the record
        record_dict = {columns[i]: record[i] for i in range(len(columns))}
        
        print(f"\n=== Database State BEFORE Update for {handle} ===")
        profile_fields = [
            'tweet_count', 'followers_count', 'following_count',
            'profile_image_url', 'profile_banner_url', 'verified',
            'location', 'description', 'created_at', 'profile_updated_at'
        ]
        
        for field in profile_fields:
            if field in record_dict:
                print(f"{field}: {record_dict.get(field)}")
            else:
                print(f"{field}: Not in schema")
        
        conn.close()
        return True
    
    except Exception as e:
        logging.error(f"Error checking database before update: {str(e)}")
        return False

def check_database_after_update(db_path, handle):
    """Check the database after updating profile data"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get profile data for the handle
        cursor.execute("SELECT * FROM url_tracking WHERE screen_name = ?", (handle,))
        record = cursor.fetchone()
        
        if not record:
            print(f"\nNo record found for handle: {handle}")
            conn.close()
            return False
        
        # Get column names
        cursor.execute("PRAGMA table_info(url_tracking)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Create a dictionary of the record
        record_dict = {columns[i]: record[i] for i in range(len(columns))}
        
        print(f"\n=== Database State AFTER Update for {handle} ===")
        profile_fields = [
            'tweet_count', 'followers_count', 'following_count',
            'profile_image_url', 'profile_banner_url', 'verified',
            'location', 'description', 'created_at', 'profile_updated_at'
        ]
        
        for field in profile_fields:
            if field in record_dict:
                print(f"{field}: {record_dict.get(field)}")
            else:
                print(f"{field}: Not in schema")
        
        conn.close()
        return True
    
    except Exception as e:
        logging.error(f"Error checking database after update: {str(e)}")
        return False

def process_excel_file(excel_path, db_path):
    """Process an Excel file with Twitter profile data"""
    try:
        # Import the process_excel_with_profile module
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../database')))
        
        try:
            from process_excel_with_profile import process_excel_file as process_excel
            
            # Process the Excel file
            print(f"\n=== Processing Excel File {excel_path} ===")
            result = process_excel(excel_path, db_path)
            
            if result > 0:
                print(f"Successfully processed {result} rows from Excel file")
            else:
                print("Failed to process Excel file")
            
            return result
        
        except ImportError:
            logging.error("Could not import process_excel_with_profile module")
            return 0
    
    except Exception as e:
        logging.error(f"Error processing Excel file: {str(e)}")
        return 0

def demonstrate_profile_flow(db_path, handle, excel_path=None):
    """Demonstrate the complete profile data flow"""
    try:
        # Create a test Excel file if not provided
        if not excel_path:
            excel_path = os.path.join(tempfile.gettempdir(), 'test_excel.xlsx')
            create_test_excel(excel_path)
        
        # Check database before update
        check_database_before_update(db_path, handle)
        
        # Get profile data
        profile_data = get_profile_data(handle)
        
        if profile_data:
            # Print profile data
            print(f"\n=== Profile Data Retrieved for {handle} ===")
            for key, value in profile_data.items():
                print(f"{key}: {value}")
            
            # Get the URL for the handle
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT url FROM url_tracking WHERE screen_name = ?", (handle,))
            url_result = cursor.fetchone()
            conn.close()
            
            if url_result:
                url = url_result[0]
                
                # Update profile in database
                print(f"\n=== Updating Profile Data for {url} ===")
                result = update_profile_in_db(db_path, url, profile_data)
                
                if result:
                    print("Profile data updated successfully")
                else:
                    print("Failed to update profile data")
                
                # Check database after update
                check_database_after_update(db_path, handle)
            else:
                print(f"No URL found for handle: {handle}")
        else:
            print(f"Failed to retrieve profile data for {handle}")
        
        # Process Excel file
        if os.path.exists(excel_path):
            process_excel_file(excel_path, db_path)
        
        return True
    
    except Exception as e:
        logging.error(f"Error demonstrating profile flow: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Demonstrate the complete profile data flow')
    parser.add_argument('--db-path', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db', help='Path to the SQLite database')
    parser.add_argument('--handle', type=str, default='cz_binance', help='Twitter handle to check')
    parser.add_argument('--excel', type=str, help='Path to the Excel file')
    
    args = parser.parse_args()
    
    # Check if the database exists
    if not os.path.exists(args.db_path):
        logging.error(f"Database file not found: {args.db_path}")
        return 1
    
    # Demonstrate profile flow
    demonstrate_profile_flow(args.db_path, args.handle, args.excel)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
