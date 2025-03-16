#!/usr/bin/env python3
"""
Script to update the sync_url_tracking_only.py script to handle profile data.
This script modifies the sync_url_tracking function to include profile columns.
"""

import os
import sys
import logging
import fileinput
import re
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def update_sync_url_tracking_script(script_path):
    """Update the sync_url_tracking_only.py script to handle profile data"""
    try:
        # Create a backup of the original file
        backup_path = f"{script_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        shutil.copy2(script_path, backup_path)
        logging.info(f"Created backup of original script at {backup_path}")
        
        # Read the original file
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Define the profile columns to add to the synchronization
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
        
        # Update the sync_url_tracking function to include profile columns
        # Find the section where MySQL columns are mapped
        pattern = r"(# Add kol_screen_name if it exists in MySQL.*?if 'created_at' in mysql_columns:.*?insert_values\.append\(datetime\.now\(\)\.strftime\('%Y-%m-%d %H:%M:%S'\)\))"
        
        # Replacement text that adds profile columns
        replacement = r"\1\n                \n                # Add profile columns if they exist in MySQL"
        
        for column in profile_columns:
            mysql_column = column
            replacement += f"""
                if '{mysql_column}' in mysql_columns and '{column}' in row_dict and row_dict['{column}']:
                    insert_columns.append('{mysql_column}')
                    insert_values.append(row_dict['{column}'])"""
        
        # Apply the replacement
        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Also update the update section for existing records
        pattern2 = r"(# Add kol_screen_name if it exists in MySQL.*?update_params\.append\(twitter_handle or ''\))"
        
        # Replacement text that adds profile columns for updates
        replacement2 = r"\1\n                \n                # Add profile columns if they exist in MySQL"
        
        for column in profile_columns:
            mysql_column = column
            replacement2 += f"""
                if '{mysql_column}' in mysql_columns and '{column}' in row_dict and row_dict['{column}']:
                    set_clauses.append("{mysql_column} = %s")
                    update_params.append(row_dict['{column}'])"""
        
        # Apply the second replacement
        updated_content = re.sub(pattern2, replacement2, updated_content, flags=re.DOTALL)
        
        # Write the updated content back to the file
        with open(script_path, 'w') as f:
            f.write(updated_content)
        
        logging.info(f"Updated {script_path} to handle profile columns")
        return True
    
    except Exception as e:
        logging.error(f"Error updating sync_url_tracking script: {str(e)}")
        return False

def main():
    """Main function"""
    # Path to the sync_url_tracking_only.py script
    script_path = '/home/ubuntu/nitterlocal/scripts/sync/sync_url_tracking_only.py'
    
    # Update the script
    if update_sync_url_tracking_script(script_path):
        logging.info("Successfully updated sync_url_tracking_only.py script")
    else:
        logging.error("Failed to update sync_url_tracking_only.py script")
        sys.exit(1)

if __name__ == "__main__":
    main()
