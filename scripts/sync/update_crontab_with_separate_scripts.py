#!/usr/bin/env python3
"""
Script to update crontab with separate synchronization scripts.

This script:
1. Creates a new crontab configuration with separate synchronization scripts
2. Installs the new crontab configuration
3. Provides detailed logging of the update process
"""

import os
import sys
import logging
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_current_crontab():
    """Get the current crontab configuration"""
    try:
        result = subprocess.run(
            ['crontab', '-l'],
            check=False,  # Don't fail if no crontab exists
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            logging.warning(f"No existing crontab found: {result.stderr}")
            return "# New crontab\n"
    
    except Exception as e:
        logging.error(f"Error getting current crontab: {str(e)}")
        return "# New crontab\n"

def remove_existing_sync_entries(crontab_content):
    """Remove existing synchronization entries from crontab"""
    lines = crontab_content.splitlines()
    filtered_lines = []
    
    for line in lines:
        # Skip lines containing sync scripts
        if any(script in line for script in [
            'sync_to_mysql_combined.py',
            'sync_kol_character_only.py',
            'sync_url_tracking_only.py',
            'sync_tweets_only.py'
        ]):
            logging.info(f"Removing existing sync entry: {line}")
            continue
        
        filtered_lines.append(line)
    
    return '\n'.join(filtered_lines) + '\n'

def add_separate_sync_entries(crontab_content, project_dir):
    """Add separate synchronization entries to crontab"""
    # Add new entries for separate synchronization scripts
    new_entries = f"""
# Every 2 hours, synchronize kol_character table
0 */2 * * * cd {project_dir} && python3 scripts/sync/sync_kol_character_only.py --lock-timeout 60 >> data/kol_character_sync.log 2>&1

# Every 2 hours, synchronize url_tracking table
30 */2 * * * cd {project_dir} && python3 scripts/sync/sync_url_tracking_only.py --lock-timeout 60 >> data/url_tracking_sync.log 2>&1

# Every hour, synchronize tweets table (with 30-day window)
0 */1 * * * cd {project_dir} && python3 scripts/sync/sync_tweets_only.py --since-days 30 --lock-timeout 60 >> data/tweets_sync.log 2>&1
"""
    
    return crontab_content + new_entries

def install_new_crontab(crontab_content):
    """Install the new crontab configuration"""
    try:
        # Write the new crontab to a temporary file
        temp_file = '/tmp/new_crontab.txt'
        with open(temp_file, 'w') as f:
            f.write(crontab_content)
        
        # Install the new crontab
        result = subprocess.run(
            ['crontab', temp_file],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Remove the temporary file
        os.remove(temp_file)
        
        logging.info("Installed new crontab configuration")
        return True
    
    except Exception as e:
        logging.error(f"Error installing new crontab: {str(e)}")
        return False

def main():
    """Main function"""
    try:
        # Get the project directory
        project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        logging.info(f"Starting crontab update at {datetime.now().isoformat()}")
        logging.info(f"Project directory: {project_dir}")
        
        # Get the current crontab
        current_crontab = get_current_crontab()
        
        # Remove existing synchronization entries
        filtered_crontab = remove_existing_sync_entries(current_crontab)
        
        # Add separate synchronization entries
        new_crontab = add_separate_sync_entries(filtered_crontab, project_dir)
        
        # Print the new crontab for review
        logging.info("New crontab configuration:")
        for line in new_crontab.splitlines():
            logging.info(f"  {line}")
        
        # Install the new crontab
        success = install_new_crontab(new_crontab)
        
        if success:
            logging.info("Crontab updated successfully")
            logging.info("KOL Character sync: Every 2 hours at minute 0")
            logging.info("URL Tracking sync: Every 2 hours at minute 30")
            logging.info("Tweets sync: Every hour at minute 0")
            return 0
        else:
            logging.error("Failed to update crontab")
            return 1
    
    except Exception as e:
        logging.error(f"Error updating crontab: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
