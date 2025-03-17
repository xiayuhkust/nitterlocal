# Excel Processing Workflow

This document explains the workflow for processing Excel files with Twitter profile data in the nitterlocal system.

## Generating Test Excel Files

To generate a test Excel file with Twitter profile data:

```bash
python3 scripts/tests/generate_test_excel.py --output /path/to/output.xlsx
```

Options:
- `--output`: Path to save the Excel file (default: /tmp/test_excel.xlsx)
- `--rows`: Number of rows to generate (default: 1)
- `--use-x-domain`: Use x.com domain instead of twitter.com

Examples:
```bash
# Generate test Excel file with twitter.com URLs
python3 scripts/tests/generate_test_excel.py --output /tmp/test_excel.xlsx

# Generate test Excel file with x.com URLs
python3 scripts/tests/generate_test_excel.py --output /tmp/test_excel_x.xlsx --use-x-domain
```

## Processing Excel Files

To process an Excel file with Twitter profile data:

```bash
python3 scripts/database/process_excel_with_profile.py --excel /path/to/excel.xlsx
```

Options:
- `--excel`: Path to the Excel file (required)
- `--db-path`: Path to the SQLite database (default: /home/ubuntu/nitterlocal/data/local_database.db)
- `--display`: Display results for a specific handle

Examples:
```bash
# Process Excel file with default database
python3 scripts/database/process_excel_with_profile.py --excel /tmp/test_excel.xlsx

# Process Excel file with custom database and display results
python3 scripts/database/process_excel_with_profile.py --excel /tmp/test_excel.xlsx --db-path /path/to/custom.db --display cz_binance
```

## Viewing Database Records

To view database records for a specific Twitter handle:

```bash
python3 scripts/database/display_url_tracking_record.py --screen-name <twitter_handle>
```

Options:
- `--screen-name`: Twitter screen name to look up
- `--url`: Twitter URL to look up
- `--format`: Display format: separate tables or joined record (default: joined)
- `--db-path`: Path to the SQLite database (default: /home/ubuntu/nitterlocal/data/local_database.db)

Examples:
```bash
# Display joined record for a Twitter handle
python3 scripts/database/display_url_tracking_record.py --screen-name cz_binance

# Display separate records for a Twitter URL
python3 scripts/database/display_url_tracking_record.py --url https://twitter.com/cz_binance --format separate
```

## URL Normalization

The system automatically normalizes Twitter URLs to ensure consistent handling:

- `https://x.com/username` → `https://twitter.com/username`
- `https://nitter.net/username` → `https://twitter.com/username`

This normalization is necessary because the core scraper only supports twitter.com URLs. All x.com URLs are converted to twitter.com format before being processed.

## Database Schema

The system uses two main tables to store Twitter profile data:

1. `url_tracking`: Stores Twitter URLs and profile information
2. `kol_character`: Stores KOL (Key Opinion Leader) character data

The `url_tracking_id` column in the `kol_character` table links to the `id` column in the `url_tracking` table, establishing a relationship between the two tables.

## Troubleshooting

If you encounter issues with Excel processing:

1. Verify the Excel file exists at the specified path
2. Check that the Excel file has the required columns (Twitter url, etc.)
3. Ensure the database has the necessary tables and columns
4. Check the logs for error messages

For more detailed information, run the scripts with verbose logging enabled.
