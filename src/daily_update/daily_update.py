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
    
    def run(self, batch_size=10, sleep_between_urls=2, max_tweets=10, max_replies=5, limit=None, 
            performance_monitoring=False, parallel=False, num_threads=2):
        """Run the daily update"""
        logging.info("Starting daily update")
        logging.info(f"Time: {datetime.now().isoformat()}")
        logging.info(f"Batch size: {batch_size}, Sleep between URLs: {sleep_between_urls} seconds")
        logging.info(f"Max tweets per URL: {max_tweets}, Max replies per URL: {max_replies}")
        logging.info(f"Parallel processing: {parallel}, Number of threads: {num_threads}")
        
        # Initialize performance metrics if monitoring is enabled
        performance_metrics = {}
        if performance_monitoring:
            performance_metrics = {
                'total_start_time': time.time(),
                'url_processing_time': 0,
                'tweet_scraping_time': 0,
                'db_storage_time': 0,
                'url_status_update_time': 0,
                'sleep_time': 0,
                'stats_generation_time': 0,
                'url_times': []
            }
        
        try:
            # Get active URLs
            if performance_monitoring:
                url_fetch_start = time.time()
                
            urls = self.url_manager.get_urls(status='active')
            
            if limit:
                urls = urls[:limit]
            
            total_urls = len(urls)
            logging.info(f"Found {total_urls} active URLs to process")
            
            if performance_monitoring:
                url_fetch_time = time.time() - url_fetch_start
                performance_metrics['url_fetch_time'] = f"{url_fetch_time:.2f} seconds"
            
            # Process URLs in batches
            processed_count = 0
            success_count = 0
            error_count = 0
            total_tweets = 0
            
            for i in range(0, len(urls), batch_size):
                batch = urls[i:i+batch_size]
                logging.info(f"Processing batch {i//batch_size + 1}/{(total_urls + batch_size - 1)//batch_size}")
                
                batch_urls = [url_data['url'] for url_data in batch]
                
                # Process the batch of URLs
                if parallel:
                    # Use parallel processing
                    logging.info(f"Using parallel processing with {num_threads} threads")
                    
                    if performance_monitoring:
                        scrape_start_time = time.time()
                    
                    # Scrape URLs in parallel
                    tweets_by_url = {}
                    try:
                        # Extract just the URLs from the batch
                        batch_urls = [url_data['url'] for url_data in batch]
                        
                        # Scrape URLs in parallel
                        all_tweets = self.scraper.scrape_urls_parallel(
                            batch_urls, 
                            max_tweets=max_tweets, 
                            max_replies=max_replies,
                            num_threads=num_threads,
                            sleep_between_urls=sleep_between_urls
                        )
                        
                        # Group tweets by URL
                        for tweet in all_tweets:
                            source_url = tweet.get('source_url')
                            if source_url not in tweets_by_url:
                                tweets_by_url[source_url] = []
                            tweets_by_url[source_url].append(tweet)
                        
                        if performance_monitoring:
                            scrape_time = time.time() - scrape_start_time
                            performance_metrics['tweet_scraping_time'] += scrape_time
                            logging.info(f"Parallel scraping completed in {scrape_time:.2f} seconds")
                    
                    except Exception as e:
                        logging.error(f"Error in parallel scraping: {str(e)}")
                        # Continue with processing what we have
                    
                    # Process the results
                    for url_data in batch:
                        url = url_data['url']
                        try:
                            url_start_time = time.time()
                            url_metrics = {'url': url} if performance_monitoring else None
                            
                            # Get tweets for this URL
                            tweets = tweets_by_url.get(url, [])
                            
                            if tweets:
                                # Store the tweets in the database
                                if performance_monitoring:
                                    db_start_time = time.time()
                                
                                processed_count_url = self.database.store_tweets(tweets, url)
                                
                                if performance_monitoring:
                                    db_time = time.time() - db_start_time
                                    performance_metrics['db_storage_time'] += db_time
                                    if url_metrics:
                                        url_metrics['db_time'] = f"{db_time:.2f} seconds"
                                
                                if processed_count_url > 0:
                                    logging.info(f"Processed {processed_count_url} tweets for URL: {url}")
                                    success_count += 1
                                    total_tweets += processed_count_url
                                else:
                                    logging.warning(f"No tweets processed for URL: {url}")
                                    error_count += 1
                            else:
                                logging.warning(f"No tweets found for URL: {url}")
                                error_count += 1
                            
                            # Update the URL status
                            if performance_monitoring:
                                update_start_time = time.time()
                            
                            self.url_manager.update_last_scraped(url)
                            
                            if performance_monitoring:
                                update_time = time.time() - update_start_time
                                performance_metrics['url_status_update_time'] += update_time
                                if url_metrics:
                                    url_metrics['update_time'] = f"{update_time:.2f} seconds"
                            
                            processed_count += 1
                            logging.info(f"Processed {processed_count}/{total_urls} URLs")
                            
                            if performance_monitoring:
                                url_total_time = time.time() - url_start_time
                                if url_metrics:
                                    url_metrics['total_time'] = f"{url_total_time:.2f} seconds"
                                    performance_metrics['url_times'].append(url_metrics)
                            
                        except Exception as e:
                            logging.error(f"Error processing URL {url}: {str(e)}")
                            self.url_manager.update_url_status(url, 'error', str(e))
                            error_count += 1
                            processed_count += 1
                else:
                    # Use sequential processing (existing code)
                    for url_data in batch:
                        url = url_data['url']
                        
                        try:
                            logging.info(f"Processing URL: {url}")
                            
                            url_start_time = time.time()
                            url_metrics = {'url': url} if performance_monitoring else None
                            
                            # Scrape the URL for both regular tweets and replies
                            if performance_monitoring:
                                scrape_start_time = time.time()
                                
                            tweets = self.scraper.scrape_url(url, max_tweets=max_tweets, max_replies=max_replies)
                            
                            if performance_monitoring:
                                scrape_time = time.time() - scrape_start_time
                                performance_metrics['tweet_scraping_time'] += scrape_time
                                if url_metrics:
                                    url_metrics['scrape_time'] = f"{scrape_time:.2f} seconds"
                            
                            if tweets:
                                # Store the tweets in the database
                                if performance_monitoring:
                                    db_start_time = time.time()
                                    
                                processed_count_url = self.database.store_tweets(tweets, url)
                                
                                if performance_monitoring:
                                    db_time = time.time() - db_start_time
                                    performance_metrics['db_storage_time'] += db_time
                                    if url_metrics:
                                        url_metrics['db_time'] = f"{db_time:.2f} seconds"
                                
                                if processed_count_url > 0:
                                    logging.info(f"Processed {processed_count_url} tweets for URL: {url}")
                                    success_count += 1
                                    total_tweets += processed_count_url
                                else:
                                    logging.warning(f"No tweets processed for URL: {url}")
                                    error_count += 1
                            else:
                                logging.warning(f"No tweets found for URL: {url}")
                                error_count += 1
                            
                            # Update the URL status
                            if performance_monitoring:
                                update_start_time = time.time()
                                
                            self.url_manager.update_last_scraped(url)
                            
                            if performance_monitoring:
                                update_time = time.time() - update_start_time
                                performance_metrics['url_status_update_time'] += update_time
                                if url_metrics:
                                    url_metrics['update_time'] = f"{update_time:.2f} seconds"
                            
                            processed_count += 1
                            logging.info(f"Processed {processed_count}/{total_urls} URLs")
                            
                            if performance_monitoring:
                                url_total_time = time.time() - url_start_time
                                if url_metrics:
                                    url_metrics['total_time'] = f"{url_total_time:.2f} seconds"
                                    performance_metrics['url_times'].append(url_metrics)
                            
                        except Exception as e:
                            logging.error(f"Error processing URL {url}: {str(e)}")
                            self.url_manager.update_url_status(url, 'error', str(e))
                            error_count += 1
                            processed_count += 1
                
                # Sleep between batches
                if i + batch_size < len(urls):
                    logging.info(f"Sleeping for {sleep_between_urls} seconds between batches")
                    
                    if performance_monitoring:
                        sleep_start_time = time.time()
                        
                    time.sleep(sleep_between_urls)
                    
                    if performance_monitoring:
                        sleep_time = time.time() - sleep_start_time
                        performance_metrics['sleep_time'] += sleep_time
            
            # Generate statistics
            logging.info("Generating statistics")
            
            if performance_monitoring:
                stats_start_time = time.time()
                
            stats = self.database.generate_stats()
            
            if performance_monitoring:
                stats_time = time.time() - stats_start_time
                performance_metrics['stats_generation_time'] = f"{stats_time:.2f} seconds"
            
            # Log completion
            logging.info("Daily update completed successfully")
            logging.info(f"Processed: {processed_count}, Success: {success_count}, Errors: {error_count}")
            logging.info(f"Total tweets stored: {total_tweets}")
            
            if stats:
                logging.info(f"Total URLs in database: {stats['total_urls']}")
                logging.info(f"Total tweets in database: {stats['total_tweets']}")
            
            # Calculate total time if performance monitoring is enabled
            if performance_monitoring:
                total_time = time.time() - performance_metrics['total_start_time']
                performance_metrics['total_time'] = f"{total_time:.2f} seconds"
                
                # Calculate average times
                if processed_count > 0:
                    performance_metrics['avg_scraping_time'] = f"{performance_metrics['tweet_scraping_time'] / processed_count:.2f} seconds"
                    performance_metrics['avg_db_time'] = f"{performance_metrics['db_storage_time'] / processed_count:.2f} seconds"
                
                # Log performance metrics
                logging.info(f"Performance metrics: {performance_metrics}")
            
            result = {
                'processed_count': processed_count,
                'success_count': success_count,
                'error_count': error_count,
                'total_tweets': total_tweets,
                'completed_at': datetime.now().isoformat()
            }
            
            # Add performance metrics to result if monitoring is enabled
            if performance_monitoring:
                result['performance_details'] = performance_metrics
            
            return result
            
        except Exception as e:
            logging.error(f"Error in daily update: {str(e)}")
            return {
                'error': str(e),
                'completed_at': datetime.now().isoformat()
            }
