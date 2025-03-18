#!/usr/bin/env python3
"""
Dynamic update pipeline script.
This script uses the separate tweet scraper and storer to implement dynamic updates.
"""

import os
import sys
import logging
import argparse
import subprocess
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/dynamic_update_pipeline.log"),
        logging.StreamHandler()
    ]
)

def run_dynamic_update(batch_size=10, sleep=2, limit=None, parallel=False, threads=2, 
                      performance=False, update_profile=False):
    """Run the dynamic update pipeline"""
    logging.info("Starting dynamic update pipeline")
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
        
        # Step 3: Update profile data if requested
        if update_profile:
            logging.info("Step 3: Updating profile data")
            
            profile_cmd = [
                "python3", "scripts/newstruct/fill_profiledata.py",
                "--all"
            ]
            
            if limit:
                profile_cmd.extend(["--limit", str(limit)])
            
            logging.info(f"Running command: {' '.join(profile_cmd)}")
            profile_process = subprocess.run(profile_cmd, check=True, capture_output=True, text=True)
            
            logging.info("Profile updater output:")
            logging.info(profile_process.stdout)
            
            if profile_process.stderr:
                logging.warning("Profile updater errors:")
                logging.warning(profile_process.stderr)
        
        # Log completion
        logging.info("Dynamic update pipeline completed successfully")
        
        return {
            'completed_at': datetime.now().isoformat(),
            'scraper_output': scraper_process.stdout,
            'storer_output': storer_process.stdout,
            'profile_output': profile_process.stdout if update_profile else None
        }
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Error in dynamic update pipeline: {str(e)}")
        return {
            'error': str(e),
            'completed_at': datetime.now().isoformat()
        }
    except Exception as e:
        logging.error(f"Error in dynamic update pipeline: {str(e)}")
        return {
            'error': str(e),
            'completed_at': datetime.now().isoformat()
        }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Dynamic update pipeline')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for URL processing')
    parser.add_argument('--sleep', type=int, default=2, help='Sleep time between URLs (seconds)')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to process')
    parser.add_argument('--parallel', action='store_true', help='Use parallel processing')
    parser.add_argument('--threads', type=int, default=2, help='Number of threads for parallel processing')
    parser.add_argument('--performance', action='store_true', help='Enable performance monitoring')
    parser.add_argument('--update-profile', action='store_true', help='Update profile data')
    
    args = parser.parse_args()
    
    # Run the pipeline
    result = run_dynamic_update(
        batch_size=args.batch_size,
        sleep=args.sleep,
        limit=args.limit,
        parallel=args.parallel,
        threads=args.threads,
        performance=args.performance,
        update_profile=args.update_profile
    )
    
    # Print summary
    print("\nDynamic Update Pipeline Summary:")
    print(f"Completed at: {result.get('completed_at')}")
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print("Pipeline completed successfully")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
