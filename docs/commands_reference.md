# Commands Reference

This document provides a reference for commands to verify tweet_count storage and Excel processing workflow.

## Checking Database Schema

To check the schema of the url_tracking table and verify tweet_count storage:

```bash
python3 scripts/tests/check_url_tracking_schema.py
```

This command will show:
- The schema of the url_tracking table
- Whether the table has tweet_count, followers_count, and profile fields
- The number of records in the table
- The number of records with tweet_count > 0
- A sample record from the table

To trace the profile update flow:

```bash
python3 scripts/tests/check_url_tracking_schema.py --trace
```

This command will:
- Check the database before update
- Get profile data for cz_binance
- Update the profile data in the database
- Check the database after update

## Demonstrating Excel Profile Flow

To demonstrate the complete data flow from Excel processing to database storage:

```bash
python3 scripts/tests/demonstrate_excel_profile_flow.py
```

This command will:
- Create a test Excel file
- Check the database before update
- Get profile data for cz_binance
- Update the profile data in the database
- Check the database after update
- Process the Excel file

To use a specific Excel file:

```bash
python3 scripts/tests/demonstrate_excel_profile_flow.py --excel /path/to/excel/file.xlsx
```

To check a different Twitter handle:

```bash
python3 scripts/tests/demonstrate_excel_profile_flow.py --handle twitter_handle
```

## Displaying Database Records

To display records from the url_tracking and kol_character tables:

```bash
python3 scripts/newstruct/display_url_tracking_record.py --screen-name cz_binance
```

This command will show:
- URL tracking fields (including tweet_count)
- KOL character fields

To display records for a specific URL:

```bash
python3 scripts/newstruct/display_url_tracking_record.py --url https://twitter.com/cz_binance
```

To display records in separate tables:

```bash
python3 scripts/newstruct/display_url_tracking_record.py --screen-name cz_binance --format separate
```

## Processing Excel Files

To process an Excel file with Twitter profile data:

```bash
python3 scripts/newstruct/process_excel_with_profile.py /path/to/excel/file.xlsx
```

This command will:
- Read the Excel file
- Process each row
- Update the url_tracking table with profile data
- Update the kol_character table with character data

## Generating Test Excel Files

To generate a test Excel file:

```bash
python3 scripts/tests/create_test_excel_simple.py --output /tmp/test_excel.xlsx
```

This command will create a test Excel file with Twitter profile data for cz_binance.

To generate a test Excel file with x.com domain:

```bash
python3 scripts/tests/generate_test_excel.py --output /tmp/test_excel.xlsx --use-x-domain
```

This command will create a test Excel file with Twitter profile data using the x.com domain.

## Updating Profile Data

To update profile data for a specific handle:

```bash
python3 scripts/profile/update_profile_data.py --handle cz_binance
```

This command will:
- Get profile data for cz_binance
- Update the profile data in the database

## Resetting URL Tracking Table

To reset the url_tracking table with the correct schema:

```bash
sqlite3 data/local_database.db < scripts/database/reset_url_tracking_table.sql
```

This command will:
- Create a backup of the current url_tracking table
- Drop the current url_tracking table
- Create a new url_tracking table with the correct schema
- Restore data from the backup table
- Create indexes for better performance
- Update kol_character table to reference the new url_tracking ids
