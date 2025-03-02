#!/usr/bin/env python3
"""
URL Manager for the local database.
This module provides functionality for managing URLs in the local database.
"""

import sqlite3
import os
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class URLManager:
    def __init__(self, db_path='data/local_database.db'):
        """Initialize the URL manager with a database path"""
        self.db_path = db_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
    def _get_db_connection(self):
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
        
    def get_urls(self, status=None, limit=None):
        """Get all URLs, optionally filtered by status"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            if status:
                cursor.execute("SELECT * FROM url_tracking WHERE status = ? LIMIT ?", (status, limit or -1))
            else:
                cursor.execute("SELECT * FROM url_tracking LIMIT ?", (limit or -1,))
            
            urls = [dict(row) for row in cursor.fetchall()]
            return urls
        except Exception as e:
            logging.error(f"Error getting URLs: {str(e)}")
            return []
        finally:
            conn.close()
            
    def add_url(self, url, description="", url_type="kol"):
        """Add a new URL to track"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Check if URL already exists
            cursor.execute("SELECT * FROM url_tracking WHERE url = ?", (url,))
            existing_url = cursor.fetchone()
            
            if existing_url:
                return dict(existing_url)
                
            # Add new URL
            now = datetime.now().isoformat()
            cursor.execute("""
            INSERT INTO url_tracking (
                url, description, status, last_checked, error_count, tweet_count, type, added_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                url, description, 'active', now, 0, 0, url_type, now
            ))
            
            conn.commit()
            
            # Get the inserted URL
            cursor.execute("SELECT * FROM url_tracking WHERE url = ?", (url,))
            return dict(cursor.fetchone())
        except Exception as e:
            logging.error(f"Error adding URL {url}: {e}")
            return None
        finally:
            conn.close()
            
    def update_url_status(self, url, status, error=None):
        """Update the status of a URL"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.now().isoformat()
            
            if error:
                cursor.execute("""
                UPDATE url_tracking 
                SET status = ?, last_checked = ?, error_count = error_count + 1, last_error = ?
                WHERE url = ?
                """, (status, now, error, url))
            else:
                cursor.execute("""
                UPDATE url_tracking 
                SET status = ?, last_checked = ?, error_count = 0
                WHERE url = ?
                """, (status, now, url))
            
            if cursor.rowcount == 0:
                logging.warning(f"URL {url} not found")
                return None
            
            conn.commit()
            
            # Get the updated URL
            cursor.execute("SELECT * FROM url_tracking WHERE url = ?", (url,))
            return dict(cursor.fetchone())
        except Exception as e:
            logging.error(f"Error updating URL status for {url}: {e}")
            return None
        finally:
            conn.close()
            
    def update_last_scraped(self, url):
        """Update the last_scraped timestamp for a URL"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.now().isoformat()
            
            cursor.execute("""
            UPDATE url_tracking 
            SET last_scraped = ?
            WHERE url = ?
            """, (now, url))
            
            if cursor.rowcount == 0:
                logging.warning(f"URL {url} not found")
                return None
            
            conn.commit()
            
            # Get the updated URL
            cursor.execute("SELECT * FROM url_tracking WHERE url = ?", (url,))
            return dict(cursor.fetchone())
        except Exception as e:
            logging.error(f"Error updating last_scraped for {url}: {e}")
            return None
        finally:
            conn.close()
            
    def remove_url(self, url):
        """Remove a URL from tracking"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM url_tracking WHERE url = ?", (url,))
            
            if cursor.rowcount == 0:
                logging.warning(f"URL {url} not found")
                return False
            
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error removing URL {url}: {e}")
            return False
        finally:
            conn.close()
            
    def update_tweet_count(self, url, count):
        """Update the tweet count for a URL"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
            UPDATE url_tracking 
            SET tweet_count = tweet_count + ?
            WHERE url = ?
            """, (count, url))
            
            if cursor.rowcount == 0:
                logging.warning(f"URL {url} not found")
                return None
            
            conn.commit()
            
            # Get the updated URL
            cursor.execute("SELECT * FROM url_tracking WHERE url = ?", (url,))
            return dict(cursor.fetchone())
        except Exception as e:
            logging.error(f"Error updating tweet count for {url}: {e}")
            return None
        finally:
            conn.close()
