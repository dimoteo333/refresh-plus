-- Adds a summary column to store up to 5 key features per accommodation
-- NOTE: SQLite (our local/dev database) doesn't support JSONB or "IF NOT EXISTS"
--       in ALTER TABLE statements. The following statements are SQLite-compatible.
    ALTER TABLE accommodations
    ADD COLUMN summary TEXT DEFAULT '[]';

-- Initialize null entries to an empty list for consistency
UPDATE accommodations
SET summary = '[]'
WHERE summary IS NULL;

-- If you are running against PostgreSQL instead, use the snippet below instead.
--
-- ALTER TABLE accommodations
-- ADD COLUMN IF NOT EXISTS summary JSONB DEFAULT '[]'::jsonb;
--
-- UPDATE accommodations
-- SET summary = '[]'::jsonb
-- WHERE summary IS NULL;
