-- Create decision_vault table in Supabase
-- Run this SQL script in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS decision_vault (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision TEXT NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    type TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT decision_vault_decision_not_empty CHECK (LENGTH(TRIM(decision)) > 0),
    CONSTRAINT decision_vault_type_not_empty CHECK (LENGTH(TRIM(type)) > 0),
    CONSTRAINT decision_vault_type_valid CHECK (type IN ('strategy', 'technical', 'ethical', 'architecture', 'process', 'security', 'other'))
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_decision_vault_date ON decision_vault(date DESC);
CREATE INDEX IF NOT EXISTS idx_decision_vault_type ON decision_vault(type);
CREATE INDEX IF NOT EXISTS idx_decision_vault_active ON decision_vault(active);
CREATE INDEX IF NOT EXISTS idx_decision_vault_created_at ON decision_vault(created_at DESC);

-- Create trigger to automatically update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_decision_vault_updated_at 
    BEFORE UPDATE ON decision_vault 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert test data to verify table works
INSERT INTO decision_vault (decision, date, type, active, comment) VALUES 
('Use PostgreSQL as primary database for better performance', CURRENT_DATE, 'technical', true, 'Decision made after performance analysis'),
('Implement Code Review for all pull requests', CURRENT_DATE - INTERVAL '1 day', 'process', true, 'Improves code quality and knowledge sharing'),
('Use HTTPS for all communication', CURRENT_DATE - INTERVAL '2 days', 'security', true, 'Security department requirement');

-- Show table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'decision_vault'
ORDER BY ordinal_position;