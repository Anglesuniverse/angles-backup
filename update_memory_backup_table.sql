-- Update memory_backup_log table to support manual backups with tags
-- Adds columns for backup_type distinction and tag support

-- Add new columns if they don't exist
ALTER TABLE memory_backup_log 
ADD COLUMN IF NOT EXISTS tag TEXT,
ADD COLUMN IF NOT EXISTS github_commit_hash VARCHAR(64),
ADD COLUMN IF NOT EXISTS github_commit_url TEXT;

-- Update backup_type column to ensure it supports both daily and manual
ALTER TABLE memory_backup_log 
ALTER COLUMN backup_type SET DEFAULT 'daily';

-- Add constraint to ensure backup_type is valid
ALTER TABLE memory_backup_log 
DROP CONSTRAINT IF EXISTS check_backup_type;

ALTER TABLE memory_backup_log 
ADD CONSTRAINT check_backup_type CHECK (backup_type IN ('daily', 'manual'));

-- Create indexes for new columns
CREATE INDEX IF NOT EXISTS idx_memory_backup_log_tag ON memory_backup_log(tag);
CREATE INDEX IF NOT EXISTS idx_memory_backup_log_github_commit ON memory_backup_log(github_commit_hash);

-- Create view for manual backups
CREATE OR REPLACE VIEW manual_memory_backups AS
SELECT 
    filename,
    tag,
    timestamp,
    status,
    file_count,
    file_size,
    duration_seconds,
    github_commit_hash,
    github_commit_url,
    storage_url,
    error_message
FROM memory_backup_log
WHERE backup_type = 'manual'
ORDER BY timestamp DESC;

-- Create view for recent tagged backups (last 30 days)
CREATE OR REPLACE VIEW recent_tagged_backups AS
SELECT 
    backup_type,
    tag,
    filename,
    timestamp,
    status,
    file_count,
    file_size,
    github_commit_hash
FROM memory_backup_log
WHERE timestamp >= NOW() - INTERVAL '30 days'
    AND tag IS NOT NULL
ORDER BY timestamp DESC;

-- Update comments
COMMENT ON COLUMN memory_backup_log.tag IS 'Optional tag for manual backups (e.g., hotfix, v2.1.0)';
COMMENT ON COLUMN memory_backup_log.github_commit_hash IS 'Git commit hash for backup files pushed to repository';
COMMENT ON COLUMN memory_backup_log.github_commit_url IS 'Full URL to GitHub commit for traceability';
COMMENT ON VIEW manual_memory_backups IS 'Shows all manual memory backups with tags and GitHub integration';
COMMENT ON VIEW recent_tagged_backups IS 'Shows tagged backups from the last 30 days across all backup types';