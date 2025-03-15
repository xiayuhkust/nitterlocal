#!/bin/bash
# Script to set up crontab entries with lock mechanism for MySQL synchronization

# Get the absolute path to the nitterlocal directory
NITTER_DIR=$(cd "$(dirname "$0")/../.." && pwd)

# Create a temporary file for the new crontab
TEMP_CRONTAB=$(mktemp)

# Export the current crontab
crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "# New crontab file" > "$TEMP_CRONTAB"

# Check if the sync entries already exist and remove them
if grep -q "scripts/sync/sync_to_mysql_combined.py" "$TEMP_CRONTAB"; then
    echo "Removing existing sync_to_mysql_combined.py entry..."
    sed -i '/scripts\/sync\/sync_to_mysql_combined.py/d' "$TEMP_CRONTAB"
fi

if grep -q "scripts/sync/sync_to_mysql.py" "$TEMP_CRONTAB"; then
    echo "Removing existing sync_to_mysql.py entry..."
    sed -i '/scripts\/sync\/sync_to_mysql.py/d' "$TEMP_CRONTAB"
fi

# Add the new entry for sync_to_mysql_combined.py with lock mechanism
echo "# Every 15 minutes, synchronize to MySQL with lock mechanism" >> "$TEMP_CRONTAB"
echo "*/15 * * * * cd $NITTER_DIR && python3 scripts/sync/sync_to_mysql_combined.py --lock-timeout 60 >> data/sync_cron.log 2>&1" >> "$TEMP_CRONTAB"

# Install the new crontab
crontab "$TEMP_CRONTAB"

# Clean up
rm "$TEMP_CRONTAB"

echo "MySQL synchronization crontab entry with lock mechanism installed successfully."
echo "The following entry was added to your crontab:"
echo "*/15 * * * * cd $NITTER_DIR && python3 scripts/sync/sync_to_mysql_combined.py --lock-timeout 60 >> data/sync_cron.log 2>&1"
