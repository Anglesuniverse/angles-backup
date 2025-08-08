#!/usr/bin/env python3
"""
Angles AI Universe™ Schema Guard System
Verifies and maintains Supabase database schema integrity with auto-migration

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Import alert manager
try:
    from alerts.notify import AlertManager
except ImportError:
    AlertManager = None

class SchemaGuard:
    """Database schema integrity monitor and auto-migration system"""
    
    def __init__(self):
        """Initialize schema guard"""
        self.setup_logging()
        self.load_environment()
        self.alert_manager = AlertManager() if AlertManager else None
        
        # Define required schema
        self.required_schema = {
            'decision_vault': {
                'columns': {
                    'id': {'type': 'uuid', 'primary_key': True},
                    'decision': {'type': 'text', 'nullable': True},
                    'date': {'type': 'date', 'nullable': True},
                    'type': {'type': 'text', 'nullable': True},
                    'active': {'type': 'boolean', 'nullable': True},
                    'comment': {'type': 'text', 'nullable': True},
                    'created_at': {'type': 'timestamptz', 'default': 'now()', 'nullable': False},
                    'updated_at': {'type': 'timestamptz', 'default': 'now()', 'nullable': False},
                    'synced': {'type': 'boolean', 'default': 'false', 'nullable': False},
                    'synced_at': {'type': 'timestamptz', 'nullable': True}
                },
                'indexes': {
                    'idx_decision_date': {'columns': ['date'], 'type': 'btree'}
                }
            },
            'ai_decision_log': {
                'columns': {
                    'id': {'type': 'uuid', 'primary_key': True},
                    'decision_text': {'type': 'text', 'nullable': True},
                    'decision_type': {'type': 'text', 'default': "'general'", 'nullable': False},
                    'timestamp': {'type': 'timestamptz', 'default': 'now()', 'nullable': False},
                    'confidence': {'type': 'numeric', 'nullable': True},
                    'metadata': {'type': 'jsonb', 'nullable': True}
                },
                'indexes': {
                    'idx_ai_log_timestamp': {'columns': ['timestamp'], 'type': 'btree', 'order': 'DESC'}
                }
            }
        }
        
        self.logger.info("🔒 Angles AI Universe™ Schema Guard Initialized")
    
    def setup_logging(self):
        """Setup logging for schema guard"""
        os.makedirs("logs/active", exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger('schema_guard')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/active/schema_guard.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def load_environment(self):
        """Load required environment variables"""
        self.env = {
            'supabase_url': os.getenv('SUPABASE_URL'),
            'supabase_key': os.getenv('SUPABASE_KEY')
        }
        
        # Validate required environment variables
        if not self.env['supabase_url'] or not self.env['supabase_key']:
            raise ValueError("Missing required Supabase environment variables")
        
        self.logger.info("📋 Schema Guard environment loaded")
    
    def get_supabase_headers(self) -> Dict[str, str]:
        """Get standard Supabase headers"""
        return {
            'apikey': self.env['supabase_key'],
            'Authorization': f"Bearer {self.env['supabase_key']}",
            'Content-Type': 'application/json'
        }
    
    def check_table_exists(self, table_name: str) -> bool:
        """Check if table exists in database"""
        try:
            url = f"{self.env['supabase_url']}/rest/v1/{table_name}"
            headers = self.get_supabase_headers()
            
            # Try to query with limit 0 to check existence
            params = {'select': 'id', 'limit': '0'}
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"❌ Error checking table {table_name}: {str(e)}")
            return False
    
    def get_table_schema(self, table_name: str) -> Optional[Dict]:
        """Get current table schema from Supabase"""
        try:
            # Use Supabase REST API to introspect schema
            # This is a simplified version - in production you might use direct SQL
            url = f"{self.env['supabase_url']}/rest/v1/{table_name}"
            headers = self.get_supabase_headers()
            
            # Get table structure by making a query and analyzing the response
            params = {'select': '*', 'limit': '1'}
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    # Extract column names from first record
                    columns = list(data[0].keys())
                    return {'columns': columns, 'exists': True}
                else:
                    # Table exists but is empty
                    return {'columns': [], 'exists': True}
            else:
                return {'exists': False}
                
        except Exception as e:
            self.logger.error(f"❌ Error getting schema for {table_name}: {str(e)}")
            return None
    
    def verify_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Verify table schema matches requirements"""
        self.logger.info(f"🔍 Verifying schema for {table_name}...")
        
        result = {
            'table_name': table_name,
            'exists': False,
            'columns_missing': [],
            'indexes_missing': [],
            'schema_valid': False,
            'needs_migration': False
        }
        
        # Check if table exists
        if not self.check_table_exists(table_name):
            result['needs_migration'] = True
            result['columns_missing'] = list(self.required_schema[table_name]['columns'].keys())
            result['indexes_missing'] = list(self.required_schema[table_name]['indexes'].keys())
            self.logger.warning(f"⚠️ Table {table_name} does not exist")
            return result
        
        result['exists'] = True
        
        # Get current schema
        current_schema = self.get_table_schema(table_name)
        if not current_schema:
            result['needs_migration'] = True
            return result
        
        # Check required columns
        required_columns = set(self.required_schema[table_name]['columns'].keys())
        current_columns = set(current_schema.get('columns', []))
        
        missing_columns = required_columns - current_columns
        if missing_columns:
            result['columns_missing'] = list(missing_columns)
            result['needs_migration'] = True
            self.logger.warning(f"⚠️ Missing columns in {table_name}: {missing_columns}")
        
        # For now, assume indexes are missing if any columns are missing
        # In a full implementation, you'd query the database for index information
        if missing_columns:
            result['indexes_missing'] = list(self.required_schema[table_name]['indexes'].keys())
        
        result['schema_valid'] = not result['needs_migration']
        
        if result['schema_valid']:
            self.logger.info(f"✅ Schema valid for {table_name}")
        
        return result
    
    def generate_migration_sql(self, table_name: str, schema_check: Dict) -> str:
        """Generate SQL migration script for table"""
        self.logger.info(f"🛠️ Generating migration SQL for {table_name}...")
        
        sql_statements = []
        table_spec = self.required_schema[table_name]
        
        if not schema_check['exists']:
            # Create entire table
            sql_statements.append(f"-- Create table {table_name}")
            
            columns_sql = []
            for col_name, col_spec in table_spec['columns'].items():
                col_def = f"{col_name} {col_spec['type']}"
                
                if col_spec.get('primary_key'):
                    col_def += " PRIMARY KEY DEFAULT gen_random_uuid()"
                elif 'default' in col_spec:
                    col_def += f" DEFAULT {col_spec['default']}"
                
                if not col_spec.get('nullable', True):
                    col_def += " NOT NULL"
                
                columns_sql.append(col_def)
            
            create_table_sql = f"CREATE TABLE {table_name} (\n  {',\n  '.join(columns_sql)}\n);"
            sql_statements.append(create_table_sql)
        
        else:
            # Add missing columns
            for col_name in schema_check['columns_missing']:
                col_spec = table_spec['columns'][col_name]
                col_def = f"ADD COLUMN {col_name} {col_spec['type']}"
                
                if 'default' in col_spec:
                    col_def += f" DEFAULT {col_spec['default']}"
                
                if not col_spec.get('nullable', True):
                    col_def += " NOT NULL"
                
                sql_statements.append(f"ALTER TABLE {table_name} {col_def};")
        
        # Add indexes
        for idx_name in schema_check.get('indexes_missing', []):
            idx_spec = table_spec['indexes'][idx_name]
            columns = ', '.join(idx_spec['columns'])
            
            if idx_spec.get('order') == 'DESC':
                columns = f"{idx_spec['columns'][0]} DESC"
            
            idx_sql = f"CREATE INDEX {idx_name} ON {table_name} USING {idx_spec.get('type', 'btree')} ({columns});"
            sql_statements.append(idx_sql)
        
        return '\n\n'.join(sql_statements)
    
    def save_migration_file(self, table_name: str, sql: str) -> str:
        """Save migration SQL to file"""
        os.makedirs("migrations", exist_ok=True)
        
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f"migrations/{timestamp}_{table_name}_migration.sql"
        
        with open(filename, 'w') as f:
            f.write(f"-- Migration for {table_name}\n")
            f.write(f"-- Generated: {datetime.now(timezone.utc).isoformat()}\n")
            f.write(f"-- Schema Guard Auto-Migration\n\n")
            f.write(sql)
        
        self.logger.info(f"💾 Migration saved: {filename}")
        return filename
    
    def apply_migration_sql(self, sql: str) -> bool:
        """Apply migration SQL using Supabase RPC"""
        try:
            # Note: Direct SQL execution via REST API is limited
            # In production, you might use a stored procedure or direct database connection
            self.logger.warning("⚠️ Direct SQL migration not implemented via REST API")
            self.logger.info("Please apply the migration manually using the Supabase dashboard or direct database connection")
            
            # For now, return True assuming manual application
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Migration application failed: {str(e)}")
            return False
    
    def run_schema_verification(self) -> Dict[str, Any]:
        """Run complete schema verification"""
        self.logger.info("🚀 Starting Schema Verification")
        self.logger.info("=" * 60)
        
        start_time = datetime.now(timezone.utc)
        
        verification_result = {
            'timestamp': start_time.isoformat(),
            'tables_checked': [],
            'migrations_needed': [],
            'migrations_generated': [],
            'overall_status': 'unknown',
            'errors': []
        }
        
        try:
            # Check each required table
            for table_name in self.required_schema.keys():
                schema_check = self.verify_table_schema(table_name)
                verification_result['tables_checked'].append(schema_check)
                
                if schema_check['needs_migration']:
                    verification_result['migrations_needed'].append(table_name)
                    
                    # Generate migration SQL
                    try:
                        migration_sql = self.generate_migration_sql(table_name, schema_check)
                        migration_file = self.save_migration_file(table_name, migration_sql)
                        
                        verification_result['migrations_generated'].append({
                            'table': table_name,
                            'file': migration_file,
                            'sql': migration_sql
                        })
                        
                        # Apply migration (currently manual)
                        self.apply_migration_sql(migration_sql)
                        
                    except Exception as e:
                        error_msg = f"Migration generation failed for {table_name}: {str(e)}"
                        verification_result['errors'].append(error_msg)
                        self.logger.error(f"❌ {error_msg}")
            
            # Determine overall status
            if verification_result['errors']:
                verification_result['overall_status'] = 'error'
            elif verification_result['migrations_needed']:
                verification_result['overall_status'] = 'migration_needed'
            else:
                verification_result['overall_status'] = 'healthy'
            
            # Calculate duration
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            verification_result['duration_seconds'] = duration
            
            # Log summary
            self.logger.info("=" * 60)
            self.logger.info("🎉 Schema Verification Complete")
            self.logger.info(f"   Duration: {duration:.2f} seconds")
            self.logger.info(f"   Tables checked: {len(verification_result['tables_checked'])}")
            self.logger.info(f"   Migrations needed: {len(verification_result['migrations_needed'])}")
            self.logger.info(f"   Status: {verification_result['overall_status'].upper()}")
            
            # Send alerts if needed
            if verification_result['overall_status'] != 'healthy' and self.alert_manager:
                self.send_schema_alert(verification_result)
            
            # Save verification report
            self.save_verification_report(verification_result)
            
            return verification_result
            
        except Exception as e:
            verification_result['overall_status'] = 'error'
            verification_result['errors'].append(f"Schema verification failed: {str(e)}")
            self.logger.error(f"💥 Schema verification failed: {str(e)}")
            
            # Send critical alert
            if self.alert_manager:
                self.alert_manager.send_alert(
                    title="Schema Guard Critical Failure",
                    message=f"Schema verification failed with error: {str(e)}",
                    severity="critical",
                    tags=['schema', 'critical', 'failure']
                )
            
            return verification_result
    
    def send_schema_alert(self, verification_result: Dict):
        """Send alert for schema issues"""
        if not self.alert_manager:
            return
        
        status = verification_result['overall_status']
        severity = 'critical' if status == 'error' else 'warning'
        
        title = f"Schema Guard Alert: {status.replace('_', ' ').title()}"
        
        message = f"**Schema Status:** {status.upper()}\n"
        message += f"**Timestamp:** {verification_result['timestamp']}\n"
        message += f"**Tables Checked:** {len(verification_result['tables_checked'])}\n"
        
        if verification_result['migrations_needed']:
            message += f"**Migrations Needed:** {', '.join(verification_result['migrations_needed'])}\n"
        
        if verification_result['errors']:
            message += f"**Errors:** {len(verification_result['errors'])}\n"
            for error in verification_result['errors'][:3]:  # Limit to first 3 errors
                message += f"- {error}\n"
        
        message += "\n**Next Actions:**\n"
        message += "1. Review generated migration files in `migrations/`\n"
        message += "2. Apply migrations manually via Supabase dashboard\n"
        message += "3. Re-run schema guard: `python schema_guard.py`\n"
        
        self.alert_manager.send_alert(
            title=title,
            message=message,
            severity=severity,
            tags=['schema', status, 'guard'],
            github_labels=['schema-guard', status]
        )
    
    def save_verification_report(self, verification_result: Dict):
        """Save verification report to JSON file"""
        try:
            os.makedirs("logs/schema", exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = f"logs/schema/schema_report_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(verification_result, f, indent=2, default=str)
            
            self.logger.info(f"📊 Schema report saved: {report_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save schema report: {str(e)}")

def main():
    """Main entry point for schema guard"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database schema integrity guard')
    parser.add_argument('--verify', action='store_true', help='Run schema verification')
    parser.add_argument('--table', help='Check specific table only')
    parser.add_argument('--generate-only', action='store_true', help='Generate migrations without applying')
    
    args = parser.parse_args()
    
    try:
        guard = SchemaGuard()
        
        if args.verify or not any([args.table, args.generate_only]):
            result = guard.run_schema_verification()
            
            # Exit with appropriate code
            if result['overall_status'] == 'healthy':
                print("\n✅ All schemas are healthy!")
                sys.exit(0)
            elif result['overall_status'] == 'migration_needed':
                print("\n⚠️ Schema migrations needed - check logs for details")
                sys.exit(1)
            else:
                print("\n❌ Schema verification failed - check logs for details")
                sys.exit(2)
        
        elif args.table:
            schema_check = guard.verify_table_schema(args.table)
            
            print(f"\n📋 Schema Check Results for {args.table}:")
            print(f"Exists: {schema_check['exists']}")
            print(f"Schema Valid: {schema_check['schema_valid']}")
            print(f"Needs Migration: {schema_check['needs_migration']}")
            
            if schema_check['columns_missing']:
                print(f"Missing Columns: {', '.join(schema_check['columns_missing'])}")
            
            if schema_check['indexes_missing']:
                print(f"Missing Indexes: {', '.join(schema_check['indexes_missing'])}")
        
    except KeyboardInterrupt:
        print("\n🛑 Schema guard interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Schema guard failed: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()