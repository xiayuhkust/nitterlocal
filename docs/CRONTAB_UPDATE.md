# Crontab Update Instructions

The synchronization script has been updated to retrieve comprehensive profile information for KOLs. Please update your crontab entry to use the new script:

## Current crontab entry:
```
*/15 * * * * cd /home/ubuntu/nitterlocal && python3 scripts/sync/sync_to_mysql_no_nodejs.py --since-days 1 >> data/sync_cron.log 2>&1
```

## New crontab entry:
```
*/15 * * * * cd /home/ubuntu/nitterlocal && python3 scripts/sync/sync_to_mysql_with_nodejs.py --since-days 1 >> data/sync_cron.log 2>&1
```

This change removes the `--no-nodejs` flag from the synchronization process, allowing the script to retrieve comprehensive profile information using the Node.js Twitter client.
