-- Ensure online_price exists for both date-based and today tables
ALTER TABLE IF NOT EXISTS accommodation_dates
    ADD COLUMN IF NOT EXISTS online_price FLOAT;

ALTER TABLE IF NOT EXISTS today_accommodation_info
    ADD COLUMN IF NOT EXISTS online_price FLOAT;
