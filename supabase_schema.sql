-- Supabase Schema for Bidirectional Sync
-- Run this SQL in your Supabase SQL Editor to set up the decision_vault table
-- for Angles AI Universe™ bidirectional sync service

-- Create decision_vault table if it doesn't exist
CREATE TABLE IF NOT EXISTS decision_vault (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision TEXT NOT NULL,
    type TEXT NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    notion_page_id TEXT NULL,
    notion_synced BOOLEAN DEFAULT FALSE,
    checksum TEXT NULL
);

-- Add missing columns to existing table (if needed)
-- Run these individually if your table already exists

-- Add notion_page_id column
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='decision_vault' AND column_name='notion_page_id') THEN
        ALTER TABLE decision_vault ADD COLUMN notion_page_id TEXT;
    END IF;
END $$;

-- Add notion_synced column
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='decision_vault' AND column_name='notion_synced') THEN
        ALTER TABLE decision_vault ADD COLUMN notion_synced BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Add checksum column
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='decision_vault' AND column_name='checksum') THEN
        ALTER TABLE decision_vault ADD COLUMN checksum TEXT;
    END IF;
END $$;

-- Add updated_at column
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='decision_vault' AND column_name='updated_at') THEN
        ALTER TABLE decision_vault ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
END $$;

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_decision_vault_notion_page_id 
ON decision_vault(notion_page_id);

CREATE INDEX IF NOT EXISTS idx_decision_vault_checksum 
ON decision_vault(checksum);

CREATE INDEX IF NOT EXISTS idx_decision_vault_notion_synced 
ON decision_vault(notion_synced);

CREATE INDEX IF NOT EXISTS idx_decision_vault_type 
ON decision_vault(type);

CREATE INDEX IF NOT EXISTS idx_decision_vault_date 
ON decision_vault(date);

CREATE INDEX IF NOT EXISTS idx_decision_vault_created_at 
ON decision_vault(created_at);

CREATE INDEX IF NOT EXISTS idx_decision_vault_updated_at 
ON decision_vault(updated_at);

-- Create function to automatically update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to update updated_at automatically
DROP TRIGGER IF EXISTS update_decision_vault_updated_at ON decision_vault;
CREATE TRIGGER update_decision_vault_updated_at 
    BEFORE UPDATE ON decision_vault 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add constraints for data integrity
ALTER TABLE decision_vault 
    ADD CONSTRAINT check_decision_not_empty 
    CHECK (LENGTH(TRIM(decision)) > 0);

ALTER TABLE decision_vault 
    ADD CONSTRAINT check_type_not_empty 
    CHECK (LENGTH(TRIM(type)) > 0);

ALTER TABLE decision_vault 
    ADD CONSTRAINT check_type_valid 
    CHECK (type IN ('Policy', 'Architecture', 'Ops', 'UX', 'Other'));

-- Add comments for documentation
COMMENT ON TABLE decision_vault IS 'Architect decisions for Angles AI Universe™ with bidirectional Notion sync';
COMMENT ON COLUMN decision_vault.id IS 'Primary key UUID';
COMMENT ON COLUMN decision_vault.decision IS 'The decision text/description';
COMMENT ON COLUMN decision_vault.type IS 'Decision type: Policy, Architecture, Ops, UX, Other';
COMMENT ON COLUMN decision_vault.date IS 'Decision date';
COMMENT ON COLUMN decision_vault.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN decision_vault.updated_at IS 'Record last update timestamp (auto-updated)';
COMMENT ON COLUMN decision_vault.notion_page_id IS 'Corresponding Notion page ID for sync';
COMMENT ON COLUMN decision_vault.notion_synced IS 'Whether record has been synced to Notion';
COMMENT ON COLUMN decision_vault.checksum IS 'SHA256 checksum of decision|type|date for change detection';

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL ON decision_vault TO authenticated;
-- GRANT USAGE ON SCHEMA public TO authenticated;

-- Insert sample data (optional - remove if not needed)
INSERT INTO decision_vault (decision, type, date) 
VALUES 
    ('Implement user authentication with OAuth2', 'Architecture', '2025-08-07'),
    ('Establish code review process for all PRs', 'Policy', '2025-08-07'),
    ('Set up automated CI/CD pipeline', 'Ops', '2025-08-07'),
    ('Design mobile-first responsive interface', 'UX', '2025-08-07'),
    ('Standardize API error response format', 'Other', '2025-08-07')
ON CONFLICT DO NOTHING;

-- Verify table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'decision_vault' 
ORDER BY ordinal_position;