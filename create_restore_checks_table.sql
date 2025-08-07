-- Create restore_checks table for weekly memory recovery test logging
-- Run this SQL in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS restore_checks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    test_run_timestamp TIMESTAMPTZ DEFAULT NOW(),
    total_tests INTEGER NOT NULL,
    passed_tests INTEGER NOT NULL,
    failed_tests INTEGER NOT NULL,
    success_rate DECIMAL(5,2) NOT NULL,
    duration_seconds DECIMAL(10,3) NOT NULL,
    test_details JSONB,
    github_pushed BOOLEAN DEFAULT FALSE,
    scheduler_version VARCHAR(20) DEFAULT '1.0.0',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_restore_checks_timestamp 
ON restore_checks(test_run_timestamp);

CREATE INDEX IF NOT EXISTS idx_restore_checks_success_rate 
ON restore_checks(success_rate);

-- Enable Row Level Security (if needed)
ALTER TABLE restore_checks ENABLE ROW LEVEL SECURITY;

-- Create policy to allow authenticated users to read/write their own data
CREATE POLICY IF NOT EXISTS "Allow authenticated access" ON restore_checks
    FOR ALL USING (auth.role() = 'authenticated');

-- Grant permissions
GRANT ALL ON restore_checks TO authenticated;
GRANT USAGE ON SCHEMA public TO authenticated;