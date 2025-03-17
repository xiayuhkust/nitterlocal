-- SQL script to reset the url_tracking table
-- This script will:
-- 1. Create a backup of the current url_tracking table
-- 2. Drop the current url_tracking table
-- 3. Create a new url_tracking table with the correct schema
-- 4. Restore data from the backup table
-- 5. Drop the backup table

-- 1. Create a backup of the current url_tracking table
CREATE TABLE IF NOT EXISTS url_tracking_backup AS SELECT * FROM url_tracking;

-- 2. Drop the current url_tracking table
DROP TABLE IF EXISTS url_tracking;

-- 3. Create a new url_tracking table with the correct schema
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

-- 4. Restore data from the backup table
INSERT INTO url_tracking (
    url, user_id, description, status, last_checked, error_count, 
    tweet_count, type, added_at, last_scraped, last_error, subtype,
    screen_name, followers_count, following_count, profile_image_url,
    profile_banner_url, verified, location, created_at, profile_updated_at
)
SELECT 
    url, user_id, description, status, last_checked, error_count, 
    tweet_count, type, added_at, last_scraped, last_error, subtype,
    screen_name, followers_count, following_count, profile_image_url,
    profile_banner_url, verified, location, created_at, profile_updated_at
FROM url_tracking_backup;

-- 5. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_url_tracking_screen_name ON url_tracking(screen_name);
CREATE INDEX IF NOT EXISTS idx_url_tracking_user_id ON url_tracking(user_id);

-- 6. Update kol_character table to reference the new url_tracking ids
-- First, create a temporary table to map old URLs to new IDs
CREATE TEMPORARY TABLE url_id_mapping AS
SELECT url_tracking.id AS new_id, url_tracking.url AS url
FROM url_tracking;

-- Update kol_character table with the new url_tracking_id values
UPDATE kol_character
SET url_tracking_id = (
    SELECT new_id 
    FROM url_id_mapping 
    WHERE url = (
        SELECT url 
        FROM url_tracking 
        WHERE id = kol_character.url_tracking_id
    )
);

-- 7. Drop the backup table (optional - you may want to keep it for safety)
-- DROP TABLE IF EXISTS url_tracking_backup;

-- 8. Verify the new table
SELECT 'New url_tracking table created successfully with ' || COUNT(*) || ' records.' AS result FROM url_tracking;
