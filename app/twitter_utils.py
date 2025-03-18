"""
Twitter utilities for processing URLs and extracting handles.
"""

import logging
from urllib.parse import urlparse

def extract_twitter_handle(url):
    """Extract Twitter handle from URL"""
    if not url:
        return None
    
    try:
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        return path_parts[0].lower() if path_parts else None
    except Exception as e:
        logging.error(f"Error extracting Twitter handle from {url}: {str(e)}")
        return None

def process_twitter_urls(urls):
    """Process Twitter URLs to extract handles"""
    if not urls:
        return []
    
    # Split URLs by comma, newline, or semicolon
    if isinstance(urls, str):
        url_list = [u.strip() for u in urls.replace('\n', ',').replace(';', ',').split(',')]
    else:
        url_list = urls
    
    # Filter out empty strings
    url_list = [u for u in url_list if u]
    
    # Extract handles
    handles = []
    for url in url_list:
        handle = extract_twitter_handle(url)
        if handle:
            handles.append(handle)
    
    return handles
