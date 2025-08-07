#!/usr/bin/env python3
"""
Angles AI Universe™ Automated Backup System
Backs up decision_vault table to GitHub with timestamped files

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import requests
import logging
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

class GitHubBackup:
    """Automated backup system for Angles AI Universe™"""
    
    def __init__(self):
        """Initialize backup system"""
        self.config = self._load_config()
        self._setup_logging()
        self._load_secrets()
        
        self.logger.info("📦 GitHub Backup System initialized")
    
    def _load_config(self) -> Dict:
        """Load configuration from config.json"""
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to load config.json: {e}")
            return {"backup": {"repository": "angles-backup", "retention_days": 30}}
    
    def _setup_logging(self):
        """Setup logging"""
        os.makedirs("logs", exist_ok=True)
        
        self.logger = logging.getLogger('backup_system')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler("logs/backup.log")
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
    
    def fetch_decision_vault_data(self) -> List[Dict]:
        """Fetch all data from decision_vault table"""
        self.logger.info("📥 Fetching decision_vault data from Supabase...")
        
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
                self.logger.info(f"✅ Fetched {len(data)} records from decision_vault")
                return data
            else:
                raise Exception(f"Supabase query failed: HTTP {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to fetch decision_vault data: {str(e)}")
            raise
    
    def create_backup_file(self, data: List[Dict]) -> Dict:
        """Create backup file with metadata"""
        timestamp = datetime.now(timezone.utc)
        
        backup_data = {
            'metadata': {
                'timestamp': timestamp.isoformat(),
                'record_count': len(data),
                'backup_version': '1.0.0',
                'source': 'decision_vault',
                'schema_version': '1.0'
            },
            'data': data
        }
        
        return backup_data
    
    def upload_to_github(self, backup_data: Dict, filename: str) -> bool:
        """Upload backup file to GitHub repository"""
        self.logger.info(f"📤 Uploading backup to GitHub: {filename}")
        
        try:
            # Convert data to JSON string
            json_content = json.dumps(backup_data, indent=2, default=str)
            
            # Base64 encode for GitHub API
            content_encoded = base64.b64encode(json_content.encode('utf-8')).decode('utf-8')
            
            # GitHub API URL
            api_url = f"https://api.github.com/repos/{self.secrets['github_username']}/{self.secrets['repository']}/contents/backups/{filename}"
            
            headers = {
                'Authorization': f"token {self.secrets['github_token']}",
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            }
            
            # Check if file already exists
            existing_response = requests.get(api_url, headers=headers)
            
            payload = {
                'message': f"Automated backup: {filename}",
                'content': content_encoded,
                'branch': 'main'
            }
            
            # If file exists, include SHA for update
            if existing_response.status_code == 200:
                existing_data = existing_response.json()
                payload['sha'] = existing_data['sha']
                self.logger.info("📝 Updating existing backup file")
            else:
                self.logger.info("📝 Creating new backup file")
            
            # Upload file
            response = requests.put(api_url, headers=headers, json=payload, timeout=60)
            
            if response.status_code in [200, 201]:
                self.logger.info(f"✅ Backup uploaded successfully to GitHub")
                return True
            else:
                self.logger.error(f"❌ GitHub upload failed: HTTP {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ GitHub upload error: {str(e)}")
            return False
    
    def cleanup_old_backups(self) -> bool:
        """Clean up old backup files from GitHub"""
        self.logger.info("🧹 Cleaning up old backup files...")
        
        try:
            retention_days = self.config.get('backup', {}).get('retention_days', 30)
            cutoff_date = datetime.now(timezone.utc).timestamp() - (retention_days * 24 * 60 * 60)
            
            # Get list of backup files
            api_url = f"https://api.github.com/repos/{self.secrets['github_username']}/{self.secrets['repository']}/contents/backups"
            headers = {
                'Authorization': f"token {self.secrets['github_token']}",
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(api_url, headers=headers)
            
            if response.status_code == 200:
                files = response.json()
                files_to_delete = []
                
                for file_info in files:
                    if file_info['name'].startswith('decision_vault_') and file_info['name'].endswith('.json'):
                        # Extract timestamp from filename
                        try:
                            timestamp_str = file_info['name'].replace('decision_vault_', '').replace('.json', '')
                            file_timestamp = datetime.fromisoformat(timestamp_str.replace('_', ' ').replace('-', ':')).timestamp()
                            
                            if file_timestamp < cutoff_date:
                                files_to_delete.append(file_info)
                        except:
                            continue  # Skip files with unexpected naming
                
                # Delete old files
                deleted_count = 0
                for file_info in files_to_delete:
                    delete_url = f"https://api.github.com/repos/{self.secrets['github_username']}/{self.secrets['repository']}/contents/backups/{file_info['name']}"
                    delete_payload = {
                        'message': f"Cleanup: Remove old backup {file_info['name']}",
                        'sha': file_info['sha'],
                        'branch': 'main'
                    }
                    
                    delete_response = requests.delete(delete_url, headers=headers, json=delete_payload)
                    
                    if delete_response.status_code == 200:
                        deleted_count += 1
                        self.logger.info(f"🗑️ Deleted old backup: {file_info['name']}")
                
                self.logger.info(f"✅ Cleanup complete: {deleted_count} old backups removed")
                return True
            else:
                self.logger.warning(f"⚠️ Could not list backup files for cleanup: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Cleanup error: {str(e)}")
            return False
    
    def run_backup(self) -> bool:
        """Run complete backup process"""
        self.logger.info("🚀 Starting automated backup process...")
        self.logger.info("=" * 50)
        
        try:
            # Fetch data
            data = self.fetch_decision_vault_data()
            
            # Create backup
            backup_data = self.create_backup_file(data)
            
            # Generate filename with timestamp
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')
            filename = f"decision_vault_{timestamp}.json"
            
            # Upload to GitHub
            success = self.upload_to_github(backup_data, filename)
            
            if success:
                # Cleanup old backups
                self.cleanup_old_backups()
                
                self.logger.info("=" * 50)
                self.logger.info("🎉 Backup process completed successfully!")
                self.logger.info(f"   Records backed up: {len(data)}")
                self.logger.info(f"   Filename: {filename}")
                self.logger.info(f"   Repository: {self.secrets['repository']}")
                return True
            else:
                self.logger.error("❌ Backup process failed!")
                return False
                
        except Exception as e:
            self.logger.error(f"💥 Backup process failed with exception: {str(e)}")
            return False

def main():
    """Main entry point"""
    try:
        backup_system = GitHubBackup()
        success = backup_system.run_backup()
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Backup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Backup failed with exception: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()