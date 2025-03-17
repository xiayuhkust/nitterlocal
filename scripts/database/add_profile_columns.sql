-- SQL script to add profile-related columns to url_tracking table
-- Run with: sqlite3 data/local_database.db < scripts/database/add_profile_columns.sql

-- Add followers_count column if it doesn't exist
ALTER TABLE url_tracking ADD COLUMN followers_count INTEGER DEFAULT 0;

-- Add following_count column if it doesn't exist
ALTER TABLE url_tracking ADD COLUMN following_count INTEGER DEFAULT 0;

-- Add profile_image_url column if it doesn't exist
ALTER TABLE url_tracking ADD COLUMN profile_image_url TEXT;

-- Add profile_banner_url column if it doesn't exist
ALTER TABLE url_tracking ADD COLUMN profile_banner_url TEXT;

-- Add verified column if it doesn't exist
ALTER TABLE url_tracking ADD COLUMN verified INTEGER DEFAULT 0;

-- Add location column if it doesn't exist
ALTER TABLE url_tracking ADD COLUMN location TEXT;

-- Add created_at column if it doesn't exist
ALTER TABLE url_tracking ADD COLUMN created_at TEXT;

-- Add profile_updated_at column if it doesn't exist
ALTER TABLE url_tracking ADD COLUMN profile_updated_at TEXT;

-- Display the updated schema
PRAGMA table_info(url_tracking);
