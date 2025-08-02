-- GPT Processor Database Schema
-- Create fresh tables for the AI memory system

-- Drop existing tables if they exist (fresh setup)
DROP TABLE IF EXISTS analysis CASCADE;
DROP TABLE IF EXISTS tasks CASCADE;
DROP TABLE IF EXISTS memories CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;

-- Table for storing conversation history and interactions
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    context JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,
    CONSTRAINT conversations_user_id_not_empty CHECK (LENGTH(user_id) > 0),
    CONSTRAINT conversations_content_not_empty CHECK (LENGTH(content) > 0)
);

-- Table for storing long-term memory and knowledge
CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    importance INTEGER DEFAULT 5 CHECK (importance >= 1 AND importance <= 10),
    tags JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT memories_content_not_empty CHECK (LENGTH(content) > 0),
    CONSTRAINT memories_category_not_empty CHECK (LENGTH(category) > 0)
);

-- Table for storing tasks and action items
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'canceled')),
    priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    due_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT tasks_title_not_empty CHECK (LENGTH(title) > 0),
    CONSTRAINT tasks_description_not_empty CHECK (LENGTH(description) > 0)
);

-- Table for storing analysis results and insights
CREATE TABLE analysis (
    id SERIAL PRIMARY KEY,
    type VARCHAR(100) NOT NULL,
    data JSONB NOT NULL,
    results JSONB NOT NULL,
    confidence FLOAT DEFAULT 0.5 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT analysis_type_not_empty CHECK (LENGTH(type) > 0)
);

-- Create indexes for better performance
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_timestamp ON conversations(timestamp);
CREATE INDEX idx_memories_category ON memories(category);
CREATE INDEX idx_memories_importance ON memories(importance);
CREATE INDEX idx_memories_timestamp ON memories(timestamp);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_analysis_type ON analysis(type);
CREATE INDEX idx_analysis_timestamp ON analysis(timestamp);

-- Create indexes for JSONB fields
CREATE INDEX idx_conversations_metadata_gin ON conversations USING gin(metadata);
CREATE INDEX idx_memories_tags_gin ON memories USING gin(tags);
CREATE INDEX idx_analysis_data_gin ON analysis USING gin(data);
CREATE INDEX idx_analysis_results_gin ON analysis USING gin(results);

-- Insert sample data to verify tables work correctly
INSERT INTO conversations (user_id, content, context, metadata) VALUES 
('system', 'Database tables created successfully', '{"setup": true}', '{"source": "setup_script", "version": "1.0"}');

INSERT INTO memories (content, category, importance, tags) VALUES 
('GPT Processor database initialized with fresh schema', 'system', 8, '["setup", "database", "initialization"]');

INSERT INTO tasks (title, description, priority) VALUES 
('Test GPT processor functionality', 'Verify that the application can process GPT outputs and store them correctly', 'high');

INSERT INTO analysis (type, data, results, confidence) VALUES 
('setup_verification', '{"tables_created": 4, "indexes_created": 10}', '{"status": "success", "message": "Database setup completed"}', 1.0);