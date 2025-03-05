#!/usr/bin/env python3
"""
Wrapper script for data analysis tools.
This script provides a unified interface for all data analysis tools.
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Add the project root and scripts directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Data analysis tools for the Twitter client')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Remove duplicates command
    remove_parser = subparsers.add_parser('remove-duplicates', help='Remove duplicate tweets')
    remove_parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    remove_parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making changes')
    
    # Count tweets command
    count_parser = subparsers.add_parser('count-tweets', help='Count tweets per URL')
    count_parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    count_parser.add_argument('--format', type=str, choices=['text', 'json'], default='text', help='Output format')
    count_parser.add_argument('--output', type=str, help='Output file path')
    count_parser.add_argument('--limit', type=int, help='Limit the number of URLs to display')
    
    # Analyze tweets command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze tweets')
    analyze_parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    analyze_parser.add_argument('--type', type=str, choices=['recent', 'popular', 'search'], default='recent', help='Analysis type')
    analyze_parser.add_argument('--days', type=int, default=7, help='Number of days for recent analysis')
    analyze_parser.add_argument('--min-likes', type=int, default=0, help='Minimum likes for popular analysis')
    analyze_parser.add_argument('--min-retweets', type=int, default=0, help='Minimum retweets for popular analysis')
    analyze_parser.add_argument('--author', type=str, help='Filter by author')
    analyze_parser.add_argument('--keyword', type=str, help='Search keyword')
    analyze_parser.add_argument('--format', type=str, choices=['text', 'json'], default='text', help='Output format')
    analyze_parser.add_argument('--output', type=str, help='Output file path')
    analyze_parser.add_argument('--limit', type=int, default=50, help='Limit the number of tweets to display')
    
    # Export tweets command
    export_parser = subparsers.add_parser('export', help='Export tweets')
    export_parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    export_parser.add_argument('--format', type=str, choices=['csv', 'json'], default='csv', help='Output format')
    export_parser.add_argument('--output', type=str, help='Output file path')
    export_parser.add_argument('--source-url', type=str, help='Filter tweets by source URL')
    export_parser.add_argument('--limit', type=int, help='Limit the number of tweets to export')
    
    # Analyze hashtags command
    hashtag_parser = subparsers.add_parser('analyze-hashtags', help='Analyze hashtags in tweets')
    hashtag_parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    hashtag_parser.add_argument('--limit', type=int, default=10, help='Limit the number of hashtags to return')
    hashtag_parser.add_argument('--output', type=str, help='Output file for the analysis')
    
    # List URLs command
    list_urls_parser = subparsers.add_parser('list-urls', help='List URLs in the database')
    list_urls_parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    list_urls_parser.add_argument('--format', type=str, choices=['text', 'json'], default='text', help='Output format')
    list_urls_parser.add_argument('--output', type=str, help='Output file path')
    list_urls_parser.add_argument('--limit', type=int, help='Limit the number of URLs to display')
    list_urls_parser.add_argument('--type', type=str, help='Filter URLs by type')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute the command
    if args.command == 'remove-duplicates':
        # Import the module directly
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data_analysis'))
        from remove_duplicate_tweets import remove_duplicate_tweets
        remove_duplicate_tweets(db_path=args.db_path, dry_run=args.dry_run)
    
    elif args.command == 'count-tweets':
        # Import the module directly
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data_analysis'))
        from count_tweets_per_url import count_tweets_per_url
        count_tweets_per_url(
            db_path=args.db_path,
            output_format=args.format,
            output_file=args.output,
            limit=args.limit
        )
    
    elif args.command == 'analyze':
        # Import the module directly
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data_analysis'))
        from analyze_tweets import analyze_tweets
        analyze_tweets(
            db_path=args.db_path,
            analysis_type=args.type,
            days=args.days,
            min_likes=args.min_likes,
            min_retweets=args.min_retweets,
            author=args.author,
            keyword=args.keyword,
            output_format=args.format,
            output_file=args.output,
            limit=args.limit
        )
    
    elif args.command == 'export':
        # Import the module directly
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data_analysis'))
        from export_tweets import export_tweets
        export_tweets(
            db_path=args.db_path,
            output_format=args.format,
            output_file=args.output,
            source_url=args.source_url,
            limit=args.limit
        )
    
    elif args.command == 'analyze-hashtags':
        # Import the module directly
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data_analysis'))
        from analyze_hashtags import analyze_hashtags
        analyze_hashtags(
            db_path=args.db_path,
            limit=args.limit,
            output=args.output
        )
    
    elif args.command == 'list-urls':
        # Import the module directly
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data_analysis'))
        from list_urls import list_urls
        list_urls(
            db_path=args.db_path,
            output_format=args.format,
            output_file=args.output,
            limit=args.limit,
            filter_type=args.type
        )
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
