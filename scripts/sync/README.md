# Cross-Server Synchronization

This directory contains scripts for synchronizing Twitter data from the SQLite database on the Ubuntu server (242ubuntu) to the MySQL database on the CentOS server (222cenos).

## Overview

The synchronization process involves two main steps:
1. Synchronizing KOL (Key Opinion Leader) information from the `url_tracking` table in SQLite to the `kol_info` table in MySQL
2. Synchronizing tweets from the `tweets` table in SQLite to the `kol_tweet` table in MySQL

## Prerequisites

- Python 3.6 or higher
- MySQL Connector for Python (`pip install mysql-connector-python`)
- Python dotenv (`pip install python-dotenv`)
- Properly configured `.env` file with MySQL connection parameters

## Configuration

Create a `.env` file in the project root directory with the following content:

```
MYSQL_HOST=43.135.26.222
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=kol_info
```

Replace `your_password_here` with the actual MySQL password.

## Usage

### Basic Synchronization

To run a full synchronization:

```bash
python3 scripts/sync/sync_to_mysql.py
```

This will synchronize all KOL information and tweets from SQLite to MySQL.

### Test Mode

To test the synchronization without actually inserting or updating records in MySQL:

```bash
python3 scripts/sync/sync_to_mysql.py --test
```

### Limiting Records

To limit the number of records to process:

```bash
python3 scripts/sync/sync_to_mysql.py --limit 100
```

### Synchronizing Only KOL Information

To synchronize only KOL information:

```bash
python3 scripts/sync/sync_to_mysql.py --kol-only
```

### Synchronizing Only Tweets

To synchronize only tweets:

```bash
python3 scripts/sync/sync_to_mysql.py --tweets-only
```

### Synchronizing Recent Tweets

To synchronize only tweets from the last N days:

```bash
python3 scripts/sync/sync_to_mysql.py --tweets-only --since-days 7
```

## Automated Synchronization

To set up automated synchronization, add a cron job:

```bash
crontab -e
```

Add the following line to run synchronization every hour:

```
0 * * * * cd /home/ubuntu/nitterlocal && python3 scripts/sync/sync_to_mysql.py --since-days 1 >> data/sync_cron.log 2>&1
```

## Troubleshooting

### Missing user_id Column

The current SQLite schema does not have a `user_id` column, but the synchronization scripts are designed to work with this limitation by extracting Twitter handles from URLs.

### Connection Issues

If you encounter connection issues:
1. Verify that the MySQL server is running on the CentOS server
2. Check that the MySQL user has appropriate permissions
3. Ensure that the firewall allows connections from the Ubuntu server to the MySQL port on the CentOS server

### Script Errors

If you encounter script errors:
1. Check the log file at `data/sync_log.log` for detailed error messages
2. Verify that all required Python packages are installed
3. Ensure that the `.env` file contains the correct MySQL connection parameters

## Implementation Details

The synchronization process uses two main scripts:

1. `update_mysql_kol_info_no_nodejs.py`: Synchronizes KOL information
   - Extracts Twitter handles from URLs
   - Generates numeric IDs for MySQL compatibility
   - Maps SQLite fields to MySQL fields

2. `update_mysql_kol_tweet_server_py36.py`: Synchronizes tweets
   - Uses author field as kol_id
   - Converts date formats from SQLite to MySQL
   - Maps SQLite fields to MySQL fields

These scripts are wrapped by `sync_to_mysql.py` for easier usage and logging.
