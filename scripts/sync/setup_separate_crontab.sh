#!/bin/bash
# Setup crontab for separate synchronization scripts

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Create a temporary file for the new crontab
TEMP_CRONTAB=$(mktemp)

# Export the current crontab to the temporary file
crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "# New crontab" > "$TEMP_CRONTAB"

# Remove any existing sync entries
grep -v "sync_to_mysql_combined.py" "$TEMP_CRONTAB" | grep -v "sync_kol_character_only.py" | grep -v "sync_url_tracking_only.py" | grep -v "sync_tweets_only.py" > "${TEMP_CRONTAB}.new"
mv "${TEMP_CRONTAB}.new" "$TEMP_CRONTAB"

# Add new entries for separate synchronization scripts
cat << EOF >> "$TEMP_CRONTAB"
# Every 2 hours, synchronize kol_character table
0 */2 * * * cd $PROJECT_DIR && python3 scripts/sync/sync_kol_character_only.py --lock-timeout 60 >> data/kol_character_sync.log 2>&1

# Every 2 hours, synchronize url_tracking table
30 */2 * * * cd $PROJECT_DIR && python3 scripts/sync/sync_url_tracking_only.py --lock-timeout 60 >> data/url_tracking_sync.log 2>&1

# Every hour, synchronize tweets table (with 30-day window)
0 */1 * * * cd $PROJECT_DIR && python3 scripts/sync/sync_tweets_only.py --since-days 30 --lock-timeout 60 >> data/tweets_sync.log 2>&1
EOF

# Install the new crontab
crontab "$TEMP_CRONTAB"

# Clean up
rm "$TEMP_CRONTAB"

echo "Crontab updated with separate synchronization scripts."
echo "KOL Character sync: Every 2 hours at minute 0"
echo "URL Tracking sync: Every 2 hours at minute 30"
echo "Tweets sync: Every hour at minute 0"
