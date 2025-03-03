#!/usr/bin/env python3
"""
Analyze hashtags in tweets.
This script provides functionality for analyzing hashtags in tweets.
"""

import os
import sys
import logging
import json
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import the database module
from src.database.local_database import LocalDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def analyze_hashtags(db_path='data/local_database.db', limit=10, output=None):
    """Analyze hashtags in tweets"""
    logging.info(f"Analyzing hashtags in tweets from {db_path}")
    
    # Initialize the database
    db = LocalDatabase(db_path=db_path)
    
    # Get popular hashtags
    popular_hashtags = db.get_popular_hashtags(limit=limit)
    
    # Print popular hashtags
    print(f"\nTop {len(popular_hashtags)} hashtags:")
    for i, hashtag_data in enumerate(popular_hashtags):
        print(f"{i+1}. #{hashtag_data['hashtag']} - {hashtag_data['count']} tweets")
    
    # Save to file if output is specified
    if output:
        with open(output, 'w') as f:
            json.dump({
                'popular_hashtags': popular_hashtags,
                'generated_at': datetime.now().isoformat()
            }, f, indent=2)
        
        logging.info(f"Hashtag analysis saved to {output}")
    
    return popular_hashtags

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze hashtags in tweets')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the database')
    parser.add_argument('--limit', type=int, default=10, help='Limit the number of hashtags to return')
    parser.add_argument('--output', type=str, help='Output file for the analysis')
    
    args = parser.parse_args()
    
    analyze_hashtags(db_path=args.db_path, limit=args.limit, output=args.output)
