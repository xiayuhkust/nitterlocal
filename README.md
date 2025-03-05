# Twitter Client Daily Update

This project provides a daily update process that uses the agent-twitter-client library to extract tweets from Twitter URLs stored in a local database.

## Features

- Extract tweets from Twitter URLs using agent-twitter-client
- Store tweets in a local SQLite database
- Process URLs in batches to avoid rate limits
- Support for extracting up to 50 tweets per URL
- Command-line interface for customizing the update process

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

## Usage

Run the daily update process:
```
python main.py
```

Customize the update process:
```
python main.py --batch-size 5 --sleep 3 --max-tweets 30 --limit 20
```

### Command-line Arguments

- `--batch-size`: Number of URLs to process in each batch (default: 10)
- `--sleep`: Sleep time between URLs in seconds (default: 2)
- `--max-tweets`: Maximum number of tweets to extract per URL (default: 50)
- `--limit`: Limit the number of URLs to process (optional)
- `--db-path`: Path to the local database (default: data/local_database.db)

## Project Structure

- `src/database`: Database module for storing tweets and managing URLs
- `src/twitter_client`: Twitter client module for extracting tweets
- `src/daily_update`: Daily update module for processing URLs in batches
- `data`: Directory for storing the SQLite database and other data files
- `config`: Configuration files for the application

## Database Schema

The local database uses SQLite with the following tables:

### url_tracking

Stores URL metadata:
- `url`: URL to track (primary key)
- `description`: Description of the URL
- `status`: Status of the URL (active, error, etc.)
- `last_checked`: Timestamp of the last check
- `error_count`: Number of errors encountered
- `tweet_count`: Number of tweets extracted
- `type`: Type of URL (kol, media, etc.)
- `added_at`: Timestamp when the URL was added
- `last_scraped`: Timestamp of the last scrape
- `last_error`: Last error message
- `user_id`: Twitter's unique user ID for the account

### tweets

Stores individual tweet information:
- `tweet_id`: Tweet ID (primary key)
- `source_url`: Source URL of the tweet
- `content`: Content of the tweet
- `created_at`: Timestamp when the tweet was created
- `author`: Author of the tweet
- `likes`: Number of likes
- `retweets`: Number of retweets
- `replies`: Number of replies
- `views`: Number of views
- `stored_at`: Timestamp when the tweet was stored

### hashtags

Stores hashtags from tweets:
- `id`: Hashtag entry ID (primary key)
- `tweet_id`: Foreign key referencing the tweets table
- `hashtag`: The hashtag text (without the # symbol)
- `stored_at`: Timestamp when the hashtag was stored

This table has a many-to-one relationship with the tweets table, allowing multiple hashtags per tweet. The `tweet_id` column has a foreign key constraint with CASCADE delete, ensuring that when a tweet is deleted, its associated hashtags are also removed. The `hashtag` column is indexed for faster queries.

### backup_log

Logs backup operations:
- `id`: Log ID (primary key)
- `timestamp`: Timestamp of the operation
- `operation`: Operation performed
- `details`: Details of the operation
- `success`: Success status (1 for success, 0 for failure)

## Twitter Client

The Twitter client uses the agent-twitter-client library to extract tweets from Twitter URLs. It requires Twitter credentials to authenticate with Twitter.

### Twitter Scraper

The Twitter scraper provides the following functionality:
- Extract usernames from URLs
- Scrape tweets from URLs
- Process tweets in batches
- Handle rate limits and errors

## Daily Update Process

The daily update process performs the following steps:
1. Get active URLs from the database
2. Process URLs in batches
3. Extract tweets from each URL
4. Store tweets in the database
5. Update URL metadata
6. Generate statistics

## License

This project is licensed under the MIT License.
