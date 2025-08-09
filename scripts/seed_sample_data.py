#!/usr/bin/env python3
"""
Angles OS™ Sample Data Seeder
Adds sample data for testing and demonstration
"""
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import json

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

def seed_sample_data():
    """Insert sample data into tables"""
    
    # Sample data
    sample_vault_chunks = [
        {
            'source': 'angles_os_docs',
            'chunk': 'Angles OS™ is a production-ready FastAPI backend with PostgreSQL, Redis, TokenVault memory system, AI-powered decision management, and automated agents.',
            'summary': 'Overview of Angles OS™ system capabilities',
            'links': ['https://github.com/angles-os']
        },
        {
            'source': 'system_architecture', 
            'chunk': 'The system employs a dual backend architecture with automated agents for memory sync, strategy management, and system verification.',
            'summary': 'System architecture description',
            'links': []
        },
        {
            'source': 'api_documentation',
            'chunk': 'FastAPI provides automatic OpenAPI documentation at /docs endpoint with interactive testing capabilities.',
            'summary': 'API documentation features',
            'links': ['http://localhost:8000/docs']
        }
    ]
    
    sample_decisions = [
        {
            'topic': 'Choose FastAPI framework for API development',
            'options': [
                {
                    'option': 'FastAPI',
                    'pros': ['Modern async support', 'Automatic docs', 'Type validation'],
                    'cons': ['Newer framework', 'Learning curve']
                },
                {
                    'option': 'Flask',
                    'pros': ['Simple', 'Mature', 'Large ecosystem'],
                    'cons': ['No async by default', 'Manual validation']
                }
            ],
            'chosen': 'FastAPI',
            'status': 'approved',
            'rationale': 'FastAPI provides superior async support and automatic documentation generation'
        },
        {
            'topic': 'Database choice for primary storage',
            'options': [
                {
                    'option': 'PostgreSQL', 
                    'pros': ['ACID compliance', 'JSON support', 'Mature'],
                    'cons': ['More complex setup']
                },
                {
                    'option': 'SQLite',
                    'pros': ['Simple setup', 'File-based'],
                    'cons': ['No concurrent writes', 'Limited scaling']
                }
            ],
            'chosen': 'PostgreSQL',
            'status': 'approved', 
            'rationale': 'PostgreSQL offers better concurrency and JSON support for complex data'
        }
    ]
    
    try:
        conn = get_db_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("🌱 Seeding Angles OS™ sample data...")
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM vault_chunks")
        vault_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM decisions")
        decision_count = cursor.fetchone()[0]
        
        if vault_count > 0 or decision_count > 0:
            print("⚠️ Sample data already exists, skipping seeding")
            return True
        
        # Insert vault chunks
        for chunk_data in sample_vault_chunks:
            cursor.execute("""
                INSERT INTO vault_chunks (source, chunk, summary, links)
                VALUES (%s, %s, %s, %s)
            """, (
                chunk_data['source'],
                chunk_data['chunk'], 
                chunk_data['summary'],
                chunk_data['links']
            ))
        
        print(f"✅ Inserted {len(sample_vault_chunks)} vault chunks")
        
        # Insert decisions
        for decision_data in sample_decisions:
            cursor.execute("""
                INSERT INTO decisions (topic, options, chosen, status, rationale)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                decision_data['topic'],
                json.dumps(decision_data['options']),
                decision_data['chosen'],
                decision_data['status'],
                decision_data['rationale']
            ))
        
        print(f"✅ Inserted {len(sample_decisions)} decisions")
        
        # Insert sample agent log
        cursor.execute("""
            INSERT INTO agent_logs (agent, level, message, meta)
            VALUES (%s, %s, %s, %s)
        """, (
            'seeder',
            'INFO', 
            'Sample data seeding completed',
            json.dumps({'chunks_added': len(sample_vault_chunks), 'decisions_added': len(sample_decisions)})
        ))
        
        print("✅ Inserted sample agent log")
        
        cursor.close()
        conn.close()
        
        print("🎉 Sample data seeding completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Sample data seeding failed: {e}")
        return False

def main():
    """Main entry point"""
    try:
        success = seed_sample_data()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()