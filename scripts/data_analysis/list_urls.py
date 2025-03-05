#!/usr/bin/env python3
"""
Script to list URLs in the database.
This script lists all URLs in the url_tracking table, including user_id information.
"""

import os
import sys
import logging
import sqlite3
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

def list_urls(db_path='data/local_database.db', output_format='text', output_file=None, limit=None, filter_type=None):
    """List URLs in the database"""
    logging.info(f"Listing URLs in database at {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build the query
        query = """
            SELECT url, user_id, description, type, status, tweet_count, error_count, 
                   last_checked, last_scraped, added_at
            FROM url_tracking
            WHERE 1=1
        """
        params = []
        
        # Add filter by type if specified
        if filter_type:
            query += " AND type = ?"
            params.append(filter_type)
        
        # Add order by and limit
        query += " ORDER BY added_at DESC LIMIT ?"
        params.append(limit or -1)
        
        # Execute the query
        cursor.execute(query, params)
        
        # Get the results
        urls = [dict(row) for row in cursor.fetchall()]
        
        # Get total URL count
        cursor.execute("SELECT COUNT(*) FROM url_tracking")
        total_urls = cursor.fetchone()[0]
        
        # Generate results
        results = {
            'total_urls': total_urls,
            'filtered_urls': len(urls),
            'urls': urls,
            'generated_at': datetime.now().isoformat()
        }
        
        conn.close()
        
        # Output the results
        if output_format == 'json':
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2)
                logging.info(f"URL list saved to {output_file}")
            else:
                print(json.dumps(results, indent=2))
        else:
            print(f"URL List:")
            print(f"Total URLs: {total_urls}")
            print(f"Filtered URLs: {len(urls)}")
            print(f"Generated at: {results['generated_at']}")
            print(f"\nURLs:")
            
            for i, url_data in enumerate(urls):
                print(f"{i+1}. {url_data['url']}")
                print(f"   User ID: {url_data['user_id'] or 'N/A'}")
                print(f"   Description: {url_data['description']}")
                print(f"   Type: {url_data['type']}")
                print(f"   Status: {url_data['status']}")
                print(f"   Tweet Count: {url_data['tweet_count']}")
                print(f"   Added at: {url_data['added_at']}")
                print()
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(f"URL List:\n")
                    f.write(f"Total URLs: {total_urls}\n")
                    f.write(f"Filtered URLs: {len(urls)}\n")
                    f.write(f"Generated at: {results['generated_at']}\n")
                    f.write(f"\nURLs:\n")
                    
                    for i, url_data in enumerate(urls):
                        f.write(f"{i+1}. {url_data['url']}\n")
                        f.write(f"   User ID: {url_data['user_id'] or 'N/A'}\n")
                        f.write(f"   Description: {url_data['description']}\n")
                        f.write(f"   Type: {url_data['type']}\n")
                        f.write(f"   Status: {url_data['status']}\n")
                        f.write(f"   Tweet Count: {url_data['tweet_count']}\n")
                        f.write(f"   Added at: {url_data['added_at']}\n")
                        f.write("\n")
                
                logging.info(f"URL list saved to {output_file}")
        
        return results
        
    except Exception as e:
        logging.error(f"Error listing URLs: {str(e)}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='List URLs in the database')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    parser.add_argument('--format', type=str, choices=['text', 'json'], default='text', help='Output format')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to display')
    parser.add_argument('--type', type=str, help='Filter URLs by type')
    
    args = parser.parse_args()
    
    # List URLs
    list_urls(
        db_path=args.db_path,
        output_format=args.format,
        output_file=args.output,
        limit=args.limit,
        filter_type=args.type
    )

if __name__ == "__main__":
    main()
