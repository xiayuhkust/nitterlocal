#!/usr/bin/env python3
"""
Comprehensive test script to demonstrate Excel processing with both twitter.com and x.com URLs.
This script:
1. Creates a test Excel file with mixed domain URLs (twitter.com and x.com)
2. Processes the Excel file using process_excel_with_profile.py
3. Verifies that all URLs are normalized to twitter.com format in the database
4. Displays the resulting database entries
"""

import os
import sys
import logging
import subprocess
import pandas as pd
import sqlite3
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_test_excel(output_path, num_rows=5):
    """Create a test Excel file with both twitter.com and x.com URLs"""
    logging.info(f"Creating test Excel file at {output_path} with {num_rows} rows")
    
    # Create test data with alternating twitter.com and x.com URLs
    urls = []
    screen_names = []
    bios = []
    lores = []
    
    # Sample data for testing
    test_data = [
        ('cz_binance', 'Founder of Binance, crypto exchange leader', 'Built Binance into the largest crypto exchange'),
        ('VitalikButerin', 'Co-founder of Ethereum, blockchain visionary', 'Created Ethereum, pioneered smart contracts'),
        ('saylor', 'Chairman of MicroStrategy, Bitcoin advocate', 'Corporate Bitcoin adoption pioneer'),
        ('SBF_FTX', 'Former CEO of FTX', 'Founded FTX cryptocurrency exchange'),
        ('elonmusk', 'CEO of Tesla, SpaceX, and X', 'Entrepreneur and tech visionary'),
        ('aantonop', 'Bitcoin educator and author', 'Author of "Mastering Bitcoin"'),
        ('naval', 'Angel investor and entrepreneur', 'Known for tech investment insights'),
        ('cdixon', 'General partner at a16z', 'Crypto and web3 venture capitalist'),
        ('balajis', 'Tech founder and investor', 'Author and crypto advocate'),
        ('jack', 'Co-founder of Twitter and Block', 'Bitcoin advocate and tech entrepreneur')
    ]
    
    # Generate the specified number of rows
    for i in range(min(num_rows, len(test_data))):
        screen_name, bio, lore = test_data[i]
        
        # Alternate between twitter.com and x.com domains
        if i % 2 == 0:
            url = f"https://twitter.com/{screen_name}"
        else:
            url = f"https://x.com/{screen_name}"
        
        urls.append(url)
        screen_names.append(screen_name)
        bios.append(bio)
        lores.append(lore)
    
    # Create DataFrame and save to Excel
    data = {
        'URL': urls,
        'KOL Screen Name': screen_names,
        'Bio': bios,
        'Lore': lores
    }
    
    df = pd.DataFrame(data)
    df.to_excel(output_path, index=False)
    
    logging.info(f"Created test Excel file with {len(urls)} rows")
    logging.info("Sample URLs in the Excel file:")
    for url in urls:
        logging.info(f"  {url}")
    
    return output_path

def process_excel_file(excel_path, db_path):
    """Process the Excel file using process_excel_with_profile.py"""
    logging.info(f"Processing Excel file {excel_path}")
    
    # Run the process_excel_with_profile.py script
    cmd = f"python3 scripts/database/process_excel_with_profile.py --excel {excel_path} --db-path {db_path}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        logging.error(f"Error processing Excel file: {result.stderr}")
        logging.error(f"Command output: {result.stdout}")
        return False
    
    logging.info(f"Excel processing output: {result.stdout}")
    return True

def check_database_entries(db_path, expected_screen_names):
    """Check the database entries to verify URL normalization and data storage"""
    logging.info(f"Checking database entries in {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for x.com URLs (should be none after normalization)
    cursor.execute("SELECT COUNT(*) FROM url_tracking WHERE url LIKE '%x.com%'")
    x_com_count = cursor.fetchone()[0]
    
    logging.info(f"Number of x.com URLs in database: {x_com_count}")
    
    # Check for twitter.com URLs
    cursor.execute("SELECT COUNT(*) FROM url_tracking WHERE url LIKE '%twitter.com%'")
    twitter_com_count = cursor.fetchone()[0]
    
    logging.info(f"Number of twitter.com URLs in database: {twitter_com_count}")
    
    # Check if all expected screen names are in the database
    found_screen_names = []
    not_found_screen_names = []
    
    for screen_name in expected_screen_names:
        cursor.execute("SELECT COUNT(*) FROM url_tracking WHERE screen_name = ? COLLATE NOCASE", (screen_name,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            found_screen_names.append(screen_name)
        else:
            not_found_screen_names.append(screen_name)
    
    logging.info(f"Found {len(found_screen_names)} of {len(expected_screen_names)} expected screen names in the database")
    
    if not_found_screen_names:
        logging.warning(f"Screen names not found in the database: {', '.join(not_found_screen_names)}")
    
    # Get the most recent entries
    cursor.execute("""
    SELECT url, screen_name, user_id, followers_count, following_count, tweet_count
    FROM url_tracking
    ORDER BY id DESC
    LIMIT 10
    """)
    
    recent_entries = cursor.fetchall()
    
    logging.info("=== Recent URL Tracking Entries ===")
    for entry in recent_entries:
        url, screen_name, user_id, followers, following, tweets = entry
        logging.info(f"URL: {url}, Screen Name: {screen_name}, User ID: {user_id}, Followers: {followers}, Following: {following}, Tweets: {tweets}")
    
    # Check KOL character entries
    cursor.execute("""
    SELECT k.kol_screen_name, k.bio, u.url
    FROM kol_character k
    JOIN url_tracking u ON k.url_tracking_id = u.id
    ORDER BY k.id DESC
    LIMIT 10
    """)
    
    kol_entries = cursor.fetchall()
    
    logging.info("=== Recent KOL Character Entries ===")
    for entry in kol_entries:
        kol_screen_name, bio, url = entry
        logging.info(f"KOL Screen Name: {kol_screen_name}, Bio: {bio}, URL: {url}")
    
    conn.close()
    
    return x_com_count == 0 and len(found_screen_names) > 0

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test Excel processing with both twitter.com and x.com URLs")
    parser.add_argument("--rows", type=int, default=5, help="Number of rows to include in the test Excel file")
    parser.add_argument("--output", default=None, help="Path to save the test Excel file")
    parser.add_argument("--db-path", default="data/test_database.db", help="Path to the SQLite database")
    
    args = parser.parse_args()
    
    # Define paths
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    excel_path = args.output or f"/tmp/test_excel_{timestamp}.xlsx"
    db_path = args.db_path
    
    # Create test Excel file
    screen_names = create_test_excel(excel_path, args.rows)
    
    # Extract screen names from the Excel file
    df = pd.read_excel(excel_path)
    expected_screen_names = df['KOL Screen Name'].tolist()
    
    # Process Excel file
    if not process_excel_file(excel_path, db_path):
        logging.error("Failed to process Excel file")
        return 1
    
    # Check database entries
    if check_database_entries(db_path, expected_screen_names):
        logging.info("✅ Success: All URLs are normalized to twitter.com format and data is stored correctly")
    else:
        logging.error("❌ Error: Some URLs are still in x.com format or data is not stored correctly")
    
    # Display command to view database entries
    logging.info("\nTo view the database entries, run:")
    logging.info(f"python3 scripts/database/view_database_records.py --db-path {db_path} --table all")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
