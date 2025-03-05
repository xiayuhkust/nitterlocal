#!/usr/bin/env python3
"""
Script to analyze replies in the database.
This script provides advanced analysis and viewing capabilities for replies in the database.
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

def analyze_replies(db_path='data/local_database.db', analysis_type='user-replies', 
                  days=7, min_likes=0, author=None, keyword=None, conversation_id=None,
                  output_format='text', output_file=None, limit=50):
    """Analyze replies in the database"""
    logging.info(f"Analyzing replies in database at {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build the query based on analysis type
        query = "SELECT * FROM tweets WHERE is_reply = 1"
        params = []
        
        # Add time filter
        if days:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            query += " AND created_at >= ?"
            params.append(cutoff_date)
        
        # Add likes filter
        if min_likes > 0:
            query += " AND likes >= ?"
            params.append(min_likes)
        
        # Add keyword filter
        if keyword:
            query += " AND content LIKE ?"
            params.append(f"%{keyword}%")
        
        # Add conversation filter
        if conversation_id:
            query += " AND conversation_id = ?"
            params.append(conversation_id)
        
        # Add analysis type specific filters
        if analysis_type == 'user-replies':
            # Get replies from the user to others
            if author:
                query += " AND author = ?"
                params.append(author)
            query += " ORDER BY created_at DESC"
        
        elif analysis_type == 'replies-to-user':
            # Get replies to the user's tweets
            if author:
                # Find tweets by the author first
                author_tweets_query = """
                SELECT tweet_id FROM tweets 
                WHERE author = ? AND (is_reply = 0 OR is_reply IS NULL)
                """
                cursor.execute(author_tweets_query, (author,))
                author_tweet_ids = [row[0] for row in cursor.fetchall()]
                
                if author_tweet_ids:
                    # Find replies to these tweets
                    placeholders = ', '.join(['?'] * len(author_tweet_ids))
                    query += f" AND in_reply_to_status_id IN ({placeholders})"
                    params.extend(author_tweet_ids)
                else:
                    # No tweets found for the author
                    logging.warning(f"No tweets found for author {author}")
                    return {
                        'analysis_type': analysis_type,
                        'total_replies': 0,
                        'filtered_replies': 0,
                        'replies': [],
                        'generated_at': datetime.now().isoformat()
                    }
            query += " ORDER BY created_at DESC"
        
        elif analysis_type == 'conversation':
            # Get all replies in a conversation
            if not conversation_id:
                logging.error("Conversation ID is required for conversation analysis")
                return None
            query += " ORDER BY created_at ASC"
        
        # Add limit
        query += " LIMIT ?"
        params.append(limit)
        
        # Execute the query
        cursor.execute(query, params)
        
        # Get the results
        replies = [dict(row) for row in cursor.fetchall()]
        
        # Get total reply count
        cursor.execute("SELECT COUNT(*) FROM tweets WHERE is_reply = 1")
        total_replies = cursor.fetchone()[0]
        
        # Generate analysis results
        results = {
            'analysis_type': analysis_type,
            'total_replies': total_replies,
            'filtered_replies': len(replies),
            'replies': replies,
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
            print(f"Reply Analysis Results:")
            print(f"Analysis Type: {analysis_type}")
            print(f"Total Replies: {total_replies}")
            print(f"Filtered Replies: {len(replies)}")
            print(f"Generated at: {results['generated_at']}")
            print(f"\nReplies:")
            
            for i, reply in enumerate(replies):
                print(f"{i+1}. Reply ID: {reply['tweet_id']}")
                print(f"   Author: {reply['author']}")
                print(f"   User ID: {reply.get('user_id') or 'N/A'}")
                print(f"   Created at: {reply['created_at']}")
                print(f"   Content: {reply['content'][:100]}...")
                print(f"   Likes: {reply['likes']}, Retweets: {reply['retweets']}, Replies: {reply['replies']}")
                print(f"   In Reply To: {reply.get('in_reply_to_status_id') or 'N/A'}")
                print(f"   Conversation ID: {reply.get('conversation_id') or 'N/A'}")
                print(f"   Source URL: {reply['source_url']}")
                print()
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(f"Reply Analysis Results:\n")
                    f.write(f"Analysis Type: {analysis_type}\n")
                    f.write(f"Total Replies: {total_replies}\n")
                    f.write(f"Filtered Replies: {len(replies)}\n")
                    f.write(f"Generated at: {results['generated_at']}\n")
                    f.write(f"\nReplies:\n")
                    
                    for i, reply in enumerate(replies):
                        f.write(f"{i+1}. Reply ID: {reply['tweet_id']}\n")
                        f.write(f"   Author: {reply['author']}\n")
                        f.write(f"   User ID: {reply.get('user_id') or 'N/A'}\n")
                        f.write(f"   Created at: {reply['created_at']}\n")
                        f.write(f"   Content: {reply['content'][:100]}...\n")
                        f.write(f"   Likes: {reply['likes']}, Retweets: {reply['retweets']}, Replies: {reply['replies']}\n")
                        f.write(f"   In Reply To: {reply.get('in_reply_to_status_id') or 'N/A'}\n")
                        f.write(f"   Conversation ID: {reply.get('conversation_id') or 'N/A'}\n")
                        f.write(f"   Source URL: {reply['source_url']}\n")
                        f.write("\n")
                
                logging.info(f"Analysis results saved to {output_file}")
        
        return results
        
    except Exception as e:
        logging.error(f"Error analyzing replies: {str(e)}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Analyze replies in the database')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    parser.add_argument('--type', type=str, choices=['user-replies', 'replies-to-user', 'conversation'], 
                        default='user-replies', help='Analysis type')
    parser.add_argument('--days', type=int, default=7, help='Number of days for recent analysis')
    parser.add_argument('--min-likes', type=int, default=0, help='Minimum likes')
    parser.add_argument('--author', type=str, help='Filter by author')
    parser.add_argument('--keyword', type=str, help='Search keyword')
    parser.add_argument('--conversation', type=str, help='Filter by conversation ID')
    parser.add_argument('--format', type=str, choices=['text', 'json'], default='text', help='Output format')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--limit', type=int, default=50, help='Limit the number of replies to display')
    
    args = parser.parse_args()
    
    # Analyze replies
    analyze_replies(
        db_path=args.db_path,
        analysis_type=args.type,
        days=args.days,
        min_likes=args.min_likes,
        author=args.author,
        keyword=args.keyword,
        conversation_id=args.conversation,
        output_format=args.format,
        output_file=args.output,
        limit=args.limit
    )

if __name__ == "__main__":
    main()
