#!/usr/bin/env python3
"""
Activity dashboard script for Twitter data extraction.
This script generates reports on Twitter account activity levels.
"""

import os
import sys
import logging
import argparse
from datetime import datetime
import json

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import activity manager
from src.database.activity_manager import ActivityManager
from src.database.local_database import LocalDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def generate_activity_report(activity_manager, db):
    """Generate a report on account activity levels"""
    print("\n===== Activity Distribution Report =====")
    print(f"Report generated at: {datetime.now().isoformat()}")
    
    # Get activity distribution
    distribution = activity_manager.get_activity_distribution()
    
    # Calculate total and percentages
    total = sum(distribution.values())
    percentages = {}
    for level, count in distribution.items():
        percentages[level] = (count / total) * 100 if total > 0 else 0
    
    # Print distribution
    print(f"\nTotal accounts analyzed: {total}")
    print("\nActivity Level Distribution:")
    for level in ['very_high', 'high', 'medium', 'low', 'inactive']:
        count = distribution.get(level, 0)
        percentage = percentages.get(level, 0)
        print(f"  {level}: {count} accounts ({percentage:.2f}%)")
    
    # Get most active accounts
    print("\nMost Active Accounts:")
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT a.url, a.activity_level, a.post_frequency, a.avg_interactions, u.description
    FROM activity_levels a
    JOIN url_tracking u ON a.url = u.url
    WHERE a.activity_level IN ('very_high', 'high')
    ORDER BY a.post_frequency DESC, a.avg_interactions DESC
    LIMIT 10
    """)
    
    for i, (url, level, frequency, interactions, description) in enumerate(cursor.fetchall()):
        print(f"  {i+1}. {url}")
        print(f"     Level: {level}, Posts/day: {frequency:.2f}, Avg interactions: {interactions:.2f}")
        print(f"     Description: {description}")
    
    conn.close()
    
    # Print tweet quantity recommendations
    print("\nRecommended Tweet Quantities:")
    print("  Very High Activity: 10 tweets, 5 replies")
    print("  High Activity: 8 tweets, 4 replies")
    print("  Medium Activity: 5 tweets, 3 replies")
    print("  Low Activity: 3 tweets, 2 replies")
    print("  Inactive: 1 tweet, 1 reply")
    
    print("=======================================")

def generate_performance_report(db):
    """Generate a performance report"""
    print("\n===== Performance Report =====")
    
    # Get database statistics
    stats = db.generate_stats()
    
    if stats:
        print(f"Total URLs in database: {stats.get('total_urls', 0)}")
        print(f"Total tweets in database: {stats.get('total_tweets', 0)}")
        print(f"Average tweets per URL: {stats.get('avg_tweets_per_url', 0):.2f}")
    
    # Get recent update performance
    try:
        with open('data/dynamic_update.log', 'r') as f:
            lines = f.readlines()
            
            # Extract performance metrics from log
            performance_lines = [line for line in lines if "Performance metrics" in line]
            
            if performance_lines:
                latest_performance = performance_lines[-1]
                # Extract JSON-like part
                metrics_str = latest_performance.split("Performance metrics: ")[1]
                
                try:
                    # Try to parse as JSON
                    metrics = json.loads(metrics_str)
                    
                    print("\nLatest Update Performance:")
                    print(f"  Total time: {metrics.get('total_time', 'N/A')}")
                    print(f"  URL fetch time: {metrics.get('url_fetch_time', 'N/A')}")
                    print(f"  Tweet scraping time: {metrics.get('tweet_scraping_time', 'N/A')}")
                    print(f"  Database storage time: {metrics.get('db_storage_time', 'N/A')}")
                except:
                    # If JSON parsing fails, just print the raw string
                    print(f"\nLatest Update Performance: {metrics_str}")
    except Exception as e:
        logging.error(f"Error reading performance log: {str(e)}")
    
    print("=======================================")

def generate_resource_efficiency_report(activity_manager, db):
    """Generate a resource efficiency report"""
    print("\n===== Resource Efficiency Report =====")
    
    # Get activity distribution
    distribution = activity_manager.get_activity_distribution()
    
    # Calculate resource usage
    total_accounts = sum(distribution.values())
    
    # Calculate tweets fetched with fixed vs. dynamic strategy
    fixed_tweets = total_accounts * 10  # 10 tweets per account
    fixed_replies = total_accounts * 5  # 5 replies per account
    
    dynamic_tweets = (
        distribution.get('very_high', 0) * 10 +
        distribution.get('high', 0) * 8 +
        distribution.get('medium', 0) * 5 +
        distribution.get('low', 0) * 3 +
        distribution.get('inactive', 0) * 1
    )
    
    dynamic_replies = (
        distribution.get('very_high', 0) * 5 +
        distribution.get('high', 0) * 4 +
        distribution.get('medium', 0) * 3 +
        distribution.get('low', 0) * 2 +
        distribution.get('inactive', 0) * 1
    )
    
    # Calculate savings
    tweet_savings = fixed_tweets - dynamic_tweets
    reply_savings = fixed_replies - dynamic_replies
    total_savings = tweet_savings + reply_savings
    
    savings_percentage = (total_savings / (fixed_tweets + fixed_replies)) * 100 if (fixed_tweets + fixed_replies) > 0 else 0
    
    print(f"Total accounts: {total_accounts}")
    print("\nResource Usage Comparison:")
    print(f"  Fixed strategy: {fixed_tweets} tweets + {fixed_replies} replies = {fixed_tweets + fixed_replies} total")
    print(f"  Dynamic strategy: {dynamic_tweets} tweets + {dynamic_replies} replies = {dynamic_tweets + dynamic_replies} total")
    print(f"\nResource savings: {total_savings} requests ({savings_percentage:.2f}%)")
    
    print("=======================================")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Activity dashboard for Twitter data extraction')
    parser.add_argument('--full', action='store_true', help='Generate full report with all sections')
    parser.add_argument('--activity', action='store_true', help='Generate activity distribution report')
    parser.add_argument('--performance', action='store_true', help='Generate performance report')
    parser.add_argument('--efficiency', action='store_true', help='Generate resource efficiency report')
    
    args = parser.parse_args()
    
    # If no specific reports are requested, show all
    if not (args.activity or args.performance or args.efficiency):
        args.full = True
    
    # Initialize components
    db = LocalDatabase()
    activity_manager = ActivityManager()
    
    # Generate requested reports
    if args.full or args.activity:
        generate_activity_report(activity_manager, db)
    
    if args.full or args.performance:
        generate_performance_report(db)
    
    if args.full or args.efficiency:
        generate_resource_efficiency_report(activity_manager, db)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
