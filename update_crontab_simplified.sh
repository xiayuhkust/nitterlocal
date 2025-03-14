#!/bin/bash

# Script to update crontab with simplified synchronization approach

echo "Updating crontab with simplified synchronization approach..."

# Create a temporary file with the new crontab entries
cat > /tmp/new_crontab.txt << 'EOF'
# Nitterlocal crontab entries

# Analyze account activity every 6 hours
0 */6 * * * cd /home/ubuntu/nitterlocal && python3 scripts/activity/analyze_activity.py --days 7 >> data/activity_analysis.log 2>&1

# Run dynamic updates every 15 minutes
*/15 * * * * cd /home/ubuntu/nitterlocal && python3 scripts/activity/dynamic_update.py --parallel --threads 3 --performance >> data/dynamic_update.log 2>&1

# Synchronize to MySQL every 15 minutes (combined script that handles both url_tracking and kol_character)
*/15 * * * * cd /home/ubuntu/nitterlocal && python3 scripts/sync/sync_to_mysql_combined.py --since-days 1 >> data/sync_cron.log 2>&1
EOF

# Display the new crontab entries
echo "New crontab entries:"
cat /tmp/new_crontab.txt

echo -e "\nTo update your crontab, run:"
echo "crontab -l | grep -v 'nitterlocal' > /tmp/current_crontab.txt"
echo "cat /tmp/new_crontab.txt >> /tmp/current_crontab.txt"
echo "crontab /tmp/current_crontab.txt"
echo "rm /tmp/current_crontab.txt /tmp/new_crontab.txt"

echo -e "\nThis will replace all existing nitterlocal crontab entries with the new ones."
echo "The new setup uses the combined sync script that handles both url_tracking and kol_character tables."
