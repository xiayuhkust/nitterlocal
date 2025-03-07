# Server Setup Instructions for MySQL Tweet Sync

This document provides instructions for setting up and running the MySQL tweet sync script on the server.

## 1. Install Required Python Packages

First, install the required Python packages:

```bash
pip3 install mysql-connector-python
pip3 install python-dotenv
```

## 2. Create .env File

Create a .env file in the project root directory with the MySQL connection parameters:

```bash
cat > .env << EOL
MYSQL_HOST=43.135.26.222
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=kol_info
EOL
```

## 3. Test the Script

Test the script with the --test flag to ensure it can retrieve tweets from SQLite without inserting them into MySQL:

```bash
python3 scripts/database/update_mysql_kol_tweet.py --test --limit 5
```

You should see output similar to:

```
Starting MySQL update script for tweets
MySQL Host: 43.135.26.222
MySQL Port: 3306
MySQL User: root
MySQL Database: kol_info
SQLite Database: /path/to/data/local_database.db
Got 5 tweets from SQLite
Test mode - not connecting to MySQL database
Test mode - would insert or update record for kol_id: cz_binance, tweet_id: 1614148296788041734
...
Processed 5 tweets
MySQL update script for tweets completed
```

## 4. Run the Script

If the test is successful, run the script without the --test flag to insert tweets into MySQL:

```bash
python3 scripts/database/update_mysql_kol_tweet.py --limit 10
```

You can also run the script without a limit to process all tweets:

```bash
python3 scripts/database/update_mysql_kol_tweet.py
```

## 5. Check the MySQL Database

Check the MySQL database to ensure that the tweets are correctly inserted:

```bash
mysql -h 43.135.26.222 -u root -p -e "SELECT * FROM kol_info.kol_tweet LIMIT 10;"
```

Enter the password when prompted.

## 6. Troubleshooting

If you encounter any issues:

1. Check that the .env file exists and contains the correct MySQL connection parameters
2. Verify that the SQLite database exists and contains tweets
3. Ensure that the MySQL database and kol_tweet table exist
4. Check the logs for any error messages

## 7. Running with Different Options

The script supports the following command-line options:

- `--limit N`: Limit the number of tweets to process to N
- `--since-days N`: Only process tweets from the last N days
- `--test`: Test mode - do not insert or update records in MySQL

For example, to process only tweets from the last 7 days:

```bash
python3 scripts/database/update_mysql_kol_tweet.py --since-days 7
```
