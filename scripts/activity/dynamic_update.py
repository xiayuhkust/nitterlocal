#!/usr/bin/env python3
"""
Dynamic update script for Twitter data extraction.
This script is a wrapper around the new dynamic_update_pipeline.py script.
It maintains backward compatibility with the original dynamic_update.py interface.
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
        logging.FileHandler("data/dynamic_update.log"),
        logging.StreamHandler()
    ]
)

def run_dynamic_update_pipeline(batch_size=10, sleep_between_urls=2, limit=None, 
                              performance_monitoring=False, parallel=False, num_threads=2,
                              update_profile=False):
    """Run the dynamic update pipeline"""
    logging.info("Starting dynamic update (wrapper)")
    logging.info(f"Time: {datetime.now().isoformat()}")
    logging.info(f"Batch size: {batch_size}, Sleep between URLs: {sleep_between_urls} seconds")
    logging.info(f"Parallel processing: {parallel}, Number of threads: {num_threads}")
    logging.info(f"Update profile: {update_profile}")
    
    try:
        # Build the command to run the dynamic update pipeline
        cmd = [
            "python3", "scripts/activity/dynamic_update_pipeline.py",
            "--batch-size", str(batch_size),
            "--sleep", str(sleep_between_urls)
        ]
        
        if limit:
            cmd.extend(["--limit", str(limit)])
        
        if parallel:
            cmd.append("--parallel")
            cmd.extend(["--threads", str(num_threads)])
        
        if performance_monitoring:
            cmd.append("--performance")
        
        if update_profile:
            cmd.append("--update-profile")
        
        # Log the command
        logging.info(f"Running command: {' '.join(cmd)}")
        
        # Run the command
        process = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Log the output
        logging.info("Dynamic update pipeline output:")
        logging.info(process.stdout)
        
        if process.stderr:
            logging.warning("Dynamic update pipeline errors:")
            logging.warning(process.stderr)
        
        # Parse the output to extract the result
        result = {
            'completed_at': datetime.now().isoformat()
        }
        
        # Check if the pipeline completed successfully
        if "Pipeline completed successfully" in process.stdout:
            result['success'] = True
        else:
            result['success'] = False
            result['error'] = "Pipeline failed"
        
        return result
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running dynamic update pipeline: {str(e)}")
        return {
            'error': str(e),
            'completed_at': datetime.now().isoformat()
        }
    except Exception as e:
        logging.error(f"Error in dynamic update: {str(e)}")
        return {
            'error': str(e),
            'completed_at': datetime.now().isoformat()
        }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Dynamic update for Twitter data extraction')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for URL processing')
    parser.add_argument('--sleep', type=int, default=2, help='Sleep time between URLs (seconds)')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to process')
    parser.add_argument('--parallel', action='store_true', help='Use parallel processing')
    parser.add_argument('--threads', type=int, default=2, help='Number of threads for parallel processing')
    parser.add_argument('--performance', action='store_true', help='Enable performance monitoring')
    parser.add_argument('--update-profile', action='store_true', help='Update profile data using fill_profiledata.py')
    
    args = parser.parse_args()
    
    # Run the dynamic update pipeline
    result = run_dynamic_update_pipeline(
        batch_size=args.batch_size,
        sleep_between_urls=args.sleep,
        limit=args.limit,
        performance_monitoring=args.performance,
        parallel=args.parallel,
        num_threads=args.threads,
        update_profile=args.update_profile
    )
    
    # Print summary
    print("\nDynamic Update Summary:")
    print(f"Completed at: {result.get('completed_at')}")
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print("Dynamic update completed successfully")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
