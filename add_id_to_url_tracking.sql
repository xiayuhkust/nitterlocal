-- Add id column to url_tracking table if it doesn't exist
PRAGMA foreign_keys = OFF;

-- Create a temporary table with the desired structure
CREATE TABLE url_tracking_temp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    user_id TEXT,
    description TEXT,
    status TEXT DEFAULT 'active',
    last_checked TEXT,
    error_count INTEGER DEFAULT 0,
    tweet_count INTEGER DEFAULT 0,
    type TEXT,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_scraped TEXT,
    last_error TEXT,
    subtype TEXT,
    screen_name TEXT
);

-- Copy data from the original table to the temporary table
INSERT INTO url_tracking_temp (url, user_id, description, status, last_checked, error_count, tweet_count, type, added_at, last_scraped, last_error, subtype, screen_name)
SELECT url, user_id, description, status, last_checked, error_count, tweet_count, type, added_at, last_scraped, last_error, subtype, screen_name
FROM url_tracking;

-- Drop the original table
DROP TABLE url_tracking;

-- Rename the temporary table to the original name
ALTER TABLE url_tracking_temp RENAME TO url_tracking;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_url_tracking_user_id ON url_tracking (user_id);
CREATE INDEX IF NOT EXISTS idx_url_tracking_screen_name ON url_tracking (screen_name);
CREATE INDEX IF NOT EXISTS idx_url_tracking_type ON url_tracking (type);

PRAGMA foreign_keys = ON;

-- Verify the changes
SELECT 'Table url_tracking updated successfully with id as PRIMARY KEY' AS result;
