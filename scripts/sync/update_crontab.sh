#!/bin/bash
# Script to update crontab configuration

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Create a temporary file for the new crontab
TEMP_CRONTAB=$(mktemp)

# Write the new crontab configuration
cat << EOF > "$TEMP_CRONTAB"
# 每6小时分析账号活跃度
0 */6 * * * cd $PROJECT_DIR && python3 scripts/activity/analyze_activity.py --days 7 >> data/activity_analysis.log 2>&1

# 每15分钟运行动态更新
*/15 * * * * cd $PROJECT_DIR && python3 scripts/activity/dynamic_update.py --parallel --threads 3 --performance >> data/dynamic_update.log 2>&1

# 每2小时同步kol_character表
0 */2 * * * cd $PROJECT_DIR && python3 scripts/sync/sync_kol_character_only.py --lock-timeout 60 >> data/kol_character_sync.log 2>&1

# 每2小时同步url_tracking表（错开30分钟）
30 */2 * * * cd $PROJECT_DIR && python3 scripts/sync/sync_url_tracking_only.py --lock-timeout 60 >> data/url_tracking_sync.log 2>&1

# 每15分钟同步tweets表（使用30天窗口）
*/15 * * * * cd $PROJECT_DIR && python3 scripts/sync/sync_tweets_only.py --since-days 30 --lock-timeout 60 >> data/tweets_sync.log 2>&1
EOF

# Display the new crontab configuration
echo "New crontab configuration:"
cat "$TEMP_CRONTAB"

# Check if crontab is installed
if command -v crontab >/dev/null 2>&1; then
    # Ask for confirmation
    read -p "Install this crontab configuration? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Install the new crontab
        crontab "$TEMP_CRONTAB"
        echo "Crontab configuration installed successfully."
    else
        echo "Crontab installation cancelled."
    fi
else
    echo "Crontab command not found. Please install crontab with:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install cron"
    echo ""
    echo "Alternatively, you can manually install this configuration when crontab is available."
    echo "The configuration has been saved to: $PROJECT_DIR/scripts/sync/crontab.txt"
    cp "$TEMP_CRONTAB" "$PROJECT_DIR/scripts/sync/crontab.txt"
fi

# Clean up
rm "$TEMP_CRONTAB"
