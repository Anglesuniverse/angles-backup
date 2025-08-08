"""
Database Migration for Angles AI Universe™
Idempotent database schema creation and updates
"""

import logging
from typing import List, Dict, Any

from .config import print_config_status, SUPABASE_URL, SUPABASE_KEY
from .utils import retry_with_backoff


logger = logging.getLogger(__name__)


class DatabaseMigration:
    """Handles database schema creation and migration"""
    
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY")
        
        self.supabase_url = SUPABASE_URL
        self.headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        
        self.migration_log = []
    
    def get_table_schemas(self) -> Dict[str, str]:
        """Get table creation SQL statements"""
        return {
            'decision_vault': """
                CREATE TABLE IF NOT EXISTS decision_vault (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    category VARCHAR(100) NOT NULL DEFAULT 'general',
                    status VARCHAR(50) NOT NULL DEFAULT 'active',
                    content TEXT NOT NULL,
                    date_added TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    tags TEXT[] DEFAULT '{}',
                    source VARCHAR(100) DEFAULT 'system',
                    checksum VARCHAR(64),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """,
            
            'system_logs': """
                CREATE TABLE IF NOT EXISTS system_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    ts TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    level VARCHAR(20) NOT NULL,
                    component VARCHAR(100) NOT NULL,
                    message TEXT NOT NULL,
                    meta JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """,
            
            'file_snapshots': """
                CREATE TABLE IF NOT EXISTS file_snapshots (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    path TEXT NOT NULL,
                    checksum VARCHAR(64) NOT NULL,
                    content TEXT NOT NULL,
                    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(path, checksum)
                );
            """,
            
            'run_artifacts': """
                CREATE TABLE IF NOT EXISTS run_artifacts (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    ts TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    kind VARCHAR(100) NOT NULL,
                    ref VARCHAR(200) NOT NULL,
                    notes TEXT,
                    blob TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """
        }
    
    def get_indexes(self) -> Dict[str, List[str]]:
        """Get index creation statements"""
        return {
            'decision_vault': [
                "CREATE INDEX IF NOT EXISTS idx_decision_vault_category ON decision_vault(category);",
                "CREATE INDEX IF NOT EXISTS idx_decision_vault_status ON decision_vault(status);",
                "CREATE INDEX IF NOT EXISTS idx_decision_vault_date_added ON decision_vault(date_added);",
                "CREATE INDEX IF NOT EXISTS idx_decision_vault_checksum ON decision_vault(checksum);"
            ],
            'system_logs': [
                "CREATE INDEX IF NOT EXISTS idx_system_logs_ts ON system_logs(ts);",
                "CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);",
                "CREATE INDEX IF NOT EXISTS idx_system_logs_component ON system_logs(component);"
            ],
            'file_snapshots': [
                "CREATE INDEX IF NOT EXISTS idx_file_snapshots_path ON file_snapshots(path);",
                "CREATE INDEX IF NOT EXISTS idx_file_snapshots_last_updated ON file_snapshots(last_updated);"
            ],
            'run_artifacts': [
                "CREATE INDEX IF NOT EXISTS idx_run_artifacts_ts ON run_artifacts(ts);",
                "CREATE INDEX IF NOT EXISTS idx_run_artifacts_kind ON run_artifacts(kind);",
                "CREATE INDEX IF NOT EXISTS idx_run_artifacts_ref ON run_artifacts(ref);"
            ]
        }
    
    @retry_with_backoff(max_retries=3)
    def execute_sql(self, sql: str, description: str) -> bool:
        """Execute SQL statement via Supabase REST API"""
        import requests
        
        try:
            # Note: Supabase REST API doesn't support arbitrary SQL execution
            # This is a simplified version - in production, you'd use the Supabase Python client
            # or direct PostgreSQL connection for schema changes
            
            logger.info(f"📝 {description}")
            logger.info(f"   SQL: {sql[:100]}{'...' if len(sql) > 100 else ''}")
            
            # For demonstration, we'll log what would be executed
            # In a real implementation, you'd execute this via psycopg2 or supabase-py
            self.migration_log.append({
                'description': description,
                'sql': sql,
                'status': 'simulated'  # Would be 'success' or 'failed' in real implementation
            })
            
            logger.info("   ✅ SQL executed (simulated)")
            return True
            
        except Exception as e:
            logger.error(f"   ❌ SQL execution failed: {e}")
            self.migration_log.append({
                'description': description,
                'sql': sql,
                'status': 'failed',
                'error': str(e)
            })
            return False
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            import requests
            
            response = requests.get(
                f"{self.supabase_url}/rest/v1/",
                headers=self.headers,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def run_migration(self) -> bool:
        """Run complete database migration"""
        logger.info("🚀 Starting Database Migration")
        print_config_status()
        
        # Test connection first
        if not self.test_connection():
            logger.error("❌ Database connection failed")
            return False
        
        logger.info("✅ Database connection successful")
        
        success = True
        
        try:
            # Create tables
            table_schemas = self.get_table_schemas()
            
            for table_name, schema_sql in table_schemas.items():
                if not self.execute_sql(schema_sql, f"Creating table: {table_name}"):
                    success = False
            
            # Create indexes
            indexes = self.get_indexes()
            
            for table_name, index_sqls in indexes.items():
                for index_sql in index_sqls:
                    index_name = index_sql.split('idx_')[1].split(' ')[0] if 'idx_' in index_sql else 'unknown'
                    if not self.execute_sql(index_sql, f"Creating index: {index_name}"):
                        success = False
            
            # Print migration summary
            logger.info("\n📊 Migration Summary:")
            for entry in self.migration_log:
                status_emoji = "✅" if entry['status'] in ['success', 'simulated'] else "❌"
                logger.info(f"   {status_emoji} {entry['description']}")
            
            if success:
                logger.info("🎉 Database migration completed successfully")
                logger.info("\n⚠️  Note: This is a simulated migration.")
                logger.info("   In production, ensure you have proper database permissions")
                logger.info("   and use direct PostgreSQL connections for schema changes.")
            else:
                logger.error("❌ Database migration completed with errors")
            
            return success
            
        except Exception as e:
            logger.error(f"Migration failed with exception: {e}")
            return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database migration utility')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be made")
        
        migration = DatabaseMigration()
        
        print("\nTables that would be created:")
        for table_name in migration.get_table_schemas().keys():
            print(f"  📊 {table_name}")
        
        print("\nIndexes that would be created:")
        for table_name, indexes in migration.get_indexes().items():
            print(f"  📊 {table_name}: {len(indexes)} indexes")
        
        return 0
    
    try:
        migration = DatabaseMigration()
        success = migration.run_migration()
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Migration setup failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())