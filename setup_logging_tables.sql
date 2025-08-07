-- Angles AI Universe™ Backend Logging Tables Setup
-- Run this SQL in your Supabase SQL Editor to create the three logging tables

-- 1. Decision Vault Table
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

-- Drop existing constraint if it exists
ALTER TABLE decision_vault DROP CONSTRAINT IF EXISTS decision_vault_type_valid;
ALTER TABLE decision_vault DROP CONSTRAINT IF EXISTS check_type_valid;

-- Add correct constraint for decision types
ALTER TABLE decision_vault 
    ADD CONSTRAINT decision_vault_type_valid 
    CHECK (type IN ('Policy', 'Architecture', 'Ops', 'UX', 'Other'));

-- Add other constraints
ALTER TABLE decision_vault 
    ADD CONSTRAINT decision_vault_decision_not_empty 
    CHECK (LENGTH(TRIM(decision)) > 0);

-- 2. Memory Log Table
CREATE TABLE IF NOT EXISTS memory_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    event_description TEXT NOT NULL,
    metadata JSONB NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add constraints for memory_log
ALTER TABLE memory_log 
    ADD CONSTRAINT memory_log_event_type_not_empty 
    CHECK (LENGTH(TRIM(event_type)) > 0);

ALTER TABLE memory_log 
    ADD CONSTRAINT memory_log_description_not_empty 
    CHECK (LENGTH(TRIM(event_description)) > 0);

-- 3. Agent Activity Table
CREATE TABLE IF NOT EXISTS agent_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name TEXT NOT NULL,
    activity_description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'completed',
    metadata JSONB NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add constraints for agent_activity
ALTER TABLE agent_activity 
    ADD CONSTRAINT agent_activity_status_valid 
    CHECK (status IN ('started', 'completed', 'failed', 'in_progress'));

ALTER TABLE agent_activity 
    ADD CONSTRAINT agent_activity_agent_name_not_empty 
    CHECK (LENGTH(TRIM(agent_name)) > 0);

ALTER TABLE agent_activity 
    ADD CONSTRAINT agent_activity_description_not_empty 
    CHECK (LENGTH(TRIM(activity_description)) > 0);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_decision_vault_type ON decision_vault(type);
CREATE INDEX IF NOT EXISTS idx_decision_vault_date ON decision_vault(date);
CREATE INDEX IF NOT EXISTS idx_decision_vault_created_at ON decision_vault(created_at);
CREATE INDEX IF NOT EXISTS idx_decision_vault_notion_synced ON decision_vault(notion_synced);

CREATE INDEX IF NOT EXISTS idx_memory_log_event_type ON memory_log(event_type);
CREATE INDEX IF NOT EXISTS idx_memory_log_created_at ON memory_log(created_at);

CREATE INDEX IF NOT EXISTS idx_agent_activity_agent_name ON agent_activity(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_activity_status ON agent_activity(status);
CREATE INDEX IF NOT EXISTS idx_agent_activity_created_at ON agent_activity(created_at);

-- Create triggers to auto-update updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Decision vault trigger
DROP TRIGGER IF EXISTS update_decision_vault_updated_at ON decision_vault;
CREATE TRIGGER update_decision_vault_updated_at 
    BEFORE UPDATE ON decision_vault 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Agent activity trigger
DROP TRIGGER IF EXISTS update_agent_activity_updated_at ON agent_activity;
CREATE TRIGGER update_agent_activity_updated_at 
    BEFORE UPDATE ON agent_activity 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE decision_vault IS 'System decisions for Angles AI Universe™';
COMMENT ON TABLE memory_log IS 'Significant events and system changes log';
COMMENT ON TABLE agent_activity IS 'Agent activities and status tracking';

-- Insert sample data to verify tables work correctly
INSERT INTO decision_vault (decision, type, date) 
VALUES ('Initialize comprehensive logging system', 'Architecture', CURRENT_DATE)
ON CONFLICT DO NOTHING;

INSERT INTO memory_log (event_type, event_description) 
VALUES ('system_setup', 'Logging tables created successfully')
ON CONFLICT DO NOTHING;

INSERT INTO agent_activity (agent_name, activity_description, status) 
VALUES ('setup_agent', 'Database schema initialization', 'completed')
ON CONFLICT DO NOTHING;

-- Grant permissions (adjust as needed)
-- GRANT ALL ON decision_vault TO authenticated;
-- GRANT ALL ON memory_log TO authenticated;
-- GRANT ALL ON agent_activity TO authenticated;