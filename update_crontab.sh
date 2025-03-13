#!/bin/bash

# Script to update the crontab with the new combined synchronization script

# Get the current crontab
crontab -l > /tmp/current_crontab

# Check if the old sync script is in the crontab
if grep -q "sync_to_mysql_with_nodejs.py" /tmp/current_crontab; then
    # Replace the old sync script with the new one
    sed -i 's/sync_to_mysql_with_nodejs.py/sync_to_mysql_combined.py/g' /tmp/current_crontab
    echo "Replaced sync_to_mysql_with_nodejs.py with sync_to_mysql_combined.py in crontab"
elif grep -q "sync_to_mysql_no_nodejs.py" /tmp/current_crontab; then
    # Replace the old sync script with the new one
    sed -i 's/sync_to_mysql_no_nodejs.py/sync_to_mysql_combined.py/g' /tmp/current_crontab
    echo "Replaced sync_to_mysql_no_nodejs.py with sync_to_mysql_combined.py in crontab"
else
    # Add the new sync script to the crontab
    echo "# Every 15 minutes sync to MySQL" >> /tmp/current_crontab
    echo "*/15 * * * * cd /home/ubuntu/nitterlocal && python3 scripts/sync/sync_to_mysql_combined.py --since-days 1 >> data/sync_cron.log 2>&1" >> /tmp/current_crontab
    echo "Added sync_to_mysql_combined.py to crontab"
fi

# Update the crontab
crontab /tmp/current_crontab
echo "Updated crontab"

# Clean up
rm /tmp/current_crontab
