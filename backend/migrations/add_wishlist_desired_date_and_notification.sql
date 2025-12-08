-- Add desired_date and notification fields to wishlists table
-- Note: SQLite doesn't support IF NOT EXISTS for ALTER TABLE ADD COLUMN
-- This migration should only be run once
ALTER TABLE wishlists ADD COLUMN desired_date DATE;
ALTER TABLE wishlists ADD COLUMN notification_type TEXT;
ALTER TABLE wishlists ADD COLUMN fcm_token TEXT;
