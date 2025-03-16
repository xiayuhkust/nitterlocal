# Twitter Data Extraction and Backend Service

This project provides tools for extracting and analyzing Twitter data, as well as a backend service for processing Excel files with Twitter URLs.

## Overview

The system extracts tweets from Twitter accounts and stores them in a local database for analysis. It supports various types of Twitter accounts, including KOLs (Key Opinion Leaders), institutions, exchanges, and meme tokens. The backend service allows users to upload Excel files containing Twitter URLs, process them, and update the local database.

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- Twitter credentials (username, password, email)
- MySQL database for synchronization

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/xiayuhkust/nitterlocal.git
   cd nitterlocal
   ```

2. Install Python dependencies:
   ```
   pip install -r app/requirements.txt
   ```

3. Create a `.env` file in the root directory with your credentials:
   ```
   TWITTER_USERNAME=your_username
   TWITTER_PASSWORD=your_password
   TWITTER_EMAIL=your_email
   MYSQL_HOST=your_mysql_host
   MYSQL_PORT=3306
   MYSQL_USER=your_mysql_user
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DATABASE=your_mysql_database
   ```

## URL Format

The system uses Twitter URLs (https://twitter.com/username) instead of Nitter URLs.
All existing URLs in the database will be automatically converted to Twitter format when running the migration script.

### Migration

To migrate existing URLs in the database from Nitter to Twitter format, run:

```bash
python scripts/migrations/convert_urls_to_twitter.py
```

To verify that all URLs have been converted to Twitter format, run:

```bash
python scripts/tests/test_url_migration.py
```

### Adding URLs

When adding new URLs, use the Twitter format (https://twitter.com/username):

```bash
python scripts/utils/add_urls.py --file data/sample_urls_with_cmc.json
```

## Database Schema

The database schema includes the following tables:

- `url_tracking`: Stores information about Twitter URLs to track
- `tweets`: Stores tweets extracted from the tracked URLs
- `kol_character`: Stores character information for KOLs

## Data Analysis

The system provides various tools for analyzing the extracted tweets:

- Count tweets per URL
- Analyze hashtags
- Export tweets to JSON or CSV
- Remove duplicate tweets

For detailed data analysis instructions:

1. Count tweets per URL:
   ```bash
   python scripts/analysis/count_tweets.py
   ```

2. Analyze hashtags:
   ```bash
   python scripts/analysis/analyze_hashtags.py
   ```

3. Export tweets to JSON:
   ```bash
   python scripts/export/export_tweets_to_json.py --output data/tweets.json
   ```

4. Remove duplicate tweets:
   ```bash
   python scripts/cleanup/remove_duplicate_tweets.py
   ```

## CoinMarketCap Integration

The system can fetch top exchanges and meme tokens from CoinMarketCap and add them to the database:

```bash
python scripts/utils/fetch_coinmarketcap_data.py
```

## Twitter Client

The system uses a Twitter client to extract tweets directly from Twitter. The client requires authentication credentials to be set in the `.env` file.

### Basic Usage

Run the daily update process with default settings:
```
python main.py
```

This will:
1. Get active URLs from the database
2. Process URLs in batches of 10
3. Extract up to 50 tweets per URL
4. Store tweets in the database
5. Generate statistics

### Advanced Usage

Customize the daily update process:
```bash
python main.py --batch-size 20 --tweets-per-url 100
```

## Backend Service

The project includes a FastAPI backend service for processing Excel files with Twitter URLs.

### Installation

```bash
cd nitterlocal
pip install -r app/requirements.txt
```

### Starting the Backend

```bash
./start_backend.sh
```

The backend service will be available at http://0.0.0.0:8000

### Features

- Upload Excel files containing Twitter URLs
- Extract Twitter user IDs from URLs
- Process and update local database tables (url_tracking and kol_character)
- Synchronize data with MySQL database
- Download processed Excel files with extracted IDs

### Systemd Service

For production use, it's recommended to run the backend service using systemd:

1. Install the service:
   ```bash
   sudo ./install_service.sh
   ```

2. Start the service:
   ```bash
   sudo systemctl start nitterlocal-backend
   ```

3. Check the service status:
   ```bash
   sudo systemctl status nitterlocal-backend
   ```

4. Enable the service to start on boot:
   ```bash
   sudo systemctl enable nitterlocal-backend
   ```

5. View service logs:
   ```bash
   sudo journalctl -u nitterlocal-backend
   ```

6. Uninstall the service:
   ```bash
   sudo ./uninstall_service.sh
   ```

## Crontab Configuration

The system uses crontab to schedule regular tasks. If crontab is not installed, you can install it with:

```bash
sudo apt-get update
sudo apt-get install cron
```

The recommended crontab configuration is:

```
# 每6小时分析账号活跃度
0 */6 * * * cd /home/ubuntu/nitterlocal && python3 scripts/activity/analyze_activity.py --days 7 >> data/activity_analysis.log 2>&1

# 每15分钟运行动态更新
*/15 * * * * cd /home/ubuntu/nitterlocal && python3 scripts/activity/dynamic_update.py --parallel --threads 3 --performance >> data/dynamic_update.log 2>&1

# 每2小时同步kol_character表
0 */2 * * * cd /home/ubuntu/nitterlocal && python3 scripts/sync/sync_kol_character_only.py --lock-timeout 60 >> data/kol_character_sync.log 2>&1

