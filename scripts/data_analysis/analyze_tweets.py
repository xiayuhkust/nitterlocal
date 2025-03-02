#!/usr/bin/env python3
"""
Script to analyze tweets in the database.
This script provides advanced analysis and viewing capabilities for tweets in the database.
"""

import os
import sys
import logging
import sqlite3
import json
import argparse
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import the database module
from src.database.local_database import LocalDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def analyze_tweets(db_path='data/local_database.db', analysis_type='recent', days=7, 
                 min_likes=0, min_retweets=0, author=None, keyword=None, 
                 output_format='text', output_file=None, limit=50):
    """Analyze tweets in the database"""
    logging.info(f"Analyzing tweets in database at {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build the query based on analysis type
        query = "SELECT * FROM tweets WHERE 1=1"
        params = []
        
        if analysis_type == 'recent':
            # Get tweets from the last N days
            if days:
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                query += " AND created_at >= ?"
                params.append(cutoff_date)
        
        elif analysis_type == 'popular':
            # Get popular tweets based on likes and retweets
            query += " AND likes >= ? AND retweets >= ?"
            params.extend([min_likes, min_retweets])
            query += " ORDER BY likes DESC, retweets DESC"
        
        elif analysis_type == 'search':
            # Search tweets by keyword
            if keyword:
                query += " AND content LIKE ?"
                params.append(f"%{keyword}%")
        
        # Filter by author if specified
        if author:
            query += " AND author = ?"
            params.append(author)
        
        # Add limit
        query += " LIMIT ?"
        params.append(limit)
        
        # Execute the query
        cursor.execute(query, params)
        
        # Get the results
        tweets = [dict(row) for row in cursor.fetchall()]
        
        # Get total tweet count
        cursor.execute("SELECT COUNT(*) FROM tweets")
        total_tweets = cursor.fetchone()[0]
        
        # Generate analysis results
        results = {
            'analysis_type': analysis_type,
            'total_tweets': total_tweets,
            'filtered_tweets': len(tweets),
            'tweets': tweets,
            'generated_at': datetime.now().isoformat()
        }
        
        conn.close()
        
        # Output the results
        if output_format == 'json':
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2)
                logging.info(f"Analysis results saved to {output_file}")
            else:
                print(json.dumps(results, indent=2))
        else:
            print(f"Tweet Analysis Results:")
            print(f"Analysis Type: {analysis_type}")
            print(f"Total Tweets: {total_tweets}")
            print(f"Filtered Tweets: {len(tweets)}")
            print(f"Generated at: {results['generated_at']}")
            print(f"\nTweets:")
            
            for i, tweet in enumerate(tweets):
                print(f"{i+1}. Tweet ID: {tweet['tweet_id']}")
                print(f"   Author: {tweet['author']}")
                print(f"   Created at: {tweet['created_at']}")
                print(f"   Content: {tweet['content'][:100]}...")
                print(f"   Likes: {tweet['likes']}, Retweets: {tweet['retweets']}, Replies: {tweet['replies']}")
                print(f"   Source URL: {tweet['source_url']}")
                print()
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(f"Tweet Analysis Results:\n")
                    f.write(f"Analysis Type: {analysis_type}\n")
                    f.write(f"Total Tweets: {total_tweets}\n")
                    f.write(f"Filtered Tweets: {len(tweets)}\n")
                    f.write(f"Generated at: {results['generated_at']}\n")
                    f.write(f"\nTweets:\n")
                    
                    for i, tweet in enumerate(tweets):
                        f.write(f"{i+1}. Tweet ID: {tweet['tweet_id']}\n")
                        f.write(f"   Author: {tweet['author']}\n")
                        f.write(f"   Created at: {tweet['created_at']}\n")
                        f.write(f"   Content: {tweet['content'][:100]}...\n")
                        f.write(f"   Likes: {tweet['likes']}, Retweets: {tweet['retweets']}, Replies: {tweet['replies']}\n")
                        f.write(f"   Source URL: {tweet['source_url']}\n")
                        f.write("\n")
                
                logging.info(f"Analysis results saved to {output_file}")
        
        return results
        
    except Exception as e:
        logging.error(f"Error analyzing tweets: {str(e)}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Analyze tweets in the database')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    parser.add_argument('--type', type=str, choices=['recent', 'popular', 'search'], default='recent', help='Analysis type')
    parser.add_argument('--days', type=int, default=7, help='Number of days for recent analysis')
    parser.add_argument('--min-likes', type=int, default=0, help='Minimum likes for popular analysis')
    parser.add_argument('--min-retweets', type=int, default=0, help='Minimum retweets for popular analysis')
    parser.add_argument('--author', type=str, help='Filter by author')
    parser.add_argument('--keyword', type=str, help='Search keyword')
    parser.add_argument('--format', type=str, choices=['text', 'json'], default='text', help='Output format')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--limit', type=int, default=50, help='Limit the number of tweets to display')
    
    args = parser.parse_args()
    
    # Analyze tweets
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

if __name__ == "__main__":
    main()
