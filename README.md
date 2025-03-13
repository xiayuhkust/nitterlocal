# Twitter Data Extraction

This project provides tools for extracting and analyzing Twitter data.

## Overview

The system extracts tweets from Twitter accounts and stores them in a local database for analysis. It supports various types of Twitter accounts, including KOLs (Key Opinion Leaders), institutions, exchanges, and meme tokens.

## URL Format

The system now uses Twitter URLs (https://twitter.com/username) instead of Nitter URLs.
All existing URLs in the database will be automatically converted to Twitter format when running the migration script.

## Migration

To migrate existing URLs in the database from Nitter to Twitter format, run:

```bash
python scripts/migrations/convert_urls_to_twitter.py
```

To verify that all URLs have been converted to Twitter format, run:

```bash
python scripts/tests/test_url_migration.py
```

## Adding URLs

When adding new URLs, use the Twitter format (https://twitter.com/username):

```bash
python scripts/utils/add_urls.py --file data/sample_urls_with_cmc.json
```

## Database Schema

The database schema includes the following tables:

- `url_tracking`: Stores information about Twitter URLs to track
- `tweets`: Stores tweets extracted from the tracked URLs

## Data Analysis

The system provides various tools for analyzing the extracted tweets:

- Count tweets per URL
- Analyze hashtags
- Export tweets to JSON or CSV
- Remove duplicate tweets

## CoinMarketCap Integration

The system can fetch top exchanges and meme tokens from CoinMarketCap and add them to the database:

```bash
python scripts/utils/fetch_coinmarketcap_data.py
```

## Twitter Client

The system uses a Twitter client to extract tweets directly from Twitter. The client requires authentication credentials to be set in the `.env` file.

## Backend Service

The project includes a FastAPI backend service for processing Excel files with Twitter URLs:

### Installation

```bash
cd nitterlocal
pip install -r app/requirements.txt
```

### Starting the Backend

```bash
./start_backend.sh
```

The backend service will be available at http://0.0.0.0:8000

### Features

- Upload Excel files containing Twitter URLs
- Extract Twitter user IDs from URLs
- Process and update local database tables (url_tracking and kol_character)
- Synchronize data with MySQL database
- Download processed Excel files with extracted IDs

## Usage

For detailed usage instructions, see [USAGE.md](USAGE.md).

## Data Analysis Guide

For detailed data analysis instructions, see [DATA_ANALYSIS_GUIDE.md](DATA_ANALYSIS_GUIDE.md).
