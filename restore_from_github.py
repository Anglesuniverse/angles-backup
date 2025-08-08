#!/usr/bin/env python3
"""
Angles AI Universe™ GitHub Restore System
Pulls latest backup from GitHub and restores Supabase database structure and data

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import requests
import logging
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

class GitHubRestoreSystem:
    """Complete restoration system from GitHub backups"""
    
    def __init__(self):
        """Initialize restore system"""
        self.setup_logging()
        self.load_environment()
        self.restore_summary = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'unknown',
            'operations': [],
            'errors': [],
            'restored_records': 0
        }
        
        self.logger.info("🔄 Angles AI Universe™ GitHub Restore System Initialized")
    
    def setup_logging(self):
        """Setup logging to restore.log"""
        os.makedirs("logs/active", exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger('github_restore')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler for restore.log
        log_file = "logs/active/restore.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter with timestamp
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
            'supabase_key': os.getenv('SUPABASE_KEY'),
            'github_token': os.getenv('GITHUB_TOKEN'),
            'github_username': os.getenv('GITHUB_USERNAME', 'angles-ai'),
            'github_repo': 'angles-backup'
        }
        
        # Validate required environment variables
        required = ['supabase_url', 'supabase_key', 'github_token']
        missing = [key for key in required if not self.env[key]]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        self.logger.info("📋 Environment variables loaded successfully")
    
    def pull_latest_backup(self) -> Optional[str]:
        """Pull latest backup repository and return backup directory path"""
        self.logger.info("📥 Pulling latest backup from GitHub...")
        
        try:
            # Create temporary directory for backup
            backup_dir = "/tmp/angles-backup"
            
            # Remove existing backup if present
            if os.path.exists(backup_dir):
                subprocess.run(['rm', '-rf', backup_dir], check=True)
            
            # Clone repository
            repo_url = f"https://{self.env['github_token']}@github.com/{self.env['github_username']}/{self.env['github_repo']}.git"
            
            result = subprocess.run([
                'git', 'clone', repo_url, backup_dir
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")
            
            self.logger.info(f"✅ Repository cloned to {backup_dir}")
            self.restore_summary['operations'].append("Repository cloned successfully")
            
            return backup_dir
            
        except subprocess.TimeoutExpired:
            self.logger.error("❌ Git clone timed out")
            return None
        except Exception as e:
            self.logger.error(f"❌ Failed to pull backup: {str(e)}")
            self.restore_summary['errors'].append(f"Repository pull failed: {str(e)}")
            return None
    
    def find_latest_backup_files(self, backup_dir: str) -> List[str]:
        """Find the latest backup files in the repository"""
        self.logger.info("🔍 Scanning for backup files...")
        
        try:
            backup_files = []
            
            # Look for backup files in common locations
            search_paths = [
                os.path.join(backup_dir, "backups"),
                os.path.join(backup_dir, "exports"),
                backup_dir
            ]
            
            for search_path in search_paths:
                if not os.path.exists(search_path):
                    continue
                
                for file in os.listdir(search_path):
                    if file.endswith('.json') and 'decision_vault' in file:
                        full_path = os.path.join(search_path, file)
                        backup_files.append(full_path)
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            self.logger.info(f"📄 Found {len(backup_files)} backup files")
            for i, file in enumerate(backup_files[:3]):  # Show first 3
                self.logger.info(f"   {i+1}. {os.path.basename(file)}")
            
            return backup_files
            
        except Exception as e:
            self.logger.error(f"❌ Failed to scan backup files: {str(e)}")
            return []
    
    def load_backup_data(self, backup_file: str) -> Optional[Dict]:
        """Load and validate backup data from file"""
        self.logger.info(f"📖 Loading backup data from {os.path.basename(backup_file)}")
        
        try:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Validate backup structure
            if 'data' not in backup_data:
                raise Exception("Invalid backup format: missing 'data' field")
            
            if 'metadata' not in backup_data:
                self.logger.warning("⚠️ Backup missing metadata - proceeding with data only")
                backup_data['metadata'] = {}
            
            record_count = len(backup_data['data'])
            backup_timestamp = backup_data.get('metadata', {}).get('timestamp', 'unknown')
            
            self.logger.info(f"✅ Backup loaded: {record_count} records from {backup_timestamp}")
            self.restore_summary['operations'].append(f"Loaded backup with {record_count} records")
            
            return backup_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load backup data: {str(e)}")
            self.restore_summary['errors'].append(f"Backup load failed: {str(e)}")
            return None
    
    def get_current_supabase_data(self) -> List[Dict]:
        """Fetch current data from Supabase decision_vault table"""
        self.logger.info("📥 Fetching current Supabase data...")
        
        try:
            headers = {
                'apikey': self.env['supabase_key'],
                'Authorization': f"Bearer {self.env['supabase_key']}",
                'Content-Type': 'application/json'
            }
            
            url = f"{self.env['supabase_url']}/rest/v1/decision_vault"
            params = {'select': '*', 'order': 'created_at.asc'}
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                current_data = response.json()
                self.logger.info(f"✅ Fetched {len(current_data)} current records")
                return current_data
            else:
                raise Exception(f"Supabase query failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to fetch current data: {str(e)}")
            return []
    
    def analyze_data_differences(self, current_data: List[Dict], backup_data: List[Dict]) -> Dict:
        """Analyze differences between current and backup data"""
        self.logger.info("🔍 Analyzing data differences...")
        
        # Create ID sets for comparison
        current_ids = {record.get('id') for record in current_data}
        backup_ids = {record.get('id') for record in backup_data}
        
        # Find missing records
        missing_ids = backup_ids - current_ids
        extra_ids = current_ids - backup_ids
        
        # Create lookup dictionaries
        backup_dict = {record.get('id'): record for record in backup_data}
        current_dict = {record.get('id'): record for record in current_data}
        
        # Records to restore
        records_to_restore = [backup_dict[rid] for rid in missing_ids if rid in backup_dict]
        
        analysis = {
            'current_count': len(current_data),
            'backup_count': len(backup_data),
            'missing_count': len(missing_ids),
            'extra_count': len(extra_ids),
            'records_to_restore': records_to_restore
        }
        
        self.logger.info(f"📊 Analysis complete:")
        self.logger.info(f"   Current records: {analysis['current_count']}")
        self.logger.info(f"   Backup records: {analysis['backup_count']}")
        self.logger.info(f"   Missing from current: {analysis['missing_count']}")
        self.logger.info(f"   Extra in current: {analysis['extra_count']}")
        
        return analysis
    
    def restore_missing_records(self, records_to_restore: List[Dict]) -> bool:
        """Restore missing records to Supabase"""
        if not records_to_restore:
            self.logger.info("✅ No missing records to restore")
            return True
        
        self.logger.info(f"🔄 Restoring {len(records_to_restore)} missing records...")
        
        try:
            headers = {
                'apikey': self.env['supabase_key'],
                'Authorization': f"Bearer {self.env['supabase_key']}",
                'Content-Type': 'application/json'
            }
            
            url = f"{self.env['supabase_url']}/rest/v1/decision_vault"
            restored_count = 0
            
            for record in records_to_restore:
                try:
                    # Clean record data (remove system fields)
                    clean_record = {
                        k: v for k, v in record.items() 
                        if k not in ['created_at', 'updated_at'] and v is not None
                    }
                    
                    response = requests.post(url, headers=headers, json=clean_record, timeout=15)
                    
                    if response.status_code in [200, 201]:
                        restored_count += 1
                        decision_preview = clean_record.get('decision', '')[:50] + "..." if len(clean_record.get('decision', '')) > 50 else clean_record.get('decision', '')
                        self.logger.info(f"✅ Restored: {decision_preview}")
                    else:
                        self.logger.error(f"❌ Failed to restore record {record.get('id')}: HTTP {response.status_code}")
                        self.restore_summary['errors'].append(f"Record restore failed: {response.status_code}")
                        
                except Exception as e:
                    self.logger.error(f"❌ Error restoring record: {str(e)}")
                    continue
            
            self.restore_summary['restored_records'] = restored_count
            self.restore_summary['operations'].append(f"Restored {restored_count} missing records")
            
            self.logger.info(f"✅ Restoration complete: {restored_count}/{len(records_to_restore)} records restored")
            return restored_count == len(records_to_restore)
            
        except Exception as e:
            self.logger.error(f"❌ Restoration failed: {str(e)}")
            self.restore_summary['errors'].append(f"Restoration process failed: {str(e)}")
            return False
    
    def run_full_restore(self) -> bool:
        """Run complete restore process"""
        self.logger.info("🚀 Starting GitHub Backup Restore Process")
        self.logger.info("=" * 70)
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Step 1: Pull latest backup
            backup_dir = self.pull_latest_backup()
            if not backup_dir:
                self.restore_summary['status'] = 'failed'
                return False
            
            # Step 2: Find backup files
            backup_files = self.find_latest_backup_files(backup_dir)
            if not backup_files:
                self.logger.error("❌ No backup files found")
                self.restore_summary['status'] = 'failed'
                return False
            
            # Step 3: Load latest backup
            backup_data = self.load_backup_data(backup_files[0])
            if not backup_data:
                self.restore_summary['status'] = 'failed'
                return False
            
            # Step 4: Get current data
            current_data = self.get_current_supabase_data()
            
            # Step 5: Analyze differences
            analysis = self.analyze_data_differences(current_data, backup_data['data'])
            
            # Step 6: Restore missing records
            restore_success = self.restore_missing_records(analysis['records_to_restore'])
            
            # Calculate duration
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.restore_summary['duration_seconds'] = duration
            
            # Determine final status
            if restore_success:
                self.restore_summary['status'] = 'success'
                self.logger.info("=" * 70)
                self.logger.info("🎉 GitHub Restore Process Completed Successfully")
                self.logger.info(f"   Duration: {duration:.2f} seconds")
                self.logger.info(f"   Records restored: {self.restore_summary['restored_records']}")
                return True
            else:
                self.restore_summary['status'] = 'partial'
                self.logger.warning("⚠️ Restore completed with some failures")
                return False
                
        except Exception as e:
            self.restore_summary['status'] = 'failed'
            self.restore_summary['errors'].append(f"Process failed: {str(e)}")
            self.logger.error(f"💥 Restore process failed: {str(e)}")
            return False
        
        finally:
            # Write restore summary
            self.write_restore_summary()
    
    def write_restore_summary(self):
        """Write restore summary to JSON file"""
        try:
            summary_file = f"logs/active/restore_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(summary_file, 'w') as f:
                json.dump(self.restore_summary, f, indent=2, default=str)
            
            self.logger.info(f"📄 Restore summary saved: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to write restore summary: {str(e)}")

def main():
    """Main entry point for restore system"""
    try:
        restore_system = GitHubRestoreSystem()
        success = restore_system.run_full_restore()
        
        if success:
            print("\n🎉 Restore completed successfully!")
            sys.exit(0)
        else:
            print("\n⚠️ Restore completed with issues - check logs for details")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Restore interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Restore failed with exception: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()