#!/bin/bash
# Script to set up crontab entries for dynamic Twitter updates, activity analysis, and MySQL synchronization

# Get the absolute path to the nitterlocal directory
NITTER_DIR=$(cd "$(dirname "$0")/../.." && pwd)

# Create a temporary file for the new crontab
TEMP_CRONTAB=$(mktemp)

# Export the current crontab
crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "# New crontab file" > "$TEMP_CRONTAB"

# Check if the old entry exists and remove it
if grep -q "main.py --max-tweets 10 --max-replies 5" "$TEMP_CRONTAB"; then
    echo "Removing old Twitter update crontab entry..."
    sed -i '/main.py --max-tweets 10 --max-replies 5/d' "$TEMP_CRONTAB"
fi

# Check if the dynamic update entries already exist
if grep -q "scripts/activity/dynamic_update.py" "$TEMP_CRONTAB"; then
    echo "Dynamic update crontab entry already exists. Updating..."
    sed -i '/scripts\/activity\/dynamic_update.py/d' "$TEMP_CRONTAB"
fi

if grep -q "scripts/activity/analyze_activity.py" "$TEMP_CRONTAB"; then
    echo "Activity analysis crontab entry already exists. Updating..."
    sed -i '/scripts\/activity\/analyze_activity.py/d' "$TEMP_CRONTAB"
fi

if grep -q "scripts/sync/sync_to_mysql.py" "$TEMP_CRONTAB"; then
    echo "MySQL sync crontab entry already exists. Updating..."
    sed -i '/scripts\/sync\/sync_to_mysql.py/d' "$TEMP_CRONTAB"
fi

# Add the new entries
echo "# Every 6 hours analyze account activity levels" >> "$TEMP_CRONTAB"
echo "0 */6 * * * cd $NITTER_DIR && python3 scripts/activity/analyze_activity.py --days 7 >> data/activity_analysis.log 2>&1" >> "$TEMP_CRONTAB"

echo "# Every 15 minutes run dynamic update" >> "$TEMP_CRONTAB"
echo "*/15 * * * * cd $NITTER_DIR && python3 scripts/activity/dynamic_update.py --parallel --threads 3 --performance >> data/dynamic_update.log 2>&1" >> "$TEMP_CRONTAB"

echo "# Every hour sync to MySQL" >> "$TEMP_CRONTAB"
echo "5 * * * * cd $NITTER_DIR && python3 scripts/sync/sync_to_mysql.py --since-days 1 >> data/sync_cron.log 2>&1" >> "$TEMP_CRONTAB"

# Install the new crontab
crontab "$TEMP_CRONTAB"

# Clean up
rm "$TEMP_CRONTAB"

echo "Dynamic update crontab entries installed successfully."
echo "The following entries were added to your crontab:"
echo "0 */6 * * * cd $NITTER_DIR && python3 scripts/activity/analyze_activity.py --days 7 >> data/activity_analysis.log 2>&1"
echo "*/15 * * * * cd $NITTER_DIR && python3 scripts/activity/dynamic_update.py --parallel --threads 3 --performance >> data/dynamic_update.log 2>&1"
echo "5 * * * * cd $NITTER_DIR && python3 scripts/sync/sync_to_mysql.py --since-days 1 >> data/sync_cron.log 2>&1"
