#!/usr/bin/env python3
"""
Database setup script to create necessary tables in Supabase
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_database():
    """Create the necessary tables for the GPT processor"""
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("Missing SUPABASE_URL or SUPABASE_KEY")
        return False
    
    try:
        supabase = create_client(url, key)
        print("Connected to Supabase successfully")
        
        # SQL statements to create tables
        create_conversations_table = """
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            context JSONB,
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            metadata JSONB
        );
        """
        
        create_memories_table = """
        CREATE TABLE IF NOT EXISTS memories (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            category VARCHAR(100) NOT NULL,
            importance INTEGER DEFAULT 5 CHECK (importance >= 1 AND importance <= 10),
            tags JSONB,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        );
        """
        
        create_tasks_table = """
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'canceled')),
            priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
            due_date TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
        
        create_analysis_table = """
        CREATE TABLE IF NOT EXISTS analysis (
            id SERIAL PRIMARY KEY,
            type VARCHAR(100) NOT NULL,
            data JSONB NOT NULL,
            results JSONB NOT NULL,
            confidence FLOAT DEFAULT 0.5 CHECK (confidence >= 0.0 AND confidence <= 1.0),
            timestamp TIMESTAMPTZ DEFAULT NOW()
        );
        """
        
        # Try to execute the SQL commands
        tables = [
            ("conversations", create_conversations_table),
            ("memories", create_memories_table),
            ("tasks", create_tasks_table),
            ("analysis", create_analysis_table)
        ]
        
        for table_name, sql in tables:
            try:
                result = supabase.rpc('exec_sql', {'sql': sql}).execute()
                print(f"✅ Created/verified table: {table_name}")
            except Exception as e:
                print(f"❌ Failed to create table {table_name}: {str(e)}")
                # Try using the SQL editor approach instead
                print(f"💡 You may need to run this SQL manually in your Supabase SQL editor:")
                print(f"   {sql}")
        
        return True
        
    except Exception as e:
        print(f"Database setup failed: {str(e)}")
        return False

if __name__ == "__main__":
    setup_database()