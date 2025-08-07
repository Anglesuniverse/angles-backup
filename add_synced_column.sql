-- Add synced tracking columns to decision_vault table
-- Run this in your Supabase SQL Editor

-- Add synced column if it doesn't exist
ALTER TABLE decision_vault 
ADD COLUMN IF NOT EXISTS synced BOOLEAN DEFAULT FALSE;

-- Add synced_at timestamp column
ALTER TABLE decision_vault 
ADD COLUMN IF NOT EXISTS synced_at TIMESTAMPTZ;

-- Create index on synced column for better performance
CREATE INDEX IF NOT EXISTS idx_decision_vault_synced ON decision_vault(synced);

-- Create index on synced_at for tracking
CREATE INDEX IF NOT EXISTS idx_decision_vault_synced_at ON decision_vault(synced_at);

-- Update existing records to be unsynced by default
UPDATE decision_vault 
SET synced = FALSE 
WHERE synced IS NULL;

-- Show updated table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'decision_vault'
ORDER BY ordinal_position;