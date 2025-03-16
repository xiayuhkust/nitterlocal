-- Setup script for initial tweet crawl
-- This script:
-- 1. Creates the activity_levels table if it doesn't exist
-- 2. Sets up fixed tweet quantities (30 regular tweets, 10 reply tweets) for all active URLs

-- Create activity_levels table if it doesn't exist
CREATE TABLE IF NOT EXISTS activity_levels (
    url TEXT PRIMARY KEY,
    activity_level TEXT,
    update_interval INTEGER DEFAULT 15,
    last_activity_check TEXT,
    post_frequency REAL,
    avg_interactions REAL,
    last_post_time TEXT,
    max_tweets INTEGER DEFAULT 10,
    max_replies INTEGER DEFAULT 5,
    FOREIGN KEY (url) REFERENCES url_tracking (url)
);

-- Create index on activity_level column
CREATE INDEX IF NOT EXISTS idx_activity_levels_level ON activity_levels (activity_level);

-- Delete existing entries (if any)
DELETE FROM activity_levels;

-- Insert entries for all active URLs with fixed tweet quantities
INSERT INTO activity_levels (url, activity_level, last_activity_check, max_tweets, max_replies)
SELECT 
    url, 
    'initial_crawl', 
    datetime('now'), 
    30, -- Fixed value for max_tweets
    10  -- Fixed value for max_replies
FROM url_tracking 
WHERE status = 'active';

-- Verify the setup
SELECT COUNT(*) AS total_entries FROM activity_levels;
