# Fix for display_url_tracking_record.py

This document explains the fix for the "no such column: url_tracking.id" error in the display_url_tracking_record.py script.

## Issue

The script was failing with the following error when trying to display joined records:

```
sqlite3.OperationalError: no such column: url_tracking.id
```

## Root Cause

The issue was in the SQL query syntax in the `display_joined_record` function, which was trying to join the `url_tracking` and `kol_character` tables using a complex SQL join. The error was also in how `cursor.description` was being accessed to get column names from the query results.

## Fix

The fix replaces the complex SQL join with a simpler approach that:

1. Queries the `url_tracking` table first to get the record for the specified screen name or URL
2. Gets the `url_tracking_id` from the record
3. Uses the `url_tracking_id` to query the `kol_character` table
4. Displays the records from both tables

This approach is more robust and easier to understand, and it avoids the issues with SQL joins and cursor.description.

## Usage

To display records for a Twitter handle:

```bash
python3 scripts/database/display_url_tracking_record.py --screen-name <twitter_handle>
```

To display records for a Twitter URL:

```bash
python3 scripts/database/display_url_tracking_record.py --url <twitter_url>
```

To display records in separate tables:

```bash
python3 scripts/database/display_url_tracking_record.py --screen-name <twitter_handle> --format separate
```
