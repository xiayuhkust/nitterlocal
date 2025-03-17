# Database Schema Analysis

This document provides a detailed analysis of the database schema, focusing on the url_tracking and kol_character tables.

## URL Tracking Table

The url_tracking table stores information about Twitter profiles being tracked:

```sql
CREATE TABLE url_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE,
    user_id TEXT,
    description TEXT,
    status TEXT DEFAULT 'active',
    last_checked TIMESTAMP,
    error_count INTEGER DEFAULT 0,
    tweet_count INTEGER DEFAULT 0,
    type TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_scraped TIMESTAMP,
    last_error TEXT,
    subtype TEXT DEFAULT '-',
    screen_name TEXT,
    followers_count INTEGER,
    following_count INTEGER,
    profile_image_url TEXT,
    profile_banner_url TEXT,
    verified INTEGER,
    location TEXT,
    created_at TEXT,
    profile_updated_at TIMESTAMP
);
```

### Key Fields

- **id**: Primary key for the table
- **url**: Twitter URL (unique)
- **user_id**: Twitter user ID
- **description**: Twitter profile description
- **tweet_count**: Number of tweets by the user
- **screen_name**: Twitter handle
- **followers_count**: Number of followers
- **following_count**: Number of accounts followed
- **profile_image_url**: URL to profile image
- **profile_banner_url**: URL to profile banner
- **verified**: Whether the account is verified (1 = yes, 0 = no)

### Indexes

```sql
CREATE INDEX IF NOT EXISTS idx_url_tracking_screen_name ON url_tracking(screen_name);
CREATE INDEX IF NOT EXISTS idx_url_tracking_user_id ON url_tracking(user_id);
```

## KOL Character Table

The kol_character table stores character information for Key Opinion Leaders (KOLs):

```sql
CREATE TABLE kol_character (
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
    FOREIGN KEY (url_tracking_id) REFERENCES url_tracking(id)
);
```

### Key Fields

- **id**: Primary key for the table
- **kol_id**: KOL identifier
- **kol_screen_name**: Twitter handle
- **bio**: Short biography
- **lore**: Background information
- **knowledge**: Areas of expertise
- **postExamples**: Example posts
- **topics**: Topics of interest
- **style_all**: Overall communication style
- **style_chat**: Chat communication style
- **style_post**: Post communication style
- **adjectives**: Descriptive adjectives
- **url_tracking_id**: Foreign key to url_tracking table

### Indexes

```sql
CREATE INDEX IF NOT EXISTS idx_kol_character_url_tracking_id ON kol_character(url_tracking_id);
```

## Relationship Between Tables

The kol_character table is linked to the url_tracking table through the url_tracking_id foreign key:

```
url_tracking(id) ← kol_character(url_tracking_id)
```

This relationship allows:
- Retrieving profile data from url_tracking for a KOL
- Retrieving character data from kol_character for a Twitter profile
- Joining the tables to get complete information about a KOL

## Sample Record

### URL Tracking Record

```json
{
  "id": 1,
  "url": "https://twitter.com/cz_binance",
  "user_id": "902926941413453824",
  "description": "holder of BNB and BTC\n@BNBchain community member\n@YZiLabs intern\n@GiggleAcademy founder\n@binance founder and ex-CEO",
  "status": "active",
  "last_checked": null,
  "error_count": 0,
  "tweet_count": 9423,
  "type": "KOL",
  "added_at": "2025-03-17 07:40:30",
  "last_scraped": null,
  "last_error": null,
  "subtype": "-",
  "screen_name": "cz_binance",
  "followers_count": 9960542,
  "following_count": 1756,
  "profile_image_url": "https://pbs.twimg.com/profile_images/1781374522966601732/HA_dnDvL.jpg",
  "profile_banner_url": "https://pbs.twimg.com/profile_banners/902926941413453824/1597864552",
  "verified": 1,
  "location": "",
  "created_at": "2017-08-30T16:12:13.000Z",
  "profile_updated_at": "2025-03-17T09:55:14.877629"
}
```

### KOL Character Record

```json
{
  "id": 1,
  "kol_id": "902926941413453824",
  "kol_screen_name": "cz_binance",
  "bio": "Binance创始人赵长鹏",
  "lore": "Active in crypto since 2017",
  "knowledge": "Crypto Trading: Expert in TA and price action",
  "postExamples": "BTC testing 70K resistance",
  "topics": "Crypto Trading: Shares TA insights",
  "style_all": "Analytical: Focuses on charts and data",
  "style_chat": "Concise: Short, sharp replies",
  "style_post": "Brief: Quick market updates",
  "adjectives": "Analytical, Precise, Practical",
  "url_tracking_id": 1
}
```

## Schema Verification

The schema can be verified using the check_url_tracking_schema.py script:

```
=== Schema for table 'url_tracking' ===
ID    Name                 Type            NotNull  Default         PK
----------------------------------------------------------------------
0     id                   INTEGER         0        None            1
1     url                  TEXT            0        None            0
2     user_id              TEXT            0        None            0
3     description          TEXT            0        None            0
4     status               TEXT            0        'active'        0
5     last_checked         TEXT            0        None            0
6     error_count          INTEGER         0        0               0
7     tweet_count          INTEGER         0        0               0
8     type                 TEXT            0        None            0
9     added_at             TEXT            0        CURRENT_TIMESTAMP 0
10    last_scraped         TEXT            0        None            0
11    last_error           TEXT            0        None            0
12    subtype              TEXT            0        None            0
13    screen_name          TEXT            0        None            0
14    followers_count      INTEGER         0        0               0
15    following_count      INTEGER         0        0               0
16    profile_image_url    TEXT            0        None            0
17    profile_banner_url   TEXT            0        None            0
18    verified             INTEGER         0        0               0
19    location             TEXT            0        None            0
20    created_at           TEXT            0        None            0
21    profile_updated_at   TEXT            0        None            0
```

## Conclusion

The database schema is well-designed for storing Twitter profile data and KOL character information. The url_tracking table includes a tweet_count column that stores the number of tweets by the user, and this data is being correctly populated during the Excel processing workflow.
