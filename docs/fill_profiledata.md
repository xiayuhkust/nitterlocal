# Fill Profile Data Script

This script retrieves profile data (tweet_count, followers_count, etc.) from Twitter and updates the url_tracking table.

## Usage

```bash
python3 scripts/newstruct/fill_profiledata.py --handle <twitter_handle>
python3 scripts/newstruct/fill_profiledata.py --url <twitter_url>
python3 scripts/newstruct/fill_profiledata.py --all
python3 scripts/newstruct/fill_profiledata.py --all --limit 10
```

## Options

- `--db-path`: Path to the SQLite database (default: data/local_database.db)
- `--handle`: Twitter handle to update
- `--url`: Twitter URL to update
- `--all`: Update all profiles
- `--limit`: Limit the number of profiles to update

## Examples

```bash
# Update profile for cz_binance
python3 scripts/newstruct/fill_profiledata.py --handle cz_binance

# Update profile for a Twitter URL
python3 scripts/newstruct/fill_profiledata.py --url https://twitter.com/cz_binance

# Update all profiles
python3 scripts/newstruct/fill_profiledata.py --all

# Update the first 10 profiles
python3 scripts/newstruct/fill_profiledata.py --all --limit 10
```

## Data Flow

1. The script retrieves profile data from Twitter using the Twitter profile client
2. The profile data is extracted and formatted
3. The url_tracking table is updated with the retrieved profile data

## Profile Fields

The following fields are updated in the url_tracking table:

- `user_id`: Twitter user ID
- `screen_name`: Twitter handle
- `followers_count`: Number of followers
- `following_count`: Number of accounts following
- `tweet_count`: Number of tweets
- `profile_image_url`: URL of profile image
- `profile_banner_url`: URL of profile banner
- `verified`: Whether the account is verified
- `location`: Account location
- `description`: Account description
- `created_at`: Account creation date
- `profile_updated_at`: Date when profile was last updated
