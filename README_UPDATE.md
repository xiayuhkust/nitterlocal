# Tweet Extraction Pipeline

This update adds a new tweet extraction pipeline that separates the tweet scraping and database storage functionality to avoid SQLite thread safety issues in parallel processing mode.

## New Scripts

### 1. `scripts/activity/separate_tweet_scraper.py`
- Extracts tweets from Twitter URLs and saves them to JSON files
- Supports both sequential and parallel processing modes
- Thread-safe implementation that avoids SQLite cross-thread access issues
- Includes performance monitoring

### 2. `scripts/activity/store_tweets.py`
- Processes JSON files containing tweets and stores them in the database
- Creates a new SQLite connection for each database operation
- Thread-safe implementation

### 3. `scripts/activity/tweet_extraction_pipeline.py`
- Runs both the separate tweet scraper and tweet storer in sequence
- Provides a unified interface for the complete extraction process

## Usage

```bash
# Run the complete pipeline with parallel processing
python3 scripts/activity/tweet_extraction_pipeline.py --parallel --threads 3 --performance

# Run just the tweet scraper
python3 scripts/activity/separate_tweet_scraper.py --parallel --threads 3 --performance

# Run just the tweet storer
python3 scripts/activity/store_tweets.py
```

## Testing

The scripts have been tested with both sequential and parallel processing modes, successfully extracting and storing tweets from Twitter URLs.

Test results:
- Successfully extracted tweets from cz_binance account
- Properly stored tweets in the database
- No SQLite thread safety issues in parallel mode
