-- Create index on decision_vault(date)
CREATE INDEX IF NOT EXISTS idx_decision_vault_date ON decision_vault(date DESC);;

-- Create index on decision_vault(type)
CREATE INDEX IF NOT EXISTS idx_decision_vault_type ON decision_vault(type);;

-- Create index on decision_vault(synced)
CREATE INDEX IF NOT EXISTS idx_decision_vault_synced ON decision_vault(synced);;

-- Create index on agent_activity(agent_name)
CREATE INDEX IF NOT EXISTS idx_agent_activity_agent_name ON agent_activity(agent_name);;

-- Create index on agent_activity(created_at)
CREATE INDEX IF NOT EXISTS idx_agent_activity_created_at ON agent_activity(created_at DESC);;

