#!/usr/bin/env python3
"""
Angles AI Universe™ Automated Restore System
Restores decision_vault data from GitHub backups with schema validation

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import argparse
import requests
import logging
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

class GitHubRestore:
    """Automated restore system for Angles AI Universe™"""
    
    def __init__(self, dry_run: bool = True):
        """Initialize restore system"""
        self.dry_run = dry_run
        self.config = self._load_config()
        self._setup_logging()
        self._load_secrets()
        
        self.logger.info("🔄 GitHub Restore System initialized")
        if self.dry_run:
            self.logger.info("⚠️ Running in DRY RUN mode - no changes will be made")
    
    def _load_config(self) -> Dict:
        """Load configuration from config.json"""
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to load config.json: {e}")
            return {"restore": {"auto_migrate": False}, "backup": {"repository": "angles-backup"}}
    
    def _setup_logging(self):
        """Setup logging"""
        os.makedirs("logs", exist_ok=True)
        
        self.logger = logging.getLogger('restore_system')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler("logs/restore.log")
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
    
    def _load_secrets(self):
        """Load secrets from environment"""
        self.secrets = {
            'supabase_url': os.getenv('SUPABASE_URL'),
            'supabase_key': os.getenv('SUPABASE_KEY'),
            'github_token': os.getenv('GITHUB_TOKEN'),
            'github_username': os.getenv('GITHUB_USERNAME', 'angles-ai'),
            'repository': self.config.get('backup', {}).get('repository', 'angles-backup')
        }
        
        # Validate required secrets
        required = ['supabase_url', 'supabase_key', 'github_token']
        missing = [key for key in required if not self.secrets[key]]
        
        if missing:
            raise ValueError(f"Missing required secrets: {', '.join(missing)}")
    
    def list_available_backups(self) -> List[Dict]:
        """List available backup files from GitHub"""
        self.logger.info("📋 Listing available backups from GitHub...")
        
        try:
            api_url = f"https://api.github.com/repos/{self.secrets['github_username']}/{self.secrets['repository']}/contents/backups"
            headers = {
                'Authorization': f"token {self.secrets['github_token']}",
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(api_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                files = response.json()
                backup_files = []
                
                for file_info in files:
                    if file_info['name'].startswith('decision_vault_') and file_info['name'].endswith('.json'):
                        backup_files.append({
                            'name': file_info['name'],
                            'download_url': file_info['download_url'],
                            'size': file_info['size'],
                            'sha': file_info['sha']
                        })
                
                backup_files.sort(key=lambda x: x['name'], reverse=True)  # Sort by name (newest first)
                self.logger.info(f"✅ Found {len(backup_files)} backup files")
                return backup_files
            else:
                raise Exception(f"GitHub API request failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to list backups: {str(e)}")
            raise
    
    def download_backup(self, backup_file: Dict) -> Dict:
        """Download and parse backup file"""
        self.logger.info(f"📥 Downloading backup: {backup_file['name']}")
        
        try:
            response = requests.get(backup_file['download_url'], timeout=60)
            
            if response.status_code == 200:
                backup_data = response.json()
                
                # Validate backup structure
                if 'metadata' not in backup_data or 'data' not in backup_data:
                    raise Exception("Invalid backup file structure")
                
                record_count = len(backup_data['data'])
                self.logger.info(f"✅ Downloaded backup with {record_count} records")
                return backup_data
            else:
                raise Exception(f"Download failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to download backup: {str(e)}")
            raise
    
    def fetch_current_data(self) -> List[Dict]:
        """Fetch current data from Supabase"""
        self.logger.info("📥 Fetching current data from Supabase...")
        
        try:
            url = f"{self.secrets['supabase_url']}/rest/v1/decision_vault"
            headers = {
                'apikey': self.secrets['supabase_key'],
                'Authorization': f"Bearer {self.secrets['supabase_key']}",
                'Content-Type': 'application/json'
            }
            
            params = {
                'select': '*',
                'order': 'created_at.asc'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✅ Fetched {len(data)} current records")
                return data
            else:
                raise Exception(f"Supabase query failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to fetch current data: {str(e)}")
            raise
    
    def analyze_differences(self, current_data: List[Dict], backup_data: List[Dict]) -> Dict:
        """Analyze differences between current and backup data"""
        self.logger.info("🔍 Analyzing differences between current and backup data...")
        
        # Create sets of record IDs
        current_ids = {record['id'] for record in current_data}
        backup_ids = {record['id'] for record in backup_data}
        
        # Find differences
        missing_in_current = backup_ids - current_ids
        extra_in_current = current_ids - backup_ids
        common_ids = current_ids & backup_ids
        
        # Check for content differences in common records
        current_dict = {record['id']: record for record in current_data}
        backup_dict = {record['id']: record for record in backup_data}
        
        modified_records = []
        for record_id in common_ids:
            current_record = current_dict[record_id]
            backup_record = backup_dict[record_id]
            
            # Compare key fields (excluding timestamps and sync flags)
            compare_fields = ['decision', 'type', 'date']
            is_different = any(
                current_record.get(field) != backup_record.get(field)
                for field in compare_fields
            )
            
            if is_different:
                modified_records.append({
                    'id': record_id,
                    'current': current_record,
                    'backup': backup_record
                })
        
        analysis = {
            'missing_in_current': len(missing_in_current),
            'extra_in_current': len(extra_in_current),
            'modified_records': len(modified_records),
            'records_to_insert': [backup_dict[rid] for rid in missing_in_current],
            'records_to_update': modified_records,
            'records_to_delete': [current_dict[rid] for rid in extra_in_current]
        }
        
        self.logger.info(f"📊 Analysis complete:")
        self.logger.info(f"   Records to insert: {analysis['missing_in_current']}")
        self.logger.info(f"   Records to update: {analysis['modified_records']}")
        self.logger.info(f"   Records to delete: {analysis['extra_in_current']}")
        
        return analysis
    
    def check_schema_compatibility(self, backup_data: Dict) -> bool:
        """Check if backup schema is compatible with current database"""
        self.logger.info("🔍 Checking schema compatibility...")
        
        try:
            metadata = backup_data.get('metadata', {})
            schema_version = metadata.get('schema_version', '1.0')
            
            # For now, we support schema version 1.0
            supported_versions = ['1.0']
            
            if schema_version in supported_versions:
                self.logger.info(f"✅ Schema version {schema_version} is compatible")
                return True
            else:
                self.logger.warning(f"⚠️ Schema version {schema_version} may not be compatible")
                
                auto_migrate = self.config.get('restore', {}).get('auto_migrate', False)
                if auto_migrate:
                    self.logger.info("🔄 Auto-migration enabled - proceeding with restore")
                    return True
                else:
                    self.logger.error("❌ Auto-migration disabled - restore aborted")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ Schema compatibility check failed: {str(e)}")
            return False
    
    def execute_restore(self, analysis: Dict) -> bool:
        """Execute the restore operation"""
        if self.dry_run:
            self.logger.info("📋 DRY RUN - Would perform the following operations:")
            self.logger.info(f"   Insert {len(analysis['records_to_insert'])} records")
            self.logger.info(f"   Update {len(analysis['records_to_update'])} records")
            self.logger.info(f"   Delete {len(analysis['records_to_delete'])} records")
            return True
        
        self.logger.info("🔄 Executing restore operations...")
        
        try:
            headers = {
                'apikey': self.secrets['supabase_key'],
                'Authorization': f"Bearer {self.secrets['supabase_key']}",
                'Content-Type': 'application/json'
            }
            
            base_url = f"{self.secrets['supabase_url']}/rest/v1/decision_vault"
            
            # Insert missing records
            for record in analysis['records_to_insert']:
                # Remove any system-generated fields
                clean_record = {k: v for k, v in record.items() if k not in ['created_at', 'updated_at']}
                
                response = requests.post(base_url, headers=headers, json=clean_record, timeout=30)
                
                if response.status_code not in [200, 201]:
                    self.logger.error(f"❌ Failed to insert record {record.get('id')}: HTTP {response.status_code}")
                    return False
                else:
                    self.logger.info(f"✅ Inserted record {record.get('id')}")
            
            # Update modified records
            for modification in analysis['records_to_update']:
                record_id = modification['id']
                backup_record = modification['backup']
                
                # Prepare update data
                update_data = {k: v for k, v in backup_record.items() if k not in ['id', 'created_at', 'updated_at']}
                
                update_url = f"{base_url}?id=eq.{record_id}"
                response = requests.patch(update_url, headers=headers, json=update_data, timeout=30)
                
                if response.status_code != 204:
                    self.logger.error(f"❌ Failed to update record {record_id}: HTTP {response.status_code}")
                    return False
                else:
                    self.logger.info(f"✅ Updated record {record_id}")
            
            # Delete extra records (optional - usually we don't delete during restore)
            # Commented out for safety - uncomment if needed
            # for record in analysis['records_to_delete']:
            #     record_id = record['id']
            #     delete_url = f"{base_url}?id=eq.{record_id}"
            #     response = requests.delete(delete_url, headers=headers, timeout=30)
            #     
            #     if response.status_code != 204:
            #         self.logger.error(f"❌ Failed to delete record {record_id}: HTTP {response.status_code}")
            #         return False
            #     else:
            #         self.logger.info(f"✅ Deleted record {record_id}")
            
            self.logger.info("✅ Restore operations completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Restore execution failed: {str(e)}")
            return False
    
    def run_restore(self, backup_filename: Optional[str] = None) -> bool:
        """Run complete restore process"""
        self.logger.info("🚀 Starting automated restore process...")
        self.logger.info("=" * 50)
        
        try:
            # List available backups
            available_backups = self.list_available_backups()
            
            if not available_backups:
                self.logger.error("❌ No backup files found")
                return False
            
            # Select backup file
            if backup_filename:
                selected_backup = next((b for b in available_backups if b['name'] == backup_filename), None)
                if not selected_backup:
                    self.logger.error(f"❌ Backup file '{backup_filename}' not found")
                    return False
            else:
                selected_backup = available_backups[0]  # Use latest
                self.logger.info(f"📁 Using latest backup: {selected_backup['name']}")
            
            # Download backup
            backup_data = self.download_backup(selected_backup)
            
            # Check schema compatibility
            if not self.check_schema_compatibility(backup_data):
                return False
            
            # Fetch current data
            current_data = self.fetch_current_data()
            
            # Analyze differences
            analysis = self.analyze_differences(current_data, backup_data['data'])
            
            # Execute restore
            success = self.execute_restore(analysis)
            
            self.logger.info("=" * 50)
            if success:
                self.logger.info("🎉 Restore process completed successfully!")
            else:
                self.logger.error("❌ Restore process failed!")
            
            return success
            
        except Exception as e:
            self.logger.error(f"💥 Restore process failed with exception: {str(e)}")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Angles AI Universe™ Restore System')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without executing them')
    parser.add_argument('--file', type=str, help='Specific backup file to restore from')
    parser.add_argument('--live', action='store_true', help='Execute live restore (overrides dry-run default)')
    
    args = parser.parse_args()
    
    # Determine if this is a dry run
    dry_run = args.dry_run or not args.live
    
    try:
        restore_system = GitHubRestore(dry_run=dry_run)
        success = restore_system.run_restore(backup_filename=args.file)
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Restore interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Restore failed with exception: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()