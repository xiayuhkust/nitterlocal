#!/usr/bin/env python3
"""
Script to verify that the sync_url_tracking_only.py script includes profile columns in the synchronization process.
This script analyzes the code without requiring MySQL connection.
"""

import os
import sys
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def verify_profile_columns_in_sync_script(script_path):
    """Verify that profile columns are included in the synchronization process"""
    logging.info(f"Verifying profile columns in sync script: {script_path}")
    
    try:
        # Read the script file
        with open(script_path, 'r') as f:
            script_content = f.read()
        
        # Define the profile columns to check for
        profile_columns = [
            'followers_count',
            'following_count',
            'tweet_count',
            'profile_image_url',
            'profile_banner_url',
            'verified',
            'location',
            'created_at',
            'profile_updated_at'
        ]
        
        # Check if each profile column is included in the script
        found_columns = []
        for column in profile_columns:
            if column in script_content:
                found_columns.append(column)
                logging.info(f"Found profile column in sync script: {column}")
        
        # Check for the section that handles profile columns
        profile_section_pattern = r"# Add profile columns if they exist in MySQL"
        profile_section_match = re.search(profile_section_pattern, script_content)
        
        if profile_section_match:
            logging.info("Found dedicated section for handling profile columns")
            
            # Extract the profile columns section
            section_start = profile_section_match.start()
            section_end = script_content.find("# This section is now handled", section_start)
            if section_end == -1:
                section_end = len(script_content)
            
            profile_section = script_content[section_start:section_end]
            print("\n=== Profile Columns Section in Sync Script ===")
            print(profile_section)
        
        # Summary
        if len(found_columns) == len(profile_columns):
            logging.info("All profile columns are included in the sync script")
            print(f"\nSUCCESS: All {len(profile_columns)} profile columns are included in the sync script")
            return True
        else:
            missing_columns = set(profile_columns) - set(found_columns)
            logging.warning(f"Missing profile columns in sync script: {', '.join(missing_columns)}")
            print(f"\nWARNING: {len(missing_columns)} profile columns are missing from the sync script: {', '.join(missing_columns)}")
            return False
    
    except Exception as e:
        logging.error(f"Error verifying profile columns in sync script: {str(e)}")
        return False

def main():
    """Main function"""
    script_path = '/home/ubuntu/nitterlocal/scripts/sync/sync_url_tracking_only.py'
    verify_profile_columns_in_sync_script(script_path)

if __name__ == "__main__":
    main()
