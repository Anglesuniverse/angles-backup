-- Create ai_decision_log table in Supabase
-- Run this SQL script in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS ai_decision_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_text TEXT NOT NULL,
    decision_type TEXT NOT NULL DEFAULT 'general',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    context TEXT,
    confidence DECIMAL(3,2) CHECK (confidence >= 0.0 AND confidence <= 1.0),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT ai_decision_log_text_not_empty CHECK (LENGTH(TRIM(decision_text)) > 0),
    CONSTRAINT ai_decision_log_type_not_empty CHECK (LENGTH(TRIM(decision_type)) > 0)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_ai_decision_log_timestamp ON ai_decision_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ai_decision_log_type ON ai_decision_log(decision_type);
CREATE INDEX IF NOT EXISTS idx_ai_decision_log_confidence ON ai_decision_log(confidence);
CREATE INDEX IF NOT EXISTS idx_ai_decision_log_created_at ON ai_decision_log(created_at DESC);

-- Create index on metadata for JSON queries
CREATE INDEX IF NOT EXISTS idx_ai_decision_log_metadata ON ai_decision_log USING GIN (metadata);

-- Insert test data to verify table works
INSERT INTO ai_decision_log (decision_text, decision_type, context, confidence, metadata) VALUES 
('Recommended using PostgreSQL over MongoDB for this use case due to ACID compliance requirements', 'technical', 'User asked about database selection for financial application', 0.92, '{"factors": ["ACID compliance", "query complexity", "team expertise"]}'),
('Suggested implementing rate limiting for API endpoints to prevent abuse', 'security', 'Discussion about API security best practices', 0.87, '{"priority": "high", "implementation_time": "1-2 days"}'),
('Advised using React hooks instead of class components for better performance', 'recommendation', 'Code review feedback', 0.95, '{"code_section": "user-profile-component", "impact": "performance"}');

-- Show table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'ai_decision_log'
ORDER BY ordinal_position;