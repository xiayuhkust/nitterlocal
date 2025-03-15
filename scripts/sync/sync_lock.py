#!/usr/bin/env python3
"""
Lock mechanism for synchronization scripts to prevent overlapping executions.
"""

import os
import sys
import time
import fcntl
import errno
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SyncLock:
    """Lock mechanism for synchronization scripts"""
    
    def __init__(self, lock_file=None, timeout=None):
        """Initialize the lock
        
        Args:
            lock_file: Path to the lock file
            timeout: Maximum time in seconds to wait for the lock
        """
        self.lock_file = lock_file or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'data/sync_lock.pid'
        )
        self.timeout = timeout
        self.lock_fd = None
        self.locked = False
    
    def acquire(self):
        """Acquire the lock
        
        Returns:
            bool: True if the lock was acquired, False otherwise
        """
        try:
            # Create the directory if it doesn't exist
            lock_dir = os.path.dirname(self.lock_file)
            os.makedirs(lock_dir, exist_ok=True)
            
            # Open the lock file
            self.lock_fd = open(self.lock_file, 'w')
            
            # Try to acquire the lock
            start_time = time.time()
            while True:
                try:
                    fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except IOError as e:
                    if e.errno != errno.EAGAIN:
                        raise
                    
                    # Check if we've timed out
                    if self.timeout and time.time() - start_time > self.timeout:
                        logging.warning(f"Timed out waiting for lock: {self.lock_file}")
                        return False
                    
                    # Wait a bit before trying again
                    time.sleep(1)
            
            # Write the PID to the lock file
            self.lock_fd.write(str(os.getpid()))
            self.lock_fd.flush()
            
            self.locked = True
            logging.info(f"Acquired lock: {self.lock_file}")
            return True
        
        except Exception as e:
            logging.error(f"Error acquiring lock: {str(e)}")
            if self.lock_fd:
                self.lock_fd.close()
                self.lock_fd = None
            return False
    
    def release(self):
        """Release the lock"""
        if self.locked and self.lock_fd:
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                self.lock_fd.close()
                self.lock_fd = None
                self.locked = False
                logging.info(f"Released lock: {self.lock_file}")
            except Exception as e:
                logging.error(f"Error releasing lock: {str(e)}")
    
    def __enter__(self):
        """Context manager entry"""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()

def main():
    """Main function for testing the lock"""
    parser = argparse.ArgumentParser(description='Test the synchronization lock')
    parser.add_argument('--lock-file', type=str, help='Path to the lock file')
    parser.add_argument('--timeout', type=int, default=5, help='Timeout in seconds')
    parser.add_argument('--hold', type=int, default=10, help='Time to hold the lock in seconds')
    
    args = parser.parse_args()
    
    lock = SyncLock(args.lock_file, args.timeout)
    
    if lock.acquire():
        logging.info(f"Lock acquired, holding for {args.hold} seconds")
        time.sleep(args.hold)
        lock.release()
        return 0
    else:
        logging.warning("Could not acquire lock, another process is running")
        return 1

if __name__ == "__main__":
    sys.exit(main())
