# Usage Guide

This document provides detailed instructions on how to use the Twitter client daily update process.

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- Twitter credentials (username, password, email)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/xiayuhkust/nitterlocal.git
   cd nitterlocal
   ```

2. Install Node.js dependencies:
   ```
   cd src/twitter_client
   npm install
   ```

3. Create a `.env` file in the `src/twitter_client` directory with your Twitter credentials:
   ```
   TWITTER_USERNAME=your_username
   TWITTER_PASSWORD=your_password
   TWITTER_EMAIL=your_email
   ```

## Basic Usage

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

## Advanced Usage

Customize the daily update process:
```
python main.py --batch-size 5 --sleep 3 --max-tweets 30 --limit 20
```

### Command-line Arguments

- `--batch-size`: Number of URLs to process in each batch (default: 10)
- `--sleep`: Sleep time between URLs in seconds (default: 2)
- `--max-tweets`: Maximum number of tweets to extract per URL (default: 50)
- `--limit`: Limit the number of URLs to process (optional)
- `--db-path`: Path to the local database (default: data/local_database.db)

## Managing URLs

### Adding URLs

To add URLs to the database, you can use the `add_urls.py` script:
```
python add_urls.py --file data/sample_urls.json
```

Or add URLs programmatically:
```python
from src.database.local_database import LocalDatabase

db = LocalDatabase()
db.add_url('https://twitter.com/0xPolygon', description='Polygon', url_type='kol')
```

### Viewing URLs

To view URLs in the database, you can use the `view_urls.py` script:
```
python view_urls.py
```

Or view URLs programmatically:
```python
from src.database.local_database import LocalDatabase

db = LocalDatabase()
urls = db.get_urls()
for url in urls:
    print(url)
```

## Viewing Tweets

To view tweets in the database, you can use the `view_tweets.py` script:
```
python view_tweets.py
```

Or view tweets programmatically:
```python
from src.database.local_database import LocalDatabase

db = LocalDatabase()
tweets = db.get_tweets()
for tweet in tweets:
    print(tweet)
```

## Generating Statistics

To generate statistics from the database, you can use the `generate_stats.py` script:
```
python generate_stats.py
```

Or generate statistics programmatically:
```python
from src.database.local_database import LocalDatabase

db = LocalDatabase()
stats = db.generate_stats()
print(stats)
```

## Troubleshooting

### Twitter Client Issues

If you encounter issues with the Twitter client, check the following:
- Ensure your Twitter credentials are correct in the `.env` file
- Check if you're being rate-limited by Twitter
- Try increasing the sleep time between URLs

### Database Issues

If you encounter issues with the database, check the following:
- Ensure the database file exists and is accessible
- Check if the database schema is correct
- Try recreating the database if it's corrupted

## API Reference

### LocalDatabase

The `LocalDatabase` class provides the following methods:
- `__init__(db_path='data/local_database.db')`: Initialize the database
- `get_urls(status=None, limit=None)`: Get URLs from the database
- `get_tweets(source_url=None, limit=None)`: Get tweets from the database
- `store_tweets(tweets, source_url)`: Store tweets in the database
- `add_url(url, description="", url_type="kol")`: Add a URL to the database
- `update_url_status(url, status, error=None)`: Update the status of a URL
- `generate_stats()`: Generate statistics for the database

### URLManager

The `URLManager` class provides the following methods:
- `__init__(db_path='data/local_database.db')`: Initialize the URL manager
- `get_urls(status=None, limit=None)`: Get URLs from the database
- `add_url(url, description="", url_type="kol")`: Add a URL to the database
- `update_url_status(url, status, error=None)`: Update the status of a URL
- `update_last_scraped(url)`: Update the last_scraped timestamp for a URL
- `remove_url(url)`: Remove a URL from the database
- `update_tweet_count(url, count)`: Update the tweet count for a URL

### TwitterScraper

The `TwitterScraper` class provides the following methods:
- `__init__(client_dir=None)`: Initialize the Twitter scraper
- `extract_username_from_url(url)`: Extract the username from a URL
- `scrape_url(url, max_tweets=50)`: Scrape tweets from a URL
- `scrape_urls(urls, max_tweets=50, batch_size=10, sleep_between_urls=2)`: Scrape tweets from multiple URLs

### DailyUpdate

The `DailyUpdate` class provides the following methods:
- `__init__(db_path='data/local_database.db')`: Initialize the daily update
- `run(batch_size=10, sleep_between_urls=2, max_tweets=50, limit=None)`: Run the daily update
