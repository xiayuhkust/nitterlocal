#!/usr/bin/env python3
"""
Test script to verify that Excel processing works correctly with both twitter.com and x.com domains.
"""

import os
import sys
import logging
import pandas as pd
import sqlite3
import tempfile

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import the functions to test
try:
    from scripts.utils.url_utils import normalize_twitter_url, extract_twitter_handle
    logging.info("Successfully imported url_utils functions")
except ImportError:
    logging.error("Could not import url_utils functions")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def generate_test_excel():
    """Generate a test Excel file with both twitter.com and x.com URLs"""
    logging.info("Generating test Excel file with both twitter.com and x.com URLs")
    
    # Create a DataFrame with both twitter.com and x.com URLs
    data = {
        'Twitter url': [
            'https://twitter.com/cz_binance',
            'https://x.com/cz_binance',
            'https://twitter.com/binance',
            'https://x.com/binance'
        ],
        'first category': ['KOL', 'KOL', 'Exchange', 'Exchange'],
        'second_category': ['-', '-', '-', '-'],
        'bio': [
            'Founder of Binance, crypto exchange leader',
            'Founder of Binance, crypto exchange leader',
            'Leading cryptocurrency exchange',
            'Leading cryptocurrency exchange'
        ],
        'lore': [
            'Born in China, started crypto in 2013, founded Binance in 2017',
            'Born in China, started crypto in 2013, founded Binance in 2017',
            'Founded in 2017, largest crypto exchange by volume',
            'Founded in 2017, largest crypto exchange by volume'
        ],
        'knowledge': [
            'Crypto Trading: Expert in exchange ops. Markets: Analyzes BTC trends. Regulation: Addresses policy',
            'Crypto Trading: Expert in exchange ops. Markets: Analyzes BTC trends. Regulation: Addresses policy',
            'Exchange Operations: Trading pairs, fees. Security: Wallet management. Compliance: Regulatory updates',
            'Exchange Operations: Trading pairs, fees. Security: Wallet management. Compliance: Regulatory updates'
        ],
        'postExamples': [
            '"Bitcoin is controlled by math" 2025/2/20 "BNB adoption grows" 2025/1/15 "Crypto needs clarity" 2024/12/10 "Stay safe in trading" 2024/11/5',
            '"Bitcoin is controlled by math" 2025/2/20 "BNB adoption grows" 2025/1/15 "Crypto needs clarity" 2024/12/10 "Stay safe in trading" 2024/11/5',
            '"New trading pairs added" 2025/2/25 "Security update complete" 2025/1/10 "Trading competition results" 2024/12/5 "New listing announcement" 2024/11/1',
            '"New trading pairs added" 2025/2/25 "Security update complete" 2025/1/10 "Trading competition results" 2024/12/5 "New listing announcement" 2024/11/1'
        ],
        'topics': [
            'Crypto Exchanges: Runs Binance. Market Trends: Tracks BTC. Regulation: Discusses rules',
            'Crypto Exchanges: Runs Binance. Market Trends: Tracks BTC. Regulation: Discusses rules',
            'Exchange Updates: New features, pairs. Market Analysis: Volume trends. Security: Protection measures',
            'Exchange Updates: New features, pairs. Market Analysis: Volume trends. Security: Protection measures'
        ],
        'style_all': [
            'Bold: Confident market takes. Analytical: Ties to trends. Direct: Clear, no-nonsense tone',
            'Bold: Confident market takes. Analytical: Ties to trends. Direct: Clear, no-nonsense tone',
            'Professional: Corporate tone. Informative: Detailed updates. Responsive: Addresses user concerns',
            'Professional: Corporate tone. Informative: Detailed updates. Responsive: Addresses user concerns'
        ],
        'style_chat': [
            'Concise: Brief replies. Confident: Firm stance. Supportive: Helps community',
            'Concise: Brief replies. Confident: Firm stance. Supportive: Helps community',
            'Helpful: Solves user issues. Formal: Business-like tone. Thorough: Complete explanations',
            'Helpful: Solves user issues. Formal: Business-like tone. Thorough: Complete explanations'
        ],
        'style_post': [
            'Concise: Sharp posts. Bold: Strong statements. Informative: Shares updates',
            'Concise: Sharp posts. Bold: Strong statements. Informative: Shares updates',
            'Structured: Organized announcements. Clear: Easy to understand. Timely: Regular updates',
            'Structured: Organized announcements. Clear: Easy to understand. Timely: Regular updates'
        ],
        'adjectives': [
            'Bold, Analytical, Direct',
            'Bold, Analytical, Direct',
            'Professional, Informative, Responsive',
            'Professional, Informative, Responsive'
        ]
    }
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(data)
    output_path = '/tmp/test_both_domains.xlsx'
    df.to_excel(output_path, index=False)
    
    logging.info(f"Generated test Excel file at {output_path}")
    return output_path

