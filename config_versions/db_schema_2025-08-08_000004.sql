-- Angles AI Universe™ Database Schema
-- Version: 2.0.0
-- Last Updated: 2025-08-07

-- Core decision vault table
CREATE TABLE IF NOT EXISTS decision_vault (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_text TEXT NOT NULL,
    context TEXT,
    impact_level VARCHAR(20) DEFAULT 'medium',
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    synced BOOLEAN DEFAULT FALSE,
    metadata JSONB
);

-- Configuration change log table
CREATE TABLE IF NOT EXISTS config_change_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name VARCHAR(255) NOT NULL,
    action VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    git_commit_id VARCHAR(64),
    file_type VARCHAR(50),
    details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Memory sync status table
CREATE TABLE IF NOT EXISTS memory_sync_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sync_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    items_processed INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_decision_vault_created_at ON decision_vault(created_at);
CREATE INDEX IF NOT EXISTS idx_decision_vault_synced ON decision_vault(synced);
CREATE INDEX IF NOT EXISTS idx_config_change_log_timestamp ON config_change_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_memory_sync_status_sync_type ON memory_sync_status(sync_type);

-- Create updated_at trigger for decision_vault
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_decision_vault_updated_at BEFORE UPDATE
    ON decision_vault FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();