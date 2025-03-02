# Sample Data

This directory contains sample data for the Twitter client daily update process.

## Files

- `sample_urls.json`: Sample URLs to track
- `local_database.db`: SQLite database for storing tweets
- `local_stats.json`: Statistics generated from the database
- `end_to_end_stats.json`: Statistics generated from the end-to-end test
- `daily_update.log`: Log file for the daily update process

## Sample URLs

The `sample_urls.json` file contains sample URLs to track:

```json
{
  "urls": [
    {
      "url": "https://twitter.com/0xPolygon",
      "description": "Polygon - Ethereum scaling platform",
      "type": "kol"
    },
    {
      "url": "https://twitter.com/elonmusk",
      "description": "Elon Musk - CEO of Tesla and SpaceX",
      "type": "kol"
    },
    {
      "url": "https://twitter.com/vitalikbuterin",
      "description": "Vitalik Buterin - Ethereum co-founder",
      "type": "kol"
    }
  ]
}
```

## Database Schema

The SQLite database uses the following schema:

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

### backup_log

Logs backup operations:
- `id`: Log ID (primary key)
- `timestamp`: Timestamp of the operation
- `operation`: Operation performed
- `details`: Details of the operation
- `success`: Success status (1 for success, 0 for failure)
