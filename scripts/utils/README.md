# Twitter URL Crawler

This directory contains utility scripts for working with Twitter URLs and crawling tweets.

## Crawl URL Script

The `crawl_url.py` script allows you to crawl tweets from a Twitter URL using the core functionality of the project.

### Usage

```bash
python scripts/utils/crawl_url.py [URL] [options]
```

### Options

- `--max-tweets`: Maximum number of tweets to crawl (default: 30)
- `--max-replies`: Maximum number of replies to crawl (default: 10)
- `--output-format`: Output format ('json', 'text', or 'both') (default: 'json')
- `--output-file`: Output file path (if not specified, print to stdout)
- `--store-in-db`: Store tweets in the local database
- `--db-path`: Database path (default: data/local_database.db)

### Examples

```bash
# Crawl tweets from a URL and print to stdout in JSON format
python scripts/utils/crawl_url.py https://twitter.com/elonmusk

# Crawl tweets from a URL and save to a file in text format
python scripts/utils/crawl_url.py https://twitter.com/elonmusk --output-format text --output-file tweets.txt

# Crawl tweets from a URL with custom tweet quantities
python scripts/utils/crawl_url.py https://twitter.com/elonmusk --max-tweets 50 --max-replies 20

# Crawl tweets from a URL and store in database
python scripts/utils/crawl_url.py https://twitter.com/elonmusk --store-in-db
```

## Other Utility Scripts

- `url_utils.py`: Utility functions for working with URLs
  - `convert_nitter_to_twitter()`: Convert a Nitter URL to a Twitter URL
  - `extract_twitter_handle()`: Extract Twitter handle from a URL

## Integration with Other Scripts

The URL crawler can be integrated with other scripts in the project:

```python
from scripts.utils.crawl_url import crawl_url

# Crawl tweets from a URL
result = crawl_url(
    'https://twitter.com/elonmusk',
    max_tweets=30,
    max_replies=10,
    output_format='json'
)

# Access the tweets
tweets = result['tweets']
```
