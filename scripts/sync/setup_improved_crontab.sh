#!/bin/bash
# Setup improved crontab for synchronization with 30-day window and lock mechanism

# Get the current crontab
CURRENT_CRONTAB=$(crontab -l 2>/dev/null || echo "")

# Define the new crontab entry
NEW_ENTRY="*/15 * * * * cd /home/ubuntu/nitterlocal && python3 scripts/sync/sync_to_mysql_combined.py --since-days 30 --lock-timeout 60 >> data/sync_cron.log 2>&1"

# Check if the entry already exists
if echo "$CURRENT_CRONTAB" | grep -q "scripts/sync/sync_to_mysql_combined.py"; then
    # Replace the existing entry
    UPDATED_CRONTAB=$(echo "$CURRENT_CRONTAB" | sed -E 's|.*/15 .* cd /home/ubuntu/nitterlocal && python3 scripts/sync/sync_to_mysql_combined.py.*|'"$NEW_ENTRY"'|g')
    echo "$UPDATED_CRONTAB" | crontab -
    echo "Updated existing crontab entry for sync_to_mysql_combined.py"
else
    # Add the new entry
    echo "$CURRENT_CRONTAB" | { cat; echo "$NEW_ENTRY"; } | crontab -
    echo "Added new crontab entry for sync_to_mysql_combined.py"
fi

# Show the updated crontab
echo "Current crontab:"
crontab -l
