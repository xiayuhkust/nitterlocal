#!/usr/bin/env python3
"""
Test script to compare sequential and parallel processing performance.
"""

import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the DailyUpdate class
from src.daily_update.daily_update import DailyUpdate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/performance_test.log"),
        logging.StreamHandler()
    ]
)

def run_test(parallel=False, num_threads=2, limit=10, max_tweets=10, max_replies=5):
    """Run a test with the specified parameters"""
    logging.info(f"Running test: parallel={parallel}, threads={num_threads}, limit={limit}")
    
    # Initialize the DailyUpdate class
    daily_update = DailyUpdate()
    
    # Start timing
    start_time = time.time()
    
    # Run the daily update
    result = daily_update.run(
        batch_size=limit,
        sleep_between_urls=2,
        max_tweets=max_tweets,
        max_replies=max_replies,
        limit=limit,
        performance_monitoring=True,
        parallel=parallel,
        num_threads=num_threads
    )
    
    # Calculate total execution time
    total_time = time.time() - start_time
    
    # Add execution time to the result
    result['execution_time'] = total_time
    result['parallel'] = parallel
    result['num_threads'] = num_threads
    result['limit'] = limit
    result['max_tweets'] = max_tweets
    result['max_replies'] = max_replies
    
    return result

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test parallel processing performance')
    parser.add_argument('--limit', type=int, default=10, help='Number of URLs to process')
    parser.add_argument('--max-tweets', type=int, default=10, help='Maximum number of tweets per URL')
    parser.add_argument('--max-replies', type=int, default=5, help='Maximum number of reply tweets per URL')
    parser.add_argument('--threads', type=int, default=2, help='Number of threads for parallel processing')
    parser.add_argument('--skip-sequential', action='store_true', help='Skip sequential test')
    parser.add_argument('--skip-parallel', action='store_true', help='Skip parallel test')
    parser.add_argument('--output', type=str, default='data/performance_comparison.json', help='Output file path')
    
    args = parser.parse_args()
    
    # Create results dictionary
    results = {
        'timestamp': datetime.now().isoformat(),
        'parameters': {
            'limit': args.limit,
            'max_tweets': args.max_tweets,
            'max_replies': args.max_replies,
            'threads': args.threads
        }
    }
    
    # Run sequential test
    sequential_result = None
    if not args.skip_sequential:
        logging.info("Running sequential test...")
        sequential_result = run_test(
            parallel=False,
            limit=args.limit,
            max_tweets=args.max_tweets,
            max_replies=args.max_replies
        )
        results['sequential'] = sequential_result
        logging.info(f"Sequential test completed in {sequential_result['execution_time']:.2f} seconds")
    
    # Run parallel test
    parallel_result = None
    if not args.skip_parallel:
        logging.info(f"Running parallel test with {args.threads} threads...")
        parallel_result = run_test(
            parallel=True,
            num_threads=args.threads,
            limit=args.limit,
            max_tweets=args.max_tweets,
            max_replies=args.max_replies
        )
        results['parallel'] = parallel_result
        logging.info(f"Parallel test completed in {parallel_result['execution_time']:.2f} seconds")
    
    # Calculate comparison metrics
    if sequential_result and parallel_result:
        sequential_time = sequential_result['execution_time']
        parallel_time = parallel_result['execution_time']
        speedup = sequential_time / parallel_time if parallel_time > 0 else 0
        improvement_percent = (speedup - 1) * 100
        
        results['comparison'] = {
            'sequential_time': sequential_time,
            'parallel_time': parallel_time,
            'speedup': speedup,
            'improvement_percent': improvement_percent
        }
        
        # Print comparison
        print("\n===== Performance Comparison =====")
        print(f"Sequential execution time: {sequential_time:.2f} seconds")
        print(f"Parallel execution time ({args.threads} threads): {parallel_time:.2f} seconds")
        print(f"Speedup: {speedup:.2f}x")
        print(f"Performance improvement: {improvement_percent:.2f}%")
        print("===============================")
    
    # Save results to file
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {args.output}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
