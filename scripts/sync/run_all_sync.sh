#!/bin/bash
# Script to manually run all synchronization scripts

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Change to the project directory
cd "$PROJECT_DIR"

echo "Starting synchronization at $(date)"
echo "----------------------------------------"

echo "Running kol_character synchronization..."
python3 scripts/sync/sync_kol_character_only.py --lock-timeout 60
if [ $? -ne 0 ]; then
    echo "Error: kol_character synchronization failed"
else
    echo "kol_character synchronization completed successfully"
fi
echo "----------------------------------------"

echo "Running url_tracking synchronization..."
python3 scripts/sync/sync_url_tracking_only.py --lock-timeout 60
if [ $? -ne 0 ]; then
    echo "Error: url_tracking synchronization failed"
else
    echo "url_tracking synchronization completed successfully"
fi
echo "----------------------------------------"

echo "Running tweets synchronization..."
python3 scripts/sync/sync_tweets_only.py --since-days 30 --lock-timeout 60
if [ $? -ne 0 ]; then
    echo "Error: tweets synchronization failed"
else
    echo "tweets synchronization completed successfully"
fi
echo "----------------------------------------"

echo "All synchronization scripts completed at $(date)"
