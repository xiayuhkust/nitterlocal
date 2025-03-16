#!/bin/bash
# Script to run initial tweet crawl with fixed tweet quantities
# This script:
# 1. Sets up the activity_levels table with fixed tweet quantities (30 regular tweets, 10 reply tweets)
# 2. Runs the dynamic_update.py script with parallel processing and performance monitoring

# Change to the project root directory
cd "$(dirname "$0")/../.."

# Set up logging
LOG_FILE="data/initial_crawl.log"
echo "$(date) - Starting initial tweet crawl" | tee -a "$LOG_FILE"

# Process command line arguments
LIMIT=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --limit)
            LIMIT="--limit $2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--limit N]"
            exit 1
            ;;
    esac
done

# Set up the activity_levels table with fixed tweet quantities
echo "$(date) - Setting up activity_levels table with fixed tweet quantities" | tee -a "$LOG_FILE"
sqlite3 data/local_database.db < scripts/database/setup_initial_crawl.sql | tee -a "$LOG_FILE"

# Run the dynamic_update.py script with parallel processing and performance monitoring
echo "$(date) - Running dynamic_update.py with parallel processing" | tee -a "$LOG_FILE"
python3 scripts/activity/dynamic_update.py --parallel --threads 3 --performance $LIMIT | tee -a "$LOG_FILE"

# Check the results
echo "$(date) - Initial tweet crawl completed" | tee -a "$LOG_FILE"
echo "$(date) - Checking results" | tee -a "$LOG_FILE"
sqlite3 data/local_database.db "SELECT COUNT(*) AS total_tweets FROM tweets;" | tee -a "$LOG_FILE"

echo "$(date) - Initial tweet crawl process finished" | tee -a "$LOG_FILE"
