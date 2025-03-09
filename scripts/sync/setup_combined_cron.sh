#!/bin/bash
# Script to set up a combined crontab entry for Twitter updates and MySQL synchronization

# Get the absolute path to the nitterlocal directory
NITTER_DIR=$(cd "$(dirname "$0")/../.." && pwd)

# Create a temporary file for the new crontab
TEMP_CRONTAB=$(mktemp)

# Export the current crontab
crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "# New crontab file" > "$TEMP_CRONTAB"

# Check if the entry already exists
if grep -q "main.py --max-tweets 10 --max-replies 5" "$TEMP_CRONTAB"; then
    echo "Crontab entry for Twitter updates already exists. Updating..."
    # Remove the existing entry
    sed -i '/main.py --max-tweets 10 --max-replies 5/d' "$TEMP_CRONTAB"
fi

# Add the new combined entry
echo "# Run Twitter updates every 15 minutes and sync to MySQL immediately after" >> "$TEMP_CRONTAB"
echo "*/15 * * * * cd $NITTER_DIR && python3 main.py --max-tweets 10 --max-replies 5 >> data/cron.log 2>&1 && python3 scripts/sync/sync_to_mysql.py --since-days 1 >> data/sync_cron.log 2>&1" >> "$TEMP_CRONTAB"

# Install the new crontab
crontab "$TEMP_CRONTAB"

# Clean up
rm "$TEMP_CRONTAB"

echo "Combined crontab entry installed successfully."
echo "The following entry was added to your crontab:"
echo "*/15 * * * * cd $NITTER_DIR && python3 main.py --max-tweets 10 --max-replies 5 >> data/cron.log 2>&1 && python3 scripts/sync/sync_to_mysql.py --since-days 1 >> data/sync_cron.log 2>&1"