def create_test_database():
    """Create a test SQLite database for testing"""
    logging.info("Creating test SQLite database")
    
    # Create a temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create url_tracking table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS url_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        user_id TEXT,
        status INTEGER DEFAULT 0,
        type TEXT,
        subtype TEXT,
        description TEXT,
        screen_name TEXT,
        followers_count INTEGER,
        following_count INTEGER,
        tweet_count INTEGER,
        profile_image_url TEXT,
        profile_banner_url TEXT,
        verified INTEGER DEFAULT 0,
        location TEXT,
        created_at TEXT,
        profile_updated_at TEXT
    )
    ''')
    
    # Create kol_character table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS kol_character (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kol_id TEXT,
        kol_screen_name TEXT NOT NULL,
        bio TEXT,
        lore TEXT,
        knowledge TEXT,
        postExamples TEXT,
        topics TEXT,
        style_all TEXT,
        style_chat TEXT,
        style_post TEXT,
        adjectives TEXT,
        url_tracking_id INTEGER,
        UNIQUE(kol_screen_name)
    )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_url_tracking_url ON url_tracking (url)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_url_tracking_screen_name ON url_tracking (screen_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_kol_character_screen_name ON kol_character (kol_screen_name)')
    
    conn.commit()
    conn.close()
    
    logging.info(f"Created test database at {db_path}")
    return db_path

def process_excel_file(excel_path, db_path):
    """Process the Excel file using the process_excel_with_profile.py script"""
    logging.info(f"Processing Excel file {excel_path} with database {db_path}")
    
    # Import the process_excel function
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database')))
    try:
        from process_excel_with_profile import process_excel_file as process_excel
        logging.info("Successfully imported process_excel_with_profile")
    except ImportError:
        logging.error("Could not import process_excel_with_profile, falling back to process_excel")
        try:
            from process_excel import process_excel_file as process_excel
            logging.info("Successfully imported process_excel")
        except ImportError:
            logging.error("Could not import process_excel")
            return False
    
    # Process the Excel file
    result = process_excel(excel_path, db_path)
    
    return result > 0

def verify_url_normalization(db_path):
    """Verify that x.com URLs were normalized to twitter.com in the database"""
    logging.info(f"Verifying URL normalization in database {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all URLs from the database
    cursor.execute("SELECT url FROM url_tracking")
    urls = [row[0] for row in cursor.fetchall()]
    
    # Check if any URL contains x.com
    x_com_urls = [url for url in urls if 'x.com' in url]
    if x_com_urls:
        logging.error(f"Found {len(x_com_urls)} URLs with x.com domain: {x_com_urls}")
        conn.close()
        return False
    
    # Check if all URLs are normalized to twitter.com
    twitter_com_urls = [url for url in urls if 'twitter.com' in url]
    if len(twitter_com_urls) != len(urls):
        logging.error(f"Not all URLs are normalized to twitter.com: {urls}")
        conn.close()
        return False
    
    logging.info(f"All URLs are normalized to twitter.com: {urls}")
    
    # Due to normalization, we expect 2 unique URLs instead of 4
    # (twitter.com/cz_binance and twitter.com/binance)
    # since x.com URLs are normalized to twitter.com
    if len(urls) != 2:
        logging.error(f"Expected 2 normalized URLs, but found {len(urls)}")
        conn.close()
        return False
    
    # Check if we have the expected handles
    cursor.execute("SELECT screen_name FROM url_tracking")
    handles = [row[0] for row in cursor.fetchall()]
    expected_handles = ['cz_binance', 'binance']
    
    # Sort both lists for comparison
    handles.sort()
    expected_handles.sort()
    
    if handles != expected_handles:
        logging.error(f"Expected handles {expected_handles}, but found {handles}")
        conn.close()
        return False
    
    logging.info(f"Found expected handles: {handles}")
    
    # Check if we have the expected number of kol_character records
    cursor.execute("SELECT kol_screen_name FROM kol_character")
    kol_handles = [row[0] for row in cursor.fetchall()]
    
    # We should have 2 unique handles
    if len(set(kol_handles)) != 2:
        logging.error(f"Expected 2 unique KOL handles, but found {len(set(kol_handles))}: {kol_handles}")
        conn.close()
        return False
    
    logging.info(f"Found expected KOL handles: {kol_handles}")
    
    conn.close()
    return True

def main():
    """Main function"""
    # Generate test Excel file
    excel_path = generate_test_excel()
    
    # Create test database
    db_path = create_test_database()
    
    # Process the Excel file
    if not process_excel_file(excel_path, db_path):
        logging.error("Failed to process Excel file")
        return 1
    
    # Verify URL normalization
    if not verify_url_normalization(db_path):
        logging.error("URL normalization verification failed")
        return 1
    
    logging.info("All tests passed!")
    
    # Clean up
    os.unlink(excel_path)
    os.unlink(db_path)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
