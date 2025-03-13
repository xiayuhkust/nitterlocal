"""
Excel processor module for handling Excel files with Twitter URLs.
"""

import os
import pandas as pd
import logging
from typing import List, Dict, Any, Optional, Tuple
import tempfile
import shutil
from .twitter_utils import process_twitter_urls, extract_twitter_handle, get_user_id_from_twitter_handle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ExcelProcessor:
    """Class for processing Excel files with Twitter URLs"""
    
    def __init__(self, upload_dir: str, temp_dir: str):
        """Initialize the Excel processor"""
        self.upload_dir = upload_dir
        self.temp_dir = temp_dir
        
    def read_excel(self, file_path: str) -> Tuple[pd.DataFrame, List[str]]:
        """
        Read an Excel file and extract Twitter URLs
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            Tuple containing the DataFrame and a list of detected Twitter URLs
        """
        try:
            # Read the Excel file
            df = pd.read_excel(file_path)
            
            # Find columns that might contain Twitter URLs
            twitter_urls = []
            url_columns = []
            
            # Check each column for Twitter URLs
            for col in df.columns:
                # Sample the first 10 non-null values (or fewer if there are fewer)
                sample = df[col].dropna().head(10).astype(str)
                
                # Check if any of the values look like Twitter URLs
                if any('twitter.com' in str(val).lower() or 'x.com' in str(val).lower() for val in sample):
                    url_columns.append(col)
                    
                    # Extract all Twitter URLs from this column
                    for val in df[col].dropna().astype(str):
                        if 'twitter.com' in val.lower() or 'x.com' in val.lower():
                            twitter_urls.append(val)
            
            logging.info(f"Found {len(twitter_urls)} Twitter URLs in columns: {url_columns}")
            
            return df, twitter_urls
            
        except Exception as e:
            logging.error(f"Error reading Excel file: {str(e)}")
            raise
    
    def process_excel(self, file_path: str) -> Dict[str, Any]:
        """
        Process an Excel file containing Twitter URLs
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Read the Excel file and extract Twitter URLs
            df, twitter_urls = self.read_excel(file_path)
            
            # Process the Twitter URLs
            processed_urls = process_twitter_urls(twitter_urls)
            
            # Create a results summary
            results = {
                "total_urls": len(twitter_urls),
                "successful": sum(1 for url in processed_urls if url["status"] == "success"),
                "failed": sum(1 for url in processed_urls if url["status"] == "error"),
                "processed_urls": processed_urls
            }
            
            return results
            
        except Exception as e:
            logging.error(f"Error processing Excel file: {str(e)}")
            raise
    
    def add_ids_to_excel(self, file_path: str, processed_urls: List[Dict[str, Any]]) -> str:
        """
        Add Twitter IDs to the Excel file
        
        Args:
            file_path: Path to the original Excel file
            processed_urls: List of processed URLs with their IDs
            
        Returns:
            Path to the new Excel file with IDs added
        """
        try:
            # Read the original Excel file
            df = pd.read_excel(file_path)
            
            # Create a mapping of URLs to user IDs
            url_to_id = {url["url"]: url["user_id"] for url in processed_urls if url["status"] == "success"}
            url_to_handle = {url["url"]: url["handle"] for url in processed_urls if url["status"] == "success"}
            
            # Find columns that might contain Twitter URLs
            for col in df.columns:
                # Check if this column contains Twitter URLs
                if df[col].astype(str).str.contains('twitter.com|x.com').any():
                    # Create new columns for handle and user ID
                    handle_col = f"{col}_handle"
                    user_id_col = f"{col}_user_id"
                    
                    # Add the handle and user ID columns
                    df[handle_col] = df[col].apply(
                        lambda x: url_to_handle.get(str(x), None) if pd.notna(x) else None
                    )
                    df[user_id_col] = df[col].apply(
                        lambda x: url_to_id.get(str(x), None) if pd.notna(x) else None
                    )
            
            # Create a new file path for the processed file
            filename = os.path.basename(file_path)
            base_name, ext = os.path.splitext(filename)
            new_filename = f"{base_name}_with_ids{ext}"
            new_file_path = os.path.join(self.temp_dir, new_filename)
            
            # Save the DataFrame to the new file
            df.to_excel(new_file_path, index=False)
            
            return new_file_path
            
        except Exception as e:
            logging.error(f"Error adding IDs to Excel file: {str(e)}")
            raise