# 每2小时同步url_tracking表（错开30分钟）
30 */2 * * * cd /home/ubuntu/nitterlocal && python3 scripts/sync/sync_url_tracking_only.py --lock-timeout 60 >> data/url_tracking_sync.log 2>&1

# 每15分钟同步tweets表（使用30天窗口）
*/15 * * * * cd /home/ubuntu/nitterlocal && python3 scripts/sync/sync_tweets_only.py --since-days 30 --lock-timeout 60 >> data/tweets_sync.log 2>&1
```

To update the crontab configuration:
```bash
./scripts/sync/update_crontab.sh
```

If crontab is not available, you can manually install the configuration from the provided file:
```bash
crontab scripts/sync/crontab.txt
```

## MySQL Synchronization

The system synchronizes data from the local SQLite database to a MySQL database. The synchronization process handles the `kol_character`, `url_tracking`, and `tweets` tables.

### Synchronization Script

The main synchronization script is `scripts/sync/sync_to_mysql_combined.py`. This script:

1. Connects to both the local SQLite database and the remote MySQL database
2. Synchronizes the `kol_character` table
3. Synchronizes the `url_tracking` table to the `kol_info` table in MySQL
4. Synchronizes the `tweets` table to the `kol_tweet` table in MySQL
5. Handles column name differences between SQLite and MySQL
6. Uses a lock mechanism to prevent overlapping executions
7. Implements dynamic column mapping to handle different table structures

### Lock Mechanism

The synchronization process uses a file-based lock mechanism to prevent multiple synchronization jobs from running simultaneously. This is especially important as data volume grows and synchronization takes longer than the cron interval.

Key features of the lock mechanism:
- Uses file locking with `fcntl` to prevent overlapping executions
- Includes timeout functionality to prevent indefinite waiting
- Stores the process ID (PID) in the lock file for debugging
- Gracefully handles lock acquisition failures

### Manual Synchronization

To manually trigger synchronization:
```bash
python scripts/sync/sync_to_mysql_combined.py
```

To run in test mode (no actual changes):
```bash
python scripts/sync/sync_to_mysql_combined.py --test
```

To only synchronize tweets:
```bash
python scripts/sync/sync_to_mysql_combined.py --tweets-only
```

To synchronize with a specific time window:
```bash
python scripts/sync/sync_to_mysql_combined.py --since-days 30
```

To disable the lock mechanism:
```bash
python scripts/sync/sync_to_mysql_combined.py --no-lock
```

To set a custom lock timeout (in seconds):
```bash
python scripts/sync/sync_to_mysql_combined.py --lock-timeout 120
```

### Error Handling

The synchronization script includes robust error handling:
- Gracefully handles missing columns in MySQL tables
- Uses dynamic column mapping to only synchronize compatible columns
- Falls back to user_id when kol_id lookup fails
- Provides detailed logging of synchronization operations
- Handles "Unread result found" errors automatically

### Database Check Tools

The system includes tools to check the status of both the local SQLite database and the remote MySQL database:

To check the latest tweets in the local SQLite database:
```bash
python scripts/sync/check_local_tweets.py
```

To check the latest tweets in the MySQL database:
```bash
python scripts/sync/check_mysql_tweets.py
```

To check the schema of MySQL tables:
```bash
python scripts/sync/check_mysql_schema.py kol_tweet
```

To check the schema of SQLite tables:
```bash
python scripts/sync/check_sqlite_tables.py tweets
```

These tools help diagnose synchronization issues by showing the most recent tweets, total tweet counts, and tweet distribution by date.

### Troubleshooting

If you encounter synchronization issues:

1. Check the MySQL connection parameters in the `.env` file
2. Verify that the MySQL server is accessible
3. Check the column names in both databases
4. Review the synchronization logs in `data/sync_cron.log`
5. Check the detailed logs in `data/logs/sync_details.log`
6. Check if a lock file exists at `data/sync_lock.pid` and remove it if no synchronization is running
7. Use the database check tools to compare local and remote data
8. Verify that the tweets table in SQLite has recent data

Common warnings that can be safely ignored:
- "Could not find kol_id for screen_name" - The system will use user_id as a fallback
- "Unread result found" - This is handled automatically by the synchronization script
- "Error getting numeric ID for handle" - Alternative ID lookup methods are used

## URL Table Regeneration

If you need to regenerate the URL tracking table:

1. Backup the current database:
   ```bash
   cp data/local_database.db data/local_database.backup.db
   ```

2. Run the regeneration script:
   ```bash
   python scripts/database/regenerate_url_table.py
   ```

3. Verify the regeneration:
   ```bash
   python scripts/tests/test_url_table.py
   ```

## Server IP Configuration

If you encounter issues with the server IP binding:

1. Check the current server IP:
   ```bash
   ./check_server_ip.sh
   ```

2. Update the systemd service file with the correct IP address
3. Restart the service:
   ```bash
   sudo systemctl restart nitterlocal-backend
   ```

## Testing

The project includes various test scripts in the `scripts/tests` directory:

```bash
# Run all tests
python -m unittest discover scripts/tests

# Run a specific test
python scripts/tests/test_database.py
```

## Simplified Workflow

For a simplified workflow:

1. User uploads Excel file through the web interface
2. System processes the file and updates the local SQLite database
3. Crontab job synchronizes data to MySQL every 15 minutes
4. User can manually trigger synchronization if needed

This approach provides faster response times and reduces the chance of synchronization failures.
