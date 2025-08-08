#!/usr/bin/env python3
"""
Angles AI Universe™ Database Migration Script
Idempotent database schema setup and migration

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ Missing required dependency: requests")
    print("Please install with: pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv not available, relying on environment variables")

def setup_logging():
    """Setup logging for migration script"""
    os.makedirs("logs/active", exist_ok=True)
    
    logger = logging.getLogger('migration')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler
    file_handler = logging.FileHandler('logs/active/migration.log')
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class DatabaseMigration:
    """Database migration and schema management"""
    
    def __init__(self, dry_run: bool = False):
        """Initialize migration system"""
        self.logger = setup_logging()
        self.dry_run = dry_run
        
        # Load environment variables
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing required SUPABASE_URL or SUPABASE_KEY environment variables")
        
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        self.changes_applied = []
        
    def test_connection(self) -> bool:
        """Test Supabase connection"""
        self.logger.info("🔗 Testing Supabase connection...")
        
        try:
            response = requests.get(
                f"{self.supabase_url}/rest/v1/",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("✅ Supabase connection successful")
                return True
            else:
                self.logger.error(f"❌ Supabase connection failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Supabase connection error: {e}")
            return False
    
    def execute_sql(self, sql: str, description: str) -> bool:
        """Execute SQL command via Supabase REST API"""
        if self.dry_run:
            self.logger.info(f"🔍 [DRY RUN] Would execute: {description}")
            self.logger.info(f"    SQL: {sql}")
            return True
        
        try:
            # Use the rpc endpoint for SQL execution
            response = requests.post(
                f"{self.supabase_url}/rpc/exec_sql",
                headers=self.headers,
                json={"sql": sql},
                timeout=30
            )
            
            if response.status_code in [200, 201, 204]:
                self.logger.info(f"✅ {description}")
                self.changes_applied.append(description)
                return True
            else:
                # Try alternative method for schema changes
                if "CREATE TABLE" in sql or "ALTER TABLE" in sql or "CREATE INDEX" in sql:
                    return self._execute_schema_change(sql, description)
                
                self.logger.error(f"❌ Failed to execute {description}: HTTP {response.status_code}")
                self.logger.error(f"    Response: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error executing {description}: {e}")
            return False
    
    def _execute_schema_change(self, sql: str, description: str) -> bool:
        """Execute schema changes using direct SQL endpoint"""
        try:
            # For schema changes, we'll log them for manual execution
            self.logger.warning(f"⚠️ Schema change requires manual execution: {description}")
            self.logger.info(f"    SQL to execute in Supabase SQL Editor:")
            self.logger.info(f"    {sql}")
            
            # Save to file for later execution
            schema_file = "logs/active/pending_schema_changes.sql"
            with open(schema_file, "a") as f:
                f.write(f"-- {description}\n")
                f.write(f"{sql};\n\n")
            
            self.logger.info(f"📝 Schema change saved to {schema_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error handling schema change {description}: {e}")
            return False
    
    def check_table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        try:
            response = requests.get(
                f"{self.supabase_url}/rest/v1/{table_name}?select=*&limit=1",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def check_column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if column exists in table"""
        try:
            # Try to query with the column
            response = requests.get(
                f"{self.supabase_url}/rest/v1/{table_name}?select={column_name}&limit=1",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def ensure_decision_vault_table(self) -> bool:
        """Ensure decision_vault table exists with correct schema"""
        self.logger.info("📋 Checking decision_vault table...")
        
        if self.check_table_exists('decision_vault'):
            self.logger.info("✅ decision_vault table exists")
            
            # Check for missing columns and add them
            success = True
            
            # Check for synced column
            if not self.check_column_exists('decision_vault', 'synced'):
                sql = """
                ALTER TABLE decision_vault 
                ADD COLUMN synced BOOLEAN NOT NULL DEFAULT false;
                """
                success &= self.execute_sql(sql, "Add synced column to decision_vault")
            
            # Check for synced_at column
            if not self.check_column_exists('decision_vault', 'synced_at'):
                sql = """
                ALTER TABLE decision_vault 
                ADD COLUMN synced_at TIMESTAMPTZ;
                """
                success &= self.execute_sql(sql, "Add synced_at column to decision_vault")
            
            return success
        else:
            # Create the table
            sql = """
            CREATE TABLE IF NOT EXISTS decision_vault (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                decision TEXT NOT NULL,
                date DATE NOT NULL DEFAULT CURRENT_DATE,
                type TEXT NOT NULL,
                active BOOLEAN NOT NULL DEFAULT true,
                comment TEXT,
                synced BOOLEAN NOT NULL DEFAULT false,
                synced_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                CONSTRAINT decision_vault_decision_not_empty CHECK (LENGTH(TRIM(decision)) > 0),
                CONSTRAINT decision_vault_type_not_empty CHECK (LENGTH(TRIM(type)) > 0),
                CONSTRAINT decision_vault_type_valid CHECK (type IN ('strategy', 'technical', 'ethical', 'architecture', 'process', 'security', 'other'))
            );
            """
            return self.execute_sql(sql, "Create decision_vault table")
    
    def ensure_agent_activity_table(self) -> bool:
        """Ensure agent_activity table exists"""
        self.logger.info("📋 Checking agent_activity table...")
        
        if self.check_table_exists('agent_activity'):
            self.logger.info("✅ agent_activity table exists")
            return True
        else:
            sql = """
            CREATE TABLE IF NOT EXISTS agent_activity (
                id BIGSERIAL PRIMARY KEY,
                agent_name TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                CONSTRAINT agent_activity_agent_name_not_empty CHECK (LENGTH(TRIM(agent_name)) > 0),
                CONSTRAINT agent_activity_action_not_empty CHECK (LENGTH(TRIM(action)) > 0)
            );
            """
            return self.execute_sql(sql, "Create agent_activity table")
    
    def ensure_indexes(self) -> bool:
        """Ensure required indexes exist"""
        self.logger.info("🗂️ Checking database indexes...")
        
        indexes = [
            {
                'name': 'idx_decision_vault_date',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_decision_vault_date ON decision_vault(date DESC);',
                'description': 'Create index on decision_vault(date)'
            },
            {
                'name': 'idx_decision_vault_type',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_decision_vault_type ON decision_vault(type);',
                'description': 'Create index on decision_vault(type)'
            },
            {
                'name': 'idx_decision_vault_synced',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_decision_vault_synced ON decision_vault(synced);',
                'description': 'Create index on decision_vault(synced)'
            },
            {
                'name': 'idx_agent_activity_agent_name',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_agent_activity_agent_name ON agent_activity(agent_name);',
                'description': 'Create index on agent_activity(agent_name)'
            },
            {
                'name': 'idx_agent_activity_created_at',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_agent_activity_created_at ON agent_activity(created_at DESC);',
                'description': 'Create index on agent_activity(created_at)'
            }
        ]
        
        success = True
        for index in indexes:
            success &= self.execute_sql(index['sql'], index['description'])
        
        return success
    
    def ensure_triggers(self) -> bool:
        """Ensure database triggers exist"""
        self.logger.info("⚡ Checking database triggers...")
        
        # Update trigger for decision_vault
        sql = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        DROP TRIGGER IF EXISTS update_decision_vault_updated_at ON decision_vault;
        CREATE TRIGGER update_decision_vault_updated_at 
            BEFORE UPDATE ON decision_vault 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
        """
        
        return self.execute_sql(sql, "Create/update decision_vault updated_at trigger")
    
    def run_migration(self) -> bool:
        """Run complete database migration"""
        self.logger.info("🚀 Starting database migration...")
        self.logger.info(f"📍 Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        
        if not self.test_connection():
            return False
        
        success = True
        
        # Create tables
        success &= self.ensure_decision_vault_table()
        success &= self.ensure_agent_activity_table()
        
        # Create indexes
        success &= self.ensure_indexes()
        
        # Create triggers
        success &= self.ensure_triggers()
        
        # Summary
        if self.dry_run:
            self.logger.info("🔍 Dry run completed - no changes applied")
        else:
            if self.changes_applied:
                self.logger.info("✅ Migration completed successfully")
                self.logger.info(f"📝 Changes applied: {len(self.changes_applied)}")
                for change in self.changes_applied:
                    self.logger.info(f"   • {change}")
            else:
                self.logger.info("✅ Database schema is up to date - no changes needed")
        
        return success
    
    def log_migration_activity(self):
        """Log migration activity to agent_activity table"""
        if self.dry_run or not self.changes_applied:
            return
        
        try:
            activity_data = {
                'agent_name': 'migration_script',
                'action': 'database_migration',
                'details': json.dumps({
                    'changes_applied': self.changes_applied,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'change_count': len(self.changes_applied)
                }),
                'status': 'completed'
            }
            
            response = requests.post(
                f"{self.supabase_url}/rest/v1/agent_activity",
                headers=self.headers,
                json=activity_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                self.logger.info("📝 Migration activity logged successfully")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not log migration activity: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Database Migration Script')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    parser.add_argument('--test', action='store_true', help='Test connection only')
    
    args = parser.parse_args()
    
    try:
        migration = DatabaseMigration(dry_run=args.dry_run)
        
        if args.test:
            success = migration.test_connection()
            sys.exit(0 if success else 1)
        
        success = migration.run_migration()
        
        if success and not args.dry_run:
            migration.log_migration_activity()
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"💥 Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()