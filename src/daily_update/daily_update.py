#!/usr/bin/env python3
"""
Daily update module.
This module provides a daily update mechanism for the local database.
"""

import os
import sys
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DailyUpdate:
    """Daily update for the local database"""
    
    def __init__(self, db_path='data/local_database.db'):
        """Initialize the daily update"""
        logging.info(f"Initializing daily update with database at {db_path}")
        
        self.db_path = db_path
        
        # Import modules
        from src.database.local_database import LocalDatabase
        from src.database.url_manager import URLManager
        from src.twitter_client.twitter_scraper import TwitterScraper
        
        # Initialize components
        self.database = LocalDatabase(db_path=db_path)
        self.url_manager = URLManager(db_path=db_path)
        self.scraper = TwitterScraper()
        
        logging.info("Daily update initialization complete")
    
    def run(self, batch_size=10, sleep_between_urls=2, max_tweets=10, max_replies=30, limit=None):
        """Run the daily update"""
        logging.info("Starting daily update")
        logging.info(f"Time: {datetime.now().isoformat()}")
        logging.info(f"Batch size: {batch_size}, Sleep between URLs: {sleep_between_urls} seconds")
        logging.info(f"Max tweets per URL: {max_tweets}, Max replies per URL: {max_replies}")
        
        try:
            # Get active URLs
            urls = self.url_manager.get_urls(status='active')
            
            if limit:
                urls = urls[:limit]
            
            total_urls = len(urls)
            logging.info(f"Found {total_urls} active URLs to process")
            
            # Process URLs in batches
            processed_count = 0
            success_count = 0
            error_count = 0
            total_tweets = 0
            
            for i in range(0, len(urls), batch_size):
                batch = urls[i:i+batch_size]
                logging.info(f"Processing batch {i//batch_size + 1}/{(total_urls + batch_size - 1)//batch_size}")
                
                batch_urls = [url_data['url'] for url_data in batch]
                
                # Scrape the batch of URLs
                for url_data in batch:
                    url = url_data['url']
                    
                    try:
                        logging.info(f"Processing URL: {url}")
                        
                        # Scrape the URL for both regular tweets and replies
                        tweets = self.scraper.scrape_url(url, max_tweets=max_tweets, max_replies=max_replies)
                        
                        if tweets:
                            # Store the tweets in the database
                            processed_count = self.database.store_tweets(tweets, url)
                            
                            if processed_count > 0:
                                logging.info(f"Processed {processed_count} tweets for URL: {url}")
                                success_count += 1
                                total_tweets += processed_count
                            else:
                                logging.warning(f"No tweets processed for URL: {url}")
                                error_count += 1
                        else:
                            logging.warning(f"No tweets found for URL: {url}")
                            error_count += 1
                        
                        # Update the URL status
                        self.url_manager.update_last_scraped(url)
                        
                        processed_count += 1
                        logging.info(f"Processed {processed_count}/{total_urls} URLs")
                        
                    except Exception as e:
                        logging.error(f"Error processing URL {url}: {str(e)}")
                        self.url_manager.update_url_status(url, 'error', str(e))
                        error_count += 1
                        processed_count += 1
                
                # Sleep between batches
                if i + batch_size < len(urls):
                    logging.info(f"Sleeping for {sleep_between_urls} seconds between batches")
                    time.sleep(sleep_between_urls)
            
            # Generate statistics
            logging.info("Generating statistics")
            stats = self.database.generate_stats()
            
            # Log completion
            logging.info("Daily update completed successfully")
            logging.info(f"Processed: {processed_count}, Success: {success_count}, Errors: {error_count}")
            logging.info(f"Total tweets stored: {total_tweets}")
            
            if stats:
                logging.info(f"Total URLs in database: {stats['total_urls']}")
                logging.info(f"Total tweets in database: {stats['total_tweets']}")
            
            return {
                'processed_count': processed_count,
                'success_count': success_count,
                'error_count': error_count,
                'total_tweets': total_tweets,
                'completed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error in daily update: {str(e)}")
            return {
                'error': str(e),
                'completed_at': datetime.now().isoformat()
            }
