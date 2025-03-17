#!/usr/bin/env python3
"""
Script to view and filter url_tracking and kol_character data from the SQLite database.
This helps verify that URL normalization is working correctly and provides a way to
explore the database contents with various filtering options.
"""

import os
import sys
import sqlite3
import logging
import argparse
import pandas as pd
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_database_stats(db_path):
    """Get statistics about the database tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    stats = {}
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        # Get record count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        
        stats[table] = {
            'count': count,
            'columns': columns
        }
    
    conn.close()
    return stats

def view_url_tracking(db_path, filter_term=None, limit=20, export=None, format_output=True):
    """View and filter url_tracking data"""
    conn = sqlite3.connect(db_path)
    
    # Build query
    query = "SELECT * FROM url_tracking"
    params = []
    
    if filter_term:
        query += " WHERE url LIKE ? OR screen_name LIKE ? OR user_id LIKE ?"
        params = [f"%{filter_term}%", f"%{filter_term}%", f"%{filter_term}%"]
    
    query += f" ORDER BY id DESC LIMIT {limit}"
    
    # Execute query using pandas
    df = pd.read_sql_query(query, conn, params=params)
    
    # Export if requested
    if export:
        export_path = f"{export}_url_tracking_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        df.to_csv(export_path, index=False)
        logging.info(f"Exported URL tracking data to {export_path}")
    
    # Display results
    if format_output:
        print("\n=== URL Tracking Data ===")
        if not df.empty:
            # Select most relevant columns for display
            display_cols = ['id', 'url', 'screen_name', 'user_id', 'followers_count', 
                           'following_count', 'tweet_count', 'verified', 'profile_updated_at']
            display_cols = [col for col in display_cols if col in df.columns]
            
            # Format the output
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 200)
            pd.set_option('display.max_colwidth', 40)
            
            print(df[display_cols].to_string())
            print(f"\nShowing {len(df)} of {conn.execute('SELECT COUNT(*) FROM url_tracking').fetchone()[0]} records")
        else:
            print("No records found in url_tracking table")
    
    conn.close()
    return df

def view_kol_character(db_path, filter_term=None, limit=20, export=None, format_output=True):
    """View and filter kol_character data"""
    conn = sqlite3.connect(db_path)
    
    # Build query
    query = "SELECT * FROM kol_character"
    params = []
    
    if filter_term:
        query += " WHERE kol_screen_name LIKE ? OR kol_id LIKE ? OR bio LIKE ?"
        params = [f"%{filter_term}%", f"%{filter_term}%", f"%{filter_term}%"]
    
    query += f" ORDER BY id DESC LIMIT {limit}"
    
    # Execute query using pandas
    df = pd.read_sql_query(query, conn, params=params)
    
    # Export if requested
    if export:
        export_path = f"{export}_kol_character_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        df.to_csv(export_path, index=False)
        logging.info(f"Exported KOL character data to {export_path}")
    
    # Display results
    if format_output:
        print("\n=== KOL Character Data ===")
        if not df.empty:
            # Select most relevant columns for display
            display_cols = ['id', 'kol_id', 'kol_screen_name', 'bio', 'url_tracking_id']
            display_cols = [col for col in display_cols if col in df.columns]
            
            # Format the output
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 200)
            pd.set_option('display.max_colwidth', 40)
            
            print(df[display_cols].to_string())
            print(f"\nShowing {len(df)} of {conn.execute('SELECT COUNT(*) FROM kol_character').fetchone()[0]} records")
        else:
            print("No records found in kol_character table")
    
    conn.close()
    return df

def view_joined_data(db_path, filter_term=None, limit=20, export=None, format_output=True):
    """View joined data from url_tracking and kol_character tables"""
    conn = sqlite3.connect(db_path)
    
    # Build query
    query = """
    SELECT 
        u.id as url_id,
        u.url, 
        u.screen_name, 
        u.user_id,
        u.followers_count,
        u.following_count,
        u.tweet_count,
        u.verified,
        k.id as kol_id,
        k.kol_screen_name, 
        k.bio,
        k.url_tracking_id
    FROM url_tracking u
    LEFT JOIN kol_character k ON u.id = k.url_tracking_id
    """
    params = []
    
    if filter_term:
        query += """ WHERE u.url LIKE ? 
                  OR u.screen_name LIKE ? 
                  OR k.kol_screen_name LIKE ?
                  OR u.user_id LIKE ?
                  OR k.kol_id LIKE ?
                  OR k.bio LIKE ?"""
        params = [f"%{filter_term}%", f"%{filter_term}%", f"%{filter_term}%", 
                 f"%{filter_term}%", f"%{filter_term}%", f"%{filter_term}%"]
    
    query += f" ORDER BY u.id DESC LIMIT {limit}"
    
    # Execute query using pandas
    df = pd.read_sql_query(query, conn, params=params)
    
    # Export if requested
    if export:
        export_path = f"{export}_joined_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        df.to_csv(export_path, index=False)
        logging.info(f"Exported joined data to {export_path}")
    
    # Display results
    if format_output:
        print("\n=== Joined URL Tracking and KOL Character Data ===")
        if not df.empty:
            # Format the output
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 200)
            pd.set_option('display.max_colwidth', 30)
            
            print(df.to_string())
            print(f"\nShowing {len(df)} of {conn.execute('SELECT COUNT(*) FROM url_tracking').fetchone()[0]} records")
        else:
            print("No joined records found")
    
    conn.close()
    return df

def search_by_domain(db_path, domain, limit=20, export=None):
    """Search for URLs with a specific domain"""
    conn = sqlite3.connect(db_path)
    
    # Build query
    query = "SELECT * FROM url_tracking WHERE url LIKE ?"
    params = [f"%{domain}%"]
    
    query += f" ORDER BY id DESC LIMIT {limit}"
    
    # Execute query using pandas
    df = pd.read_sql_query(query, conn, params=params)
    
    # Export if requested
    if export:
        export_path = f"{export}_domain_{domain}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        df.to_csv(export_path, index=False)
        logging.info(f"Exported domain search results to {export_path}")
    
    # Display results
    print(f"\n=== URLs with Domain '{domain}' ===")
    if not df.empty:
        # Select most relevant columns for display
        display_cols = ['id', 'url', 'screen_name', 'user_id']
        
        # Format the output
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 200)
        pd.set_option('display.max_colwidth', 50)
        
        print(df[display_cols].to_string())
        print(f"\nFound {len(df)} URLs with domain '{domain}'")
    else:
        print(f"No URLs found with domain '{domain}'")
    
    conn.close()
    return df

def check_domain_distribution(db_path):
    """Check the distribution of domains in the url_tracking table"""
    conn = sqlite3.connect(db_path)
    
    # Get all URLs
    query = "SELECT url FROM url_tracking"
    df = pd.read_sql_query(query, conn)
    
    # Extract domains
    def extract_domain(url):
        if not isinstance(url, str):
            return "invalid"
        if "twitter.com" in url:
            return "twitter.com"
        elif "x.com" in url:
            return "x.com"
        elif "nitter.net" in url:
            return "nitter.net"
        else:
            return "other"
    
    df['domain'] = df['url'].apply(extract_domain)
    
    # Count domains
    domain_counts = df['domain'].value_counts()
    
    # Display results
    print("\n=== Domain Distribution in URL Tracking ===")
    print(domain_counts)
    
    conn.close()
    return domain_counts

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="View and filter database records")
    parser.add_argument("--db-path", default="data/local_database.db", help="Path to the SQLite database")
    parser.add_argument("--table", choices=["url", "kol", "joined", "all", "stats", "domains"], default="all", 
                        help="Table to view: url_tracking, kol_character, joined data, statistics, domain distribution, or all")
    parser.add_argument("--filter", help="Filter term to search for in the database")
    parser.add_argument("--limit", type=int, default=20, help="Limit the number of records to display")
    parser.add_argument("--export", help="Export results to CSV files with this prefix")
    parser.add_argument("--domain", help="Search for URLs with a specific domain (twitter.com, x.com, etc.)")
    
    args = parser.parse_args()
    
    # Check if the database exists
    if not os.path.exists(args.db_path):
        logging.error(f"Database file not found: {args.db_path}")
        return 1
    
    # If domain search is requested, perform it
    if args.domain:
        search_by_domain(args.db_path, args.domain, args.limit, args.export)
        return 0
    
    # Display the requested data
    if args.table == "stats" or args.table == "all":
        stats = get_database_stats(args.db_path)
        print("\n=== Database Statistics ===")
        for table, data in stats.items():
            print(f"Table: {table}")
            print(f"  Records: {data['count']}")
            print(f"  Columns: {', '.join(data['columns'])}")
            print()
    
    if args.table == "domains" or args.table == "all":
        check_domain_distribution(args.db_path)
    
    if args.table == "url" or args.table == "all":
        view_url_tracking(args.db_path, args.filter, args.limit, args.export)
    
    if args.table == "kol" or args.table == "all":
        view_kol_character(args.db_path, args.filter, args.limit, args.export)
    
    if args.table == "joined" or args.table == "all":
        view_joined_data(args.db_path, args.filter, args.limit, args.export)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
