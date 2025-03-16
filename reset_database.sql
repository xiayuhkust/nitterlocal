-- Reset database structure
PRAGMA foreign_keys = OFF;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS kol_character;
DROP TABLE IF EXISTS url_tracking;
DROP VIEW IF EXISTS kol_character_with_url;

-- Create url_tracking table with id as PRIMARY KEY
CREATE TABLE url_tracking (
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

-- Create kol_character table with url_tracking_id foreign key
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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_url_tracking_user_id ON url_tracking (user_id);
CREATE INDEX IF NOT EXISTS idx_url_tracking_screen_name ON url_tracking (screen_name);
CREATE INDEX IF NOT EXISTS idx_url_tracking_type ON url_tracking (type);
CREATE INDEX IF NOT EXISTS idx_kol_character_kol_id ON kol_character (kol_id);
CREATE INDEX IF NOT EXISTS idx_kol_character_url_tracking_id ON kol_character (url_tracking_id);

-- Create view for joined data
CREATE VIEW IF NOT EXISTS kol_character_with_url AS
SELECT 
    k.id, k.kol_id, k.kol_screen_name, k.bio, k.lore, k.knowledge,
    k.postExamples, k.topics, k.style_all, k.style_chat, k.style_post,
    k.adjectives, k.url_tracking_id,
    u.url, u.type, u.subtype, u.user_id, u.screen_name
FROM 
    kol_character k
LEFT JOIN 
    url_tracking u ON k.url_tracking_id = u.id;

PRAGMA foreign_keys = ON;

-- Verify the changes
SELECT 'Database structure reset successfully' AS result;
