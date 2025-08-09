#!/usr/bin/env python3
"""
Angles OS™ Database Migration
Creates all required tables for the system
"""
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def get_db_connection():
    """Get database connection using environment variables"""
    # Try Replit environment variables first
    if os.environ.get('DATABASE_URL'):
        return psycopg2.connect(os.environ['DATABASE_URL'])
    
    # Try individual PostgreSQL variables
    if all(os.environ.get(var) for var in ['PGHOST', 'PGUSER', 'PGPASSWORD', 'PGDATABASE']):
        return psycopg2.connect(
            host=os.environ['PGHOST'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            database=os.environ['PGDATABASE'],
            port=os.environ.get('PGPORT', 5432)
        )
    
    raise Exception("No database connection configuration found")

def create_tables():
    """Create all required database tables"""
    
    # SQL to create all tables
    sql_commands = [
        # Vault chunks table
        """
        CREATE TABLE IF NOT EXISTS vault_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source TEXT NOT NULL,
            chunk TEXT NOT NULL,
            summary TEXT,
            links JSONB DEFAULT '[]',
            embedding FLOAT[] DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        
        # Decisions table
        """
        CREATE TABLE IF NOT EXISTS decisions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            topic TEXT NOT NULL,
            options JSONB NOT NULL DEFAULT '[]',
            chosen TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'open',
            rationale TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        
        # Agent logs table
        """
        CREATE TABLE IF NOT EXISTS agent_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            agent TEXT NOT NULL,
            level VARCHAR(10) NOT NULL DEFAULT 'INFO',
            message TEXT NOT NULL,
            meta JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        
        # Indexes for performance
        """
        CREATE INDEX IF NOT EXISTS idx_vault_chunks_source ON vault_chunks(source);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_vault_chunks_created_at ON vault_chunks(created_at);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_decisions_status ON decisions(status);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_decisions_created_at ON decisions(created_at);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_agent_logs_agent ON agent_logs(agent);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_agent_logs_level ON agent_logs(level);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_agent_logs_created_at ON agent_logs(created_at);
        """
    ]
    
    try:
        conn = get_db_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("🗄️ Creating Angles OS™ database schema...")
        
        # Execute all commands
        for i, sql in enumerate(sql_commands, 1):
            try:
                cursor.execute(sql)
                print(f"✅ Step {i}/{len(sql_commands)}: SQL command executed successfully")
            except Exception as e:
                print(f"❌ Step {i}/{len(sql_commands)}: {e}")
                # Continue with other commands
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('vault_chunks', 'decisions', 'agent_logs')
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        print(f"\n📊 Created tables: {[table[0] for table in tables]}")
        
        cursor.close()
        conn.close()
        
        if len(tables) >= 3:
            print("🎉 Database migration completed successfully!")
            return True
        else:
            print("⚠️ Some tables may not have been created")
            return False
            
    except Exception as e:
        print(f"❌ Database migration failed: {e}")
        return False

def main():
    """Main entry point"""
    try:
        success = create_tables()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ POSTGRES_URL environment variable not set")
        exit(1)

if __name__ == "__main__":
    main()