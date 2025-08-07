-- MemorySyncAgent™ Backup Log Table
-- Tracks all memory backup attempts and results

CREATE TABLE IF NOT EXISTS memory_backup_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT NOT NULL CHECK (status IN ('success', 'failure')),
    storage_url TEXT,
    file_size BIGINT,
    file_count INTEGER,
    error_message TEXT,
    duration_seconds REAL,
    backup_type TEXT DEFAULT 'daily',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_memory_backup_log_timestamp ON memory_backup_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_memory_backup_log_status ON memory_backup_log(status);
CREATE INDEX IF NOT EXISTS idx_memory_backup_log_backup_type ON memory_backup_log(backup_type);

-- Create view for recent backups
CREATE OR REPLACE VIEW recent_memory_backups AS
SELECT 
    filename,
    timestamp,
    status,
    file_count,
    file_size,
    duration_seconds,
    error_message
FROM memory_backup_log
WHERE timestamp >= NOW() - INTERVAL '30 days'
ORDER BY timestamp DESC;

COMMENT ON TABLE memory_backup_log IS 'Tracks MemorySyncAgent™ backup operations to Supabase storage';
COMMENT ON VIEW recent_memory_backups IS 'Shows memory backups from the last 30 days';