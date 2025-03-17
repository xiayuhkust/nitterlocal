# Commands Reference for Tweet Count Verification

This document provides a reference for commands to verify tweet_count storage during Excel processing.

## Verifying Tweet Count Storage

To verify that tweet_count data is correctly stored in the url_tracking table during Excel processing, you can use the following commands:

### 1. Demonstrate Tweet Count Workflow

```bash
python3 scripts/newstruct/demonstrate_tweet_count_workflow.py
```

This command will:
1. Create a test Excel file with Twitter profile data
2. Process the Excel file using the process_excel_with_profile.py script
3. Check the database before and after processing to verify that tweet_count is stored

### 2. Reset Database and Test Excel Processing

```bash
python3 scripts/newstruct/reset_and_test_excel_processing.py --db-path data/test_database.db
```

This command will:
1. Create a backup of the database
2. Reset the database by dropping and recreating tables
3. Create a test Excel file with Twitter profile data
4. Process the Excel file using the process_excel_with_profile.py script
5. Display the results to verify that tweet_count is stored

To skip database backup and reset:

```bash
python3 scripts/newstruct/reset_and_test_excel_processing.py --db-path data/test_database.db --no-backup --no-reset
```

### 3. Display URL Tracking Record

```bash
python3 scripts/newstruct/display_url_tracking_record.py --screen-name cz_binance
```

This command will display the url_tracking and kol_character records for the specified Twitter handle, including the tweet_count field.

## Conclusion

These commands provide a comprehensive way to verify that tweet_count data is correctly stored in the url_tracking table during Excel processing. The data flow is complete and works as expected.
