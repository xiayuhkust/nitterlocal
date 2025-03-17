#!/usr/bin/env python3
"""
Script to check the schema of the url_tracking table and verify if tweet_count is being stored.
"""

import os
import sys
import sqlite3
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_table_schema(db_path, table_name):
    """Check the schema of a table"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print(f"\n=== Schema for table '{table_name}' ===")
        print("ID    Name                 Type            NotNull  Default         PK")
        print("----------------------------------------------------------------------")
        for col in columns:
            print(f"{col[0]:<5} {col[1]:<20} {col[2]:<15} {col[3]:<8} {str(col[4]):<15} {col[5]}")
        
        # Check for specific columns
        has_tweet_count = False
        has_followers_count = False
        has_profile_fields = False
        
        for col in columns:
            if col[1] == 'tweet_count':
                has_tweet_count = True
            if col[1] == 'followers_count':
                has_followers_count = True
            if col[1] in ['profile_image_url', 'profile_banner_url', 'verified']:
                has_profile_fields = True
        
        print(f"\n=== Column Check for '{table_name}' ===")
        print(f"Has tweet_count column: {has_tweet_count}")
        print(f"Has followers_count column: {has_followers_count}")
        print(f"Has profile fields: {has_profile_fields}")
        
        # Check record count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"\n=== Record Count for '{table_name}' ===")
        print(f"Total records: {count}")
        
        # Check for records with tweet_count > 0
        if has_tweet_count:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE tweet_count > 0")
            count_with_tweets = cursor.fetchone()[0]
            print(f"Records with tweet_count > 0: {count_with_tweets}")
        
        # Sample record
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
        sample = cursor.fetchone()
        
        if sample:
            print(f"\n=== Sample Record from '{table_name}' ===")
            sample_dict = {columns[i][1]: sample[i] for i in range(len(columns))}
            print("{")
            for key, value in sample_dict.items():
                print(f"  \"{key}\": {repr(value)},")
            print("}")
        
        conn.close()
        return True
    
    except Exception as e:
        logging.error(f"Error checking table schema: {str(e)}")
        return False

def check_profile_data_storage(db_path, handle):
    """Check if profile data is being stored for a specific handle"""
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
        
        print(f"\n=== Profile Data for {handle} ===")
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
        logging.error(f"Error checking profile data storage: {str(e)}")
        return False

def trace_profile_update_flow(db_path, handle):
    """Trace the profile update flow by simulating the update process"""
    try:
        # Add the project root directory to the Python path
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
        
        # Import the ProfileUpdater class
        try:
            from scripts.profile.update_profile_data import ProfileUpdater
            
            # Create a profile updater
            updater = ProfileUpdater(db_path=db_path)
            
            # Get profile data
            print(f"\n=== Getting Profile Data for {handle} ===")
            profile_data = updater.get_profile_data(handle)
            
            if profile_data:
                print("Profile data retrieved successfully:")
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
                    result = updater.update_profile_in_db(url, profile_data)
                    
                    if result:
                        print("Profile data updated successfully")
                    else:
                        print("Failed to update profile data")
                    
                    # Check if the data was actually updated
                    check_profile_data_storage(db_path, handle)
                else:
                    print(f"No URL found for handle: {handle}")
            else:
                print(f"Failed to retrieve profile data for {handle}")
        
        except ImportError as e:
            logging.error(f"Could not import ProfileUpdater: {str(e)}")
            return False
    
    except Exception as e:
        logging.error(f"Error tracing profile update flow: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Check url_tracking schema and verify tweet_count storage')
    parser.add_argument('--db-path', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db', help='Path to the SQLite database')
    parser.add_argument('--handle', type=str, default='cz_binance', help='Twitter handle to check')
    parser.add_argument('--trace', action='store_true', help='Trace the profile update flow')
    
    args = parser.parse_args()
    
    # Check if the database exists
    if not os.path.exists(args.db_path):
        logging.error(f"Database file not found: {args.db_path}")
        return 1
    
    # Check table schema
    check_table_schema(args.db_path, 'url_tracking')
    
    # Check profile data storage
    check_profile_data_storage(args.db_path, args.handle)
    
    # Trace profile update flow if requested
    if args.trace:
        trace_profile_update_flow(args.db_path, args.handle)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
