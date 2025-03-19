#!/usr/bin/env python3
"""
Tweet extraction pipeline script.
This script runs both the separate tweet scraper and the tweet storer.
"""

import os
import sys
import logging
import argparse
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/tweet_extraction_pipeline.log"),
        logging.StreamHandler()
    ]
)

def run_pipeline(batch_size=10, sleep=2, limit=None, parallel=False, threads=2, performance=False, force_max_tweets=None):
    """Run the tweet extraction pipeline"""
    logging.info("Starting tweet extraction pipeline")
    logging.info(f"Time: {datetime.now().isoformat()}")
    
    try:
        # Step 1: Run the separate tweet scraper
        logging.info("Step 1: Running separate tweet scraper")
        
        scraper_cmd = [
            "python3", "scripts/activity/separate_tweet_scraper.py",
            "--batch-size", str(batch_size),
            "--sleep", str(sleep)
        ]
        
        if limit:
            scraper_cmd.extend(["--limit", str(limit)])
        
        if parallel:
            scraper_cmd.append("--parallel")
            scraper_cmd.extend(["--threads", str(threads)])
        
        if performance:
            scraper_cmd.append("--performance")
        
        if force_max_tweets is not None:
            scraper_cmd.extend(["--force-max-tweets", str(force_max_tweets)])
        
        logging.info(f"Running command: {' '.join(scraper_cmd)}")
        scraper_process = subprocess.run(scraper_cmd, check=True, capture_output=True, text=True)
        
        logging.info("Separate tweet scraper output:")
        logging.info(scraper_process.stdout)
        
        if scraper_process.stderr:
            logging.warning("Separate tweet scraper errors:")
            logging.warning(scraper_process.stderr)
        
        # Step 2: Run the tweet storer
        logging.info("Step 2: Running tweet storer")
        
        storer_cmd = [
            "python3", "scripts/activity/store_tweets.py"
        ]
        
        logging.info(f"Running command: {' '.join(storer_cmd)}")
        storer_process = subprocess.run(storer_cmd, check=True, capture_output=True, text=True)
        
        logging.info("Tweet storer output:")
        logging.info(storer_process.stdout)
        
        if storer_process.stderr:
            logging.warning("Tweet storer errors:")
            logging.warning(storer_process.stderr)
        
        # Log completion
        logging.info("Tweet extraction pipeline completed successfully")
        
        return {
            'completed_at': datetime.now().isoformat(),
            'scraper_output': scraper_process.stdout,
            'storer_output': storer_process.stdout
        }
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Error in tweet extraction pipeline: {str(e)}")
        return {
            'error': str(e),
            'completed_at': datetime.now().isoformat()
        }
    except Exception as e:
        logging.error(f"Error in tweet extraction pipeline: {str(e)}")
        return {
            'error': str(e),
            'completed_at': datetime.now().isoformat()
        }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Tweet extraction pipeline')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for URL processing')
    parser.add_argument('--sleep', type=int, default=2, help='Sleep time between URLs (seconds)')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to process')
    parser.add_argument('--parallel', action='store_true', help='Use parallel processing')
    parser.add_argument('--threads', type=int, default=2, help='Number of threads for parallel processing')
    parser.add_argument('--performance', action='store_true', help='Enable performance monitoring')
    parser.add_argument('--force-max-tweets', type=int, help='Force a specific number of tweets to retrieve per URL')
    
    args = parser.parse_args()
    
    # Run the pipeline
    result = run_pipeline(
        batch_size=args.batch_size,
        sleep=args.sleep,
        limit=args.limit,
        parallel=args.parallel,
        threads=args.threads,
        performance=args.performance,
        force_max_tweets=args.force_max_tweets
    )
    
    # Print summary
    print("\nTweet Extraction Pipeline Summary:")
    print(f"Completed at: {result.get('completed_at')}")
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print("Pipeline completed successfully")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
