# Twitter ID Management in Nitterlocal

This document explains how Twitter user IDs are managed in the Nitterlocal system.

## ID Extraction Methods

The system uses a hierarchical approach to obtain Twitter user IDs:

1. **Primary Method**: Twitter API/client extraction
   - Example: `902926941413453824` for cz_binance
   - Implementation: `TwitterScraper.extract_user_id_from_handle()`
   - Source: Direct Twitter API call

2. **Secondary Method**: Direct client call
   - Implementation: `get_user_id_from_direct_client_call()`
   - Source: Alternative API method

3. **Fallback Method**: Hash-based generation
   - Implementation: `get_user_id_fallback()`
   - Source: MD5 hash of the handle, converted to a 15-digit number
   - Used only when API methods fail

## ID Storage and Relationships

- **url_tracking.user_id**: Stores the Twitter user ID (preferably from API)
- **kol_character.kol_id**: Matches url_tracking.user_id for consistency
- **kol_character.url_tracking_id**: Foreign key to url_tracking.id

## Synchronization Process

When synchronizing data between SQLite and MySQL:

- SQLite's `url_tracking.user_id` is mapped to MySQL's `kol_info.kol_id`
- Profile data is generated in SQLite before being synced to MySQL
- The system ensures consistent ID mapping across databases

## Profile Data Management

Profile data (followers_count, following_count, etc.) is:

1. Fetched using the Twitter API
2. Stored in the url_tracking table
3. Updated periodically via cron jobs
4. Synchronized to MySQL during the sync process

## Best Practices

- Always use the API-provided user ID when available
- Maintain the relationship between url_tracking and kol_character tables
- Ensure consistent ID mapping during synchronization
- Use the existing ID extraction hierarchy for reliability
