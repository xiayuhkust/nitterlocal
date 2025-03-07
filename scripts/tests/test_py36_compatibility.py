#!/usr/bin/env python3
"""
Comprehensive test script for Python 3.6 compatibility.
This script tests all the components that might have Python 3.6 compatibility issues.
"""

import os
import sys
import logging
import subprocess
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def check_python_version():
    """Check the Python version"""
    version = sys.version_info
    logging.info("Python version: {}.{}.{}".format(version.major, version.minor, version.micro))
    
    if version.major == 3 and version.minor < 7:
        logging.info("Running on Python 3.6 or earlier - good for testing compatibility")
        return True
    else:
        logging.warning("Running on Python 3.7 or later - not ideal for testing Python 3.6 compatibility")
        return False

def test_subprocess_compatibility():
    """Test subprocess compatibility with Python 3.6"""
    try:
        # Python 3.6 compatible subprocess call
        process = subprocess.run(
            ['python3', '--version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        logging.info("Subprocess test passed: {}".format(process.stdout.strip()))
        return True
    except Exception as e:
        logging.error("Subprocess test failed: {}".format(str(e)))
        return False

def test_twitter_scraper_py36():
    """Test the Python 3.6 compatible TwitterScraper class"""
    try:
        from src.twitter_client.twitter_scraper_py36 import TwitterScraper
        
        logging.info("Importing TwitterScraper_py36 class...")
        scraper = TwitterScraper()
        logging.info("TwitterScraper_py36 initialized successfully")
        
        # Test extracting username from URL
        url = "https://twitter.com/VitalikButerin"
        username = scraper.extract_username_from_url(url)
        logging.info("Extracted username from {}: {}".format(url, username))
        
        if username != "VitalikButerin":
            logging.error("Username extraction test failed. Expected 'VitalikButerin', got '{}'".format(username))
            return False
        
        logging.info("TwitterScraper_py36 tests passed")
        return True
    except Exception as e:
        logging.error("TwitterScraper_py36 test failed: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        return False

def test_combined_update_script():
    """Test the combined update script with Python 3.6 compatibility"""
    try:
        # Path to the combined update script
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  'database/combined_update_with_performance_py36.py')
        
        # Run the script with a small limit and skip-sqlite option to avoid actual Twitter API calls
        logging.info("Running combined update script with --skip-sqlite...")
        
        # Python 3.6 compatible subprocess call
        process = subprocess.run(
            ['python3', script_path, '--limit', '2', '--skip-sqlite'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Check if the script ran successfully
        if process.returncode == 0:
            logging.info("Combined update script ran successfully")
            return True
        else:
            logging.error("Combined update script failed with return code {}".format(process.returncode))
            logging.error("Error: {}".format(process.stderr))
            return False
    
    except Exception as e:
        logging.error("Error testing combined update script: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        return False

def test_performance_logger():
    """Test the PerformanceLogger class for Python 3.6 compatibility"""
    try:
        # Create a test performance log file
        log_file = 'data/test_performance_log.json'
        
        # Import the PerformanceLogger class from the combined update script
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database'))
        from combined_update_with_performance_py36 import PerformanceLogger
        
        # Initialize the performance logger
        logger = PerformanceLogger(log_file=log_file)
        
        # Test checkpoints
        logger.checkpoint("Test Step 1")
        import time
        time.sleep(0.1)
        logger.checkpoint("Test Step 2")
        time.sleep(0.1)
        
        # Update metrics
        logger.update_sqlite_metrics(5, 10, 0)
        logger.update_mysql_metrics(5, 10, 0)
        
        # Finalize the log
        logger.finalize()
        
        # Check if the log file was created
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_data = json.load(f)
            
            logging.info("Performance log created successfully")
            logging.info("Log data: {}".format(json.dumps(log_data, indent=2)))
            
            # Clean up
            os.remove(log_file)
            
            return True
        else:
            logging.error("Performance log file was not created")
            return False
    
    except Exception as e:
        logging.error("Error testing PerformanceLogger: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    logging.info("Running comprehensive Python 3.6 compatibility tests")
    
    # Check Python version
    check_python_version()
    
    # Run tests
    tests = [
        ("Subprocess compatibility", test_subprocess_compatibility),
        ("TwitterScraper_py36", test_twitter_scraper_py36),
        ("Performance Logger", test_performance_logger),
        ("Combined update script", test_combined_update_script)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        logging.info("\n=== Testing {} ===".format(name))
        if test_func():
            logging.info("=== {} test PASSED ===".format(name))
            passed += 1
        else:
            logging.error("=== {} test FAILED ===".format(name))
            failed += 1
    
    # Print summary
    logging.info("\n=== Test Summary ===")
    logging.info("Passed: {}".format(passed))
    logging.info("Failed: {}".format(failed))
    logging.info("Total: {}".format(len(tests)))
    
    if failed == 0:
        logging.info("All tests passed - Python 3.6 compatibility confirmed")
        return 0
    else:
        logging.error("{} tests failed - Python 3.6 compatibility issues detected".format(failed))
        return 1

if __name__ == "__main__":
    sys.exit(main())
