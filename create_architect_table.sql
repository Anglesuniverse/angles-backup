-- Create architect_decisions table for storing architectural decisions
-- Run this SQL script in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS architect_decisions (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'deprecated', 'superseded')),
    tags JSONB DEFAULT '[]'::jsonb,
    CONSTRAINT architect_decisions_content_not_empty CHECK (LENGTH(TRIM(content)) > 0)
);

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_architect_decisions_created_at ON architect_decisions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_architect_decisions_status ON architect_decisions(status);

-- Insert a test record to verify the table works
INSERT INTO architect_decisions (content, status) VALUES 
('Table created successfully - ready for architect decisions', 'active');