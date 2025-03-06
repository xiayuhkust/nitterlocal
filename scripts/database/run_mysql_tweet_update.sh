#!/bin/bash
# Shell script wrapper for update_mysql_kol_tweet.py
# This script sets the environment variables and runs the update script

# Set MySQL connection parameters
export MYSQL_HOST="43.135.26.222"
export MYSQL_PORT="3306"
export MYSQL_USER="root"
export MYSQL_PASSWORD="z1050493759"
export MYSQL_DATABASE="kol_info"

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Parse command line arguments
LIMIT=""
SINCE_DAYS=""
TEST_MODE=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --limit)
      LIMIT="--limit $2"
      shift 2
      ;;
    --since-days)
      SINCE_DAYS="--since-days $2"
      shift 2
      ;;
    --test)
      TEST_MODE="--test"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--limit N] [--since-days N] [--test]"
      exit 1
      ;;
  esac
done

# Run the update script
echo "Running update_mysql_kol_tweet.py with parameters: $LIMIT $SINCE_DAYS $TEST_MODE"
python "$SCRIPT_DIR/update_mysql_kol_tweet.py" $LIMIT $SINCE_DAYS $TEST_MODE
