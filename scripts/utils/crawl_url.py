#!/usr/bin/env python3
"""
Script to crawl tweets from a provided URL.
This script uses the core Twitter scraping functionality to extract tweets from a URL.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import required modules
from src.twitter_client.twitter_scraper import TwitterScraper
from src.database.local_database import LocalDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def crawl_url(url, max_tweets=30, max_replies=10, output_format='json', output_file=None):
    """
    Crawl tweets from a URL
    
    Args:
        url (str): Twitter URL to crawl
        max_tweets (int): Maximum number of tweets to crawl
        max_replies (int): Maximum number of replies to crawl
        output_format (str): Output format ('json', 'text', or 'both')
        output_file (str): Output file path (if None, print to stdout)
        
    Returns:
        dict: Result containing tweets and metadata
    """
    logging.info(f"Crawling URL: {url}")
    logging.info(f"Max tweets: {max_tweets}, Max replies: {max_replies}")
    
    # Initialize the Twitter scraper
    scraper = TwitterScraper()
    
    # Scrape the URL
    start_time = datetime.now()
    tweets = scraper.scrape_url(url, max_tweets=max_tweets, max_replies=max_replies)
    end_time = datetime.now()
    
    # Extract username from URL
    username = scraper.extract_username_from_url(url)
    
    # Prepare result
    result = {
        'url': url,
        'username': username,
        'tweet_count': len(tweets),
        'crawl_time': (end_time - start_time).total_seconds(),
        'max_tweets': max_tweets,
        'max_replies': max_replies,
        'crawled_at': datetime.now().isoformat(),
        'tweets': tweets
    }
    
    # Output result
    if output_file:
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            if output_format == 'json' or output_format == 'both':
                json.dump(result, f, ensure_ascii=False, indent=2)
                logging.info(f"JSON output written to {output_file}")
            
            if output_format == 'text' or output_format == 'both':
                f.write(f"URL: {url}\n")
                f.write(f"Username: {username}\n")
                f.write(f"Tweet count: {len(tweets)}\n")
                f.write(f"Crawl time: {result['crawl_time']:.2f} seconds\n")
                f.write(f"Crawled at: {result['crawled_at']}\n\n")
                
                for i, tweet in enumerate(tweets, 1):
                    f.write(f"Tweet {i}:\n")
                    f.write(f"ID: {tweet.get('tweet_id', 'N/A')}\n")
                    f.write(f"Content: {tweet.get('content', 'N/A')}\n")
                    f.write(f"Created at: {tweet.get('created_at', 'N/A')}\n")
                    f.write(f"Likes: {tweet.get('likes', 0)}\n")
                    f.write(f"Retweets: {tweet.get('retweets', 0)}\n")
                    f.write(f"Replies: {tweet.get('replies', 0)}\n")
                    f.write(f"Views: {tweet.get('views', 0)}\n")
                    f.write(f"Is reply: {'Yes' if tweet.get('is_reply', 0) == 1 else 'No'}\n")
                    if tweet.get('hashtags'):
                        f.write(f"Hashtags: {', '.join(tweet.get('hashtags', []))}\n")
                    f.write("\n")
                
                logging.info(f"Text output written to {output_file}")
    else:
        # Print to stdout
        if output_format == 'json' or output_format == 'both':
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if output_format == 'text' or output_format == 'both':
            print(f"URL: {url}")
            print(f"Username: {username}")
            print(f"Tweet count: {len(tweets)}")
            print(f"Crawl time: {result['crawl_time']:.2f} seconds")
            print(f"Crawled at: {result['crawled_at']}")
            print()
            
            for i, tweet in enumerate(tweets, 1):
                print(f"Tweet {i}:")
                print(f"ID: {tweet.get('tweet_id', 'N/A')}")
                print(f"Content: {tweet.get('content', 'N/A')}")
                print(f"Created at: {tweet.get('created_at', 'N/A')}")
                print(f"Likes: {tweet.get('likes', 0)}")
                print(f"Retweets: {tweet.get('retweets', 0)}")
                print(f"Replies: {tweet.get('replies', 0)}")
                print(f"Views: {tweet.get('views', 0)}")
                print(f"Is reply: {'Yes' if tweet.get('is_reply', 0) == 1 else 'No'}")
                if tweet.get('hashtags'):
                    print(f"Hashtags: {', '.join(tweet.get('hashtags', []))}")
                print()
    
    return result

def store_tweets_in_database(url, tweets, db_path='data/local_database.db'):
    """
    Store tweets in the local database
    
    Args:
        url (str): Twitter URL
        tweets (list): List of tweets
        db_path (str): Database path
        
    Returns:
        int: Number of tweets stored
    """
    logging.info(f"Storing {len(tweets)} tweets in database")
    
    # Initialize the database
    database = LocalDatabase(db_path=db_path)
    
    # Store tweets
    stored_count = database.store_tweets(tweets, url)
    
    logging.info(f"Stored {stored_count} tweets in database")
    
    return stored_count

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Crawl tweets from a Twitter URL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crawl tweets from a URL and print to stdout in JSON format
  python crawl_url.py https://twitter.com/elonmusk
  
  # Crawl tweets from a URL and save to a file in text format
  python crawl_url.py https://twitter.com/elonmusk --output-format text --output-file tweets.txt
  
  # Crawl tweets from a URL with custom tweet quantities
  python crawl_url.py https://twitter.com/elonmusk --max-tweets 50 --max-replies 20
  
  # Crawl tweets from a URL and store in database
  python crawl_url.py https://twitter.com/elonmusk --store-in-db
"""
    )
    
    parser.add_argument(
        'url',
        type=str,
        help='Twitter URL to crawl'
    )
    
    parser.add_argument(
        '--max-tweets',
        type=int,
        default=30,
        help='Maximum number of tweets to crawl (default: 30)'
    )
    
    parser.add_argument(
        '--max-replies',
        type=int,
        default=10,
        help='Maximum number of replies to crawl (default: 10)'
    )
    
    parser.add_argument(
        '--output-format',
        type=str,
        choices=['json', 'text', 'both'],
        default='json',
        help='Output format (default: json)'
    )
    
    parser.add_argument(
        '--output-file',
        type=str,
        help='Output file path (if not specified, print to stdout)'
    )
    
    parser.add_argument(
        '--store-in-db',
        action='store_true',
        help='Store tweets in the local database'
    )
    
    parser.add_argument(
        '--db-path',
        type=str,
        default='data/local_database.db',
        help='Database path (default: data/local_database.db)'
    )
    
    args = parser.parse_args()
    
    # Crawl URL
    result = crawl_url(
        args.url,
        max_tweets=args.max_tweets,
        max_replies=args.max_replies,
        output_format=args.output_format,
        output_file=args.output_file
    )
    
    # Store tweets in database if requested
    if args.store_in_db:
        store_tweets_in_database(args.url, result['tweets'], db_path=args.db_path)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
