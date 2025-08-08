#!/usr/bin/env python3
"""
Angles AI Universe™ Schema Guard
===============================
Validates and auto-fixes database schema mismatches between expected and actual structure.
Ensures Supabase tables align with application requirements without breaking existing data.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from supabase import create_client, Client
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Expected schema definition
EXPECTED_SCHEMA = {
    "decision_vault": {
        "columns": {
            "id": {"type": "uuid", "nullable": False, "default": "gen_random_uuid()", "primary_key": True},
            "category": {"type": "text", "nullable": True},
            "status": {"type": "text", "nullable": True}, 
            "content": {"type": "text", "nullable": True},
            "date_added": {"type": "timestamptz", "nullable": False, "default": "now()"},
            "last_updated": {"type": "timestamptz", "nullable": False, "default": "now()"},
            "tags": {"type": "text[]", "nullable": True},
            "notion_page_id": {"type": "text", "nullable": True},
            "notion_synced": {"type": "boolean", "nullable": False, "default": "false"},
            "synced_at": {"type": "timestamptz", "nullable": True}
        },
        "indexes": [
            {"name": "idx_decision_date", "columns": ["date_added"]},
            {"name": "idx_decision_category", "columns": ["category"]},
            {"name": "idx_decision_status", "columns": ["status"]}
        ]
    },
    "system_logs": {
        "columns": {
            "id": {"type": "uuid", "nullable": False, "default": "gen_random_uuid()", "primary_key": True},
            "level": {"type": "text", "nullable": True},
            "message": {"type": "text", "nullable": True},
            "ts": {"type": "timestamptz", "nullable": False, "default": "now()"}
        },
        "indexes": [
            {"name": "idx_logs_timestamp", "columns": ["ts"]},
            {"name": "idx_logs_level", "columns": ["level"]}
        ]
    },
    "file_snapshots": {
        "columns": {
            "id": {"type": "uuid", "nullable": False, "default": "gen_random_uuid()", "primary_key": True},
            "file_path": {"type": "text", "nullable": True},
            "content": {"type": "text", "nullable": True},
            "ts": {"type": "timestamptz", "nullable": False, "default": "now()"}
        },
        "indexes": [
            {"name": "idx_snapshots_path", "columns": ["file_path"]},
            {"name": "idx_snapshots_timestamp", "columns": ["ts"]}
        ]
    },
    "run_artifacts": {
        "columns": {
            "id": {"type": "uuid", "nullable": False, "default": "gen_random_uuid()", "primary_key": True},
            "artifact_name": {"type": "text", "nullable": True},
            "artifact_type": {"type": "text", "nullable": True},
            "ts": {"type": "timestamptz", "nullable": False, "default": "now()"}
        },
        "indexes": [
            {"name": "idx_artifacts_name", "columns": ["artifact_name"]},
            {"name": "idx_artifacts_type", "columns": ["artifact_type"]}
        ]
    }
}

class SchemaGuard:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY") 
        self.database_url = os.getenv("DATABASE_URL")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing required environment variables: SUPABASE_URL, SUPABASE_KEY")
            
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
    def get_actual_schema(self) -> Dict:
        """Get actual database schema from Supabase."""
        actual_schema = {}
        
        try:
            # Get table and column information
            query = """
            SELECT 
                t.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                tc.constraint_type
            FROM information_schema.tables t
            LEFT JOIN information_schema.columns c ON t.table_name = c.table_name
            LEFT JOIN information_schema.table_constraints tc ON t.table_name = tc.table_name
            LEFT JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
                AND c.column_name = ccu.column_name
            WHERE t.table_schema = 'public' 
                AND t.table_name IN ('decision_vault', 'system_logs', 'file_snapshots', 'run_artifacts')
            ORDER BY t.table_name, c.ordinal_position;
            """
            
            # Execute via direct SQL since Supabase client doesn't support schema queries
            import psycopg2
            conn = psycopg2.connect(self.database_url)
            cur = conn.cursor()
            cur.execute(query)
            rows = cur.fetchall()
            
            # Process results
            for row in rows:
                table_name, col_name, data_type, is_nullable, col_default, constraint_type = row
                
                if table_name not in actual_schema:
                    actual_schema[table_name] = {"columns": {}, "indexes": []}
                
                if col_name:  # Skip rows without column info
                    actual_schema[table_name]["columns"][col_name] = {
                        "type": data_type,
                        "nullable": is_nullable == "YES",
                        "default": col_default,
                        "primary_key": constraint_type == "PRIMARY KEY"
                    }
            
            # Get index information
            index_query = """
            SELECT 
                schemaname, tablename, indexname, indexdef
            FROM pg_indexes 
            WHERE schemaname = 'public' 
                AND tablename IN ('decision_vault', 'system_logs', 'file_snapshots', 'run_artifacts')
                AND indexname NOT LIKE '%_pkey';
            """
            
            cur.execute(index_query)
            index_rows = cur.fetchall()
            
            for row in index_rows:
                schema_name, table_name, index_name, index_def = row
                if table_name in actual_schema:
                    actual_schema[table_name]["indexes"].append({
                        "name": index_name,
                        "definition": index_def
                    })
            
            cur.close()
            conn.close()
            
        except Exception as e:
            print(f"⚠️  Error getting actual schema: {e}")
            return {}
            
        return actual_schema
    
    def compare_schemas(self, expected: Dict, actual: Dict) -> Dict:
        """Compare expected vs actual schema and return differences."""
        differences = {
            "missing_tables": [],
            "missing_columns": {},
            "type_mismatches": {},
            "missing_indexes": {}
        }
        
        for table_name, expected_table in expected.items():
            if table_name not in actual:
                differences["missing_tables"].append(table_name)
                continue
                
            actual_table = actual[table_name]
            
            # Check columns
            missing_cols = []
            type_mismatches = []
            
            for col_name, expected_col in expected_table["columns"].items():
                if col_name not in actual_table["columns"]:
                    missing_cols.append({
                        "column": col_name,
                        "expected": expected_col
                    })
                else:
                    actual_col = actual_table["columns"][col_name]
                    # Type mapping for common PostgreSQL types
                    type_map = {
                        "uuid": ["uuid"],
                        "text": ["text", "character varying"],
                        "timestamptz": ["timestamp with time zone", "timestamptz"],
                        "text[]": ["ARRAY", "text[]"],
                        "boolean": ["boolean"]
                    }
                    
                    expected_types = type_map.get(expected_col["type"], [expected_col["type"]])
                    if actual_col["type"] not in expected_types:
                        type_mismatches.append({
                            "column": col_name,
                            "expected": expected_col["type"],
                            "actual": actual_col["type"]
                        })
            
            if missing_cols:
                differences["missing_columns"][table_name] = missing_cols
            if type_mismatches:
                differences["type_mismatches"][table_name] = type_mismatches
                
            # Check indexes
            actual_index_names = [idx["name"] for idx in actual_table.get("indexes", [])]
            missing_indexes = []
            
            for expected_idx in expected_table.get("indexes", []):
                if expected_idx["name"] not in actual_index_names:
                    missing_indexes.append(expected_idx)
                    
            if missing_indexes:
                differences["missing_indexes"][table_name] = missing_indexes
        
        return differences
    
    def print_schema_report(self, differences: Dict) -> bool:
        """Print schema comparison report. Returns True if differences found."""
        has_differences = any([
            differences["missing_tables"],
            differences["missing_columns"], 
            differences["type_mismatches"],
            differences["missing_indexes"]
        ])
        
        print("🔍 SCHEMA GUARD REPORT")
        print("=" * 50)
        
        if not has_differences:
            print("✅ Schema validation PASSED - all tables and columns match expected structure")
            return False
            
        print("⚠️  Schema validation FAILED - differences detected:")
        print()
        
        if differences["missing_tables"]:
            print("❌ Missing Tables:")
            for table in differences["missing_tables"]:
                print(f"   - {table}")
            print()
        
        if differences["missing_columns"]:
            print("⚠️  Missing Columns:")
            for table, columns in differences["missing_columns"].items():
                print(f"   {table}:")
                for col in columns:
                    print(f"     - {col['column']} ({col['expected']['type']})")
            print()
                    
        if differences["type_mismatches"]:
            print("🔄 Type Mismatches:")
            for table, mismatches in differences["type_mismatches"].items():
                print(f"   {table}:")
                for mismatch in mismatches:
                    print(f"     - {mismatch['column']}: expected {mismatch['expected']}, got {mismatch['actual']}")
            print()
                    
        if differences["missing_indexes"]:
            print("📊 Missing Indexes:")
            for table, indexes in differences["missing_indexes"].items():
                print(f"   {table}:")
                for idx in indexes:
                    print(f"     - {idx['name']} on {idx['columns']}")
            print()
        
        return True
    
    def auto_fix_schema(self, differences: Dict) -> bool:
        """Auto-fix safe schema differences. Returns True if fixes applied."""
        fixes_applied = False
        
        try:
            conn = psycopg2.connect(self.database_url)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            
            print("🔧 APPLYING AUTO-FIXES")
            print("=" * 30)
            
            # Fix missing columns (safe)
            for table_name, missing_cols in differences.get("missing_columns", {}).items():
                for col_info in missing_cols:
                    col_name = col_info["column"]
                    col_spec = col_info["expected"]
                    
                    # Build ALTER TABLE statement
                    sql_type = col_spec["type"]
                    nullable = "NULL" if col_spec.get("nullable", True) else "NOT NULL"
                    default = f"DEFAULT {col_spec['default']}" if col_spec.get("default") else ""
                    
                    alter_sql = f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col_name} {sql_type} {nullable} {default};"
                    
                    try:
                        cur.execute(alter_sql)
                        print(f"✅ Added column {table_name}.{col_name}")
                        fixes_applied = True
                    except Exception as e:
                        print(f"❌ Failed to add {table_name}.{col_name}: {e}")
            
            # Add missing indexes (safe)
            for table_name, missing_indexes in differences.get("missing_indexes", {}).items():
                for idx_info in missing_indexes:
                    idx_name = idx_info["name"]
                    idx_columns = ", ".join(idx_info["columns"])
                    
                    create_sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({idx_columns});"
                    
                    try:
                        cur.execute(create_sql)
                        print(f"✅ Created index {idx_name} on {table_name}")
                        fixes_applied = True
                    except Exception as e:
                        print(f"❌ Failed to create index {idx_name}: {e}")
            
            # Type mismatches - print warnings only (unsafe to auto-fix)
            if differences.get("type_mismatches"):
                print("\n⚠️  TYPE MISMATCHES (Manual review required):")
                for table, mismatches in differences["type_mismatches"].items():
                    for mismatch in mismatches:
                        print(f"   {table}.{mismatch['column']}: {mismatch['expected']} vs {mismatch['actual']}")
                print("   → These require manual review to avoid data loss")
            
            cur.close()
            conn.close()
            
        except Exception as e:
            print(f"❌ Auto-fix failed: {e}")
            return False
            
        if fixes_applied:
            print(f"\n✅ Auto-fix completed successfully")
        else:
            print("\n💡 No safe auto-fixes available")
            
        return fixes_applied

def main():
    parser = argparse.ArgumentParser(description="Angles AI Universe™ Schema Guard")
    parser.add_argument("--check", action="store_true", help="Check schema compliance")
    parser.add_argument("--autofix", action="store_true", help="Auto-fix safe schema issues")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    
    args = parser.parse_args()
    
    if not args.check and not args.autofix:
        parser.print_help()
        return 1
    
    try:
        guard = SchemaGuard()
        
        print(f"🚀 Schema Guard - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Get schemas
        expected = EXPECTED_SCHEMA
        actual = guard.get_actual_schema()
        
        if not actual:
            print("❌ Failed to retrieve actual schema")
            return 1
            
        # Compare
        differences = guard.compare_schemas(expected, actual)
        
        if args.json:
            print(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "has_differences": bool(any(differences.values())),
                "differences": differences
            }, indent=2))
            return 0
        
        # Print report
        has_diffs = guard.print_schema_report(differences)
        
        # Auto-fix if requested
        if args.autofix and has_diffs:
            print()
            fixes_applied = guard.auto_fix_schema(differences)
            
            if fixes_applied:
                print("\n🔄 Re-checking schema after fixes...")
                actual_updated = guard.get_actual_schema()
                updated_diffs = guard.compare_schemas(expected, actual_updated)
                guard.print_schema_report(updated_diffs)
        
        return 0 if not has_diffs else 1
        
    except Exception as e:
        print(f"❌ Schema Guard failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())