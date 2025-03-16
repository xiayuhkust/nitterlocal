-- Insert sample data into url_tracking
INSERT INTO url_tracking (url, user_id, description, type, subtype, screen_name)
VALUES 
('https://twitter.com/trader_xo', '608297384153714', 'Crypto trader', 'kol', 'crypto', 'trader_xo'),
('https://twitter.com/ivanontech', '123456789', 'Crypto educator', 'kol', 'crypto', 'ivanontech'),
('https://twitter.com/petermccormack', '987654321', 'Bitcoin podcaster', 'kol', 'crypto', 'petermccormack');

-- Insert sample data into kol_character
INSERT INTO kol_character (kol_id, kol_screen_name, bio, lore, knowledge, postExamples, topics, style_all, style_chat, style_post, adjectives)
VALUES 
('608297384153714', 'trader_xo', 'Crypto trader, market analyst', 'Active in crypto since 2017, known for TA on X', 'Crypto Trading: Expert in TA and price action. Market Trends: Analyzes BTC and alts', '"BTC testing 70K resistance" 2025/2/5 "Altcoins showing strength" 2025/1/20 "RSI signals overbought" 2024/12/15 "Expect a pullback soon" 2024/11/10', 'Crypto Trading: Shares TA insights. Market Trends: Tracks price moves. Predictions: Forecasts short-term shifts', 'Analytical: Focuses on charts and data. Precise: Clear TA calls. Practical: Offers trading tips', 'Concise: Short, sharp replies. Analytical: Data-driven answers. Helpful: Guides traders', 'Brief: Quick market updates. Technical: Uses TA terms. Predictive: Calls out price moves', 'Analytical, Precise, Practical');

-- Update kol_character to link with url_tracking
UPDATE kol_character
SET url_tracking_id = (SELECT id FROM url_tracking WHERE user_id = kol_character.kol_id)
WHERE kol_id = '608297384153714';

-- Verify the data
SELECT 'Sample data inserted successfully' AS result;
