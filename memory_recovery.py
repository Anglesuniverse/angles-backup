#!/usr/bin/env python3
"""
Memory Recovery System for Angles AI Universe™
4-level fallback restore system with automated testing and verification

Priority Order: GitHub → Supabase → Local → Notion

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import json
import logging
import requests
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import tempfile
import shutil

try:
    from supabase import create_client, Client as SupabaseClient
except ImportError:
    SupabaseClient = None
    create_client = None

try:
    from notion_client import Client as NotionClient
except ImportError:
    NotionClient = None

class MemoryRecoverySystem:
    """4-level fallback memory recovery system"""
    
    def __init__(self):
        """Initialize recovery system with environment variables"""
        # Environment variables
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_repo = os.getenv('GITHUB_REPO') or os.getenv('REPO_URL')
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.notion_api_key = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
        self.notion_database_id = os.getenv('NOTION_DATABASE_ID')
        self.failure_webhook_url = os.getenv('FAILURE_WEBHOOK_URL')
        
        # Initialize clients
        self.supabase = self._init_supabase_client()
        self.notion = self._init_notion_client()
        
        # Logging setup
        self.log_file = Path('last_restore.log')
        self.history_file = Path('restore_history.json')
        self._setup_logging()
        
        # Priority order for restoration
        self.restore_sources = ['github', 'supabase', 'local', 'notion']
        
        self.logger.info("🔄 MEMORY RECOVERY SYSTEM INITIALIZED")
        self.logger.info("Priority Order: GitHub → Supabase → Local → Notion")
    
    def _init_supabase_client(self):
        """Initialize Supabase client"""
        if not create_client or not self.supabase_url or not self.supabase_key:
            return None
        try:
            return create_client(self.supabase_url, self.supabase_key)
        except Exception as e:
            print(f"Failed to initialize Supabase client: {e}")
            return None
    
    def _init_notion_client(self):
        """Initialize Notion client"""
        if not NotionClient or not self.notion_api_key:
            return None
        try:
            return NotionClient(auth=self.notion_api_key)
        except Exception as e:
            print(f"Failed to initialize Notion client: {e}")
            return None
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create logger
        self.logger = logging.getLogger('memory_recovery')
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _log_restore_attempt(self, source: str, status: str, error: str = None, data_size: int = 0):
        """Log restore attempt to history file"""
        try:
            history_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": source,
                "status": status,
                "data_size": data_size,
                "error": error
            }
            
            # Load existing history
            history = []
            if self.history_file.exists():
                try:
                    with open(self.history_file, 'r') as f:
                        history = json.load(f)
                except:
                    history = []
            
            # Append new entry
            history.append(history_entry)
            
            # Keep only last 1000 entries
            if len(history) > 1000:
                history = history[-1000:]
            
            # Save updated history
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to log restore attempt: {e}")
    
    def _validate_backup_integrity(self, data: Dict[str, Any]) -> bool:
        """Validate backup JSON structure"""
        if not isinstance(data, dict):
            return False
        
        required_keys = ['source', 'data']
        for key in required_keys:
            if key not in data:
                self.logger.warning(f"Missing required key: {key}")
                return False
        
        return True
    
    def restore_from_github(self, mock: bool = False) -> Optional[Dict[str, Any]]:
        """Restore memory data from GitHub repository"""
        self.logger.info("🐙 Attempting restore from GitHub...")
        
        if mock:
            self.logger.info("📋 Mock mode enabled for GitHub")
            try:
                with open('backup_github.json', 'r') as f:
                    data = json.load(f)
                if self._validate_backup_integrity(data):
                    self._log_restore_attempt('github', 'success', data_size=len(str(data)))
                    self.logger.info("✅ GitHub restore successful (mock)")
                    return data
                else:
                    self._log_restore_attempt('github', 'fail', 'Invalid backup structure')
                    return None
            except Exception as e:
                self._log_restore_attempt('github', 'fail', str(e))
                self.logger.error(f"❌ GitHub restore failed (mock): {e}")
                return None
        
        if not self.github_token or not self.github_repo:
            error = "GitHub credentials not available"
            self._log_restore_attempt('github', 'fail', error)
            self.logger.error(f"❌ {error}")
            return None
        
        try:
            # Clone or pull repository
            repo_dir = Path('github_restore_temp')
            if repo_dir.exists():
                shutil.rmtree(repo_dir)
            
            # Prepare clone URL
            if self.github_repo.startswith('http'):
                clone_url = self.github_repo.replace('https://', f'https://x-access-token:{self.github_token}@')
            else:
                clone_url = f'https://x-access-token:{self.github_token}@github.com/{self.github_repo}.git'
            
            # Clone repository
            result = subprocess.run(['git', 'clone', clone_url, str(repo_dir)], 
                                 capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                error = f"Git clone failed: {result.stderr}"
                self._log_restore_attempt('github', 'fail', error)
                self.logger.error(f"❌ {error}")
                return None
            
            # Look for backup files in export directory
            export_dir = repo_dir / 'export'
            backup_files = []
            
            if export_dir.exists():
                # Look for recent memory backup files
                backup_files = sorted(export_dir.glob('memory_backup_*.json'), reverse=True)
                if not backup_files:
                    backup_files = sorted(export_dir.glob('backup_*.json'), reverse=True)
                if not backup_files:
                    backup_files = sorted(export_dir.glob('*.json'), reverse=True)
            
            if not backup_files:
                error = "No backup files found in GitHub repository"
                self._log_restore_attempt('github', 'fail', error)
                self.logger.error(f"❌ {error}")
                shutil.rmtree(repo_dir)
                return None
            
            # Load the most recent backup
            backup_file = backup_files[0]
            with open(backup_file, 'r') as f:
                data = json.load(f)
            
            # Cleanup
            shutil.rmtree(repo_dir)
            
            if self._validate_backup_integrity(data):
                self._log_restore_attempt('github', 'success', data_size=len(str(data)))
                self.logger.info("✅ GitHub restore successful")
                return data
            else:
                error = "Invalid backup structure from GitHub"
                self._log_restore_attempt('github', 'fail', error)
                self.logger.error(f"❌ {error}")
                return None
                
        except Exception as e:
            error = f"GitHub restore failed: {e}"
            self._log_restore_attempt('github', 'fail', error)
            self.logger.error(f"❌ {error}")
            return None
    
    def restore_from_supabase(self, mock: bool = False) -> Optional[Dict[str, Any]]:
        """Restore memory data from Supabase storage"""
        self.logger.info("🗄️ Attempting restore from Supabase...")
        
        if mock:
            self.logger.info("📋 Mock mode enabled for Supabase")
            try:
                with open('backup_supabase.json', 'r') as f:
                    data = json.load(f)
                if self._validate_backup_integrity(data):
                    self._log_restore_attempt('supabase', 'success', data_size=len(str(data)))
                    self.logger.info("✅ Supabase restore successful (mock)")
                    return data
                else:
                    self._log_restore_attempt('supabase', 'fail', 'Invalid backup structure')
                    return None
            except Exception as e:
                self._log_restore_attempt('supabase', 'fail', str(e))
                self.logger.error(f"❌ Supabase restore failed (mock): {e}")
                return None
        
        if not self.supabase:
            error = "Supabase client not available"
            self._log_restore_attempt('supabase', 'fail', error)
            self.logger.error(f"❌ {error}")
            return None
        
        try:
            # Try to get the most recent backup from storage
            bucket_name = 'memory_backups'
            
            # List files in both manual and daily directories
            files_to_check = []
            for prefix in ['manual', 'daily']:
                try:
                    files = self.supabase.storage.from_(bucket_name).list(f"{prefix}/")
                    for file_info in files:
                        file_name = file_info.get('name') if isinstance(file_info, dict) else getattr(file_info, 'name', '')
                        if file_name.endswith('.json'):
                            files_to_check.append(f"{prefix}/{file_name}")
                except:
                    continue
            
            if not files_to_check:
                error = "No backup files found in Supabase storage"
                self._log_restore_attempt('supabase', 'fail', error)
                self.logger.error(f"❌ {error}")
                return None
            
            # Try to download the most recent file
            for file_path in sorted(files_to_check, reverse=True):
                try:
                    response = self.supabase.storage.from_(bucket_name).download(file_path)
                    if response:
                        data = json.loads(response.decode('utf-8'))
                        if self._validate_backup_integrity(data):
                            self._log_restore_attempt('supabase', 'success', data_size=len(str(data)))
                            self.logger.info("✅ Supabase restore successful")
                            return data
                except:
                    continue
            
            error = "No valid backup files found in Supabase storage"
            self._log_restore_attempt('supabase', 'fail', error)
            self.logger.error(f"❌ {error}")
            return None
            
        except Exception as e:
            error = f"Supabase restore failed: {e}"
            self._log_restore_attempt('supabase', 'fail', error)
            self.logger.error(f"❌ {error}")
            return None
    
    def restore_from_local(self, mock: bool = False) -> Optional[Dict[str, Any]]:
        """Restore memory data from local backup files"""
        self.logger.info("📁 Attempting restore from local storage...")
        
        if mock:
            self.logger.info("📋 Mock mode enabled for local storage")
            try:
                with open('backup_local.json', 'r') as f:
                    data = json.load(f)
                if self._validate_backup_integrity(data):
                    self._log_restore_attempt('local', 'success', data_size=len(str(data)))
                    self.logger.info("✅ Local restore successful (mock)")
                    return data
                else:
                    self._log_restore_attempt('local', 'fail', 'Invalid backup structure')
                    return None
            except Exception as e:
                self._log_restore_attempt('local', 'fail', str(e))
                self.logger.error(f"❌ Local restore failed (mock): {e}")
                return None
        
        try:
            # Check multiple local directories for backup files
            search_dirs = [
                Path('backups'),
                Path('export'),
                Path('memory_backups'),
                Path('.'),
                Path('/tmp')
            ]
            
            backup_files = []
            for search_dir in search_dirs:
                if search_dir.exists():
                    # Look for JSON backup files
                    backup_files.extend(search_dir.glob('memory_backup_*.json'))
                    backup_files.extend(search_dir.glob('backup_*.json'))
                    backup_files.extend(search_dir.glob('*_backup.json'))
            
            if not backup_files:
                error = "No local backup files found"
                self._log_restore_attempt('local', 'fail', error)
                self.logger.error(f"❌ {error}")
                return None
            
            # Sort by modification time (most recent first)
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Try to load the most recent backup
            for backup_file in backup_files:
                try:
                    with open(backup_file, 'r') as f:
                        data = json.load(f)
                    if self._validate_backup_integrity(data):
                        self._log_restore_attempt('local', 'success', data_size=len(str(data)))
                        self.logger.info(f"✅ Local restore successful from {backup_file}")
                        return data
                except:
                    continue
            
            error = "No valid local backup files found"
            self._log_restore_attempt('local', 'fail', error)
            self.logger.error(f"❌ {error}")
            return None
            
        except Exception as e:
            error = f"Local restore failed: {e}"
            self._log_restore_attempt('local', 'fail', error)
            self.logger.error(f"❌ {error}")
            return None
    
    def restore_from_notion(self, mock: bool = False) -> Optional[Dict[str, Any]]:
        """Restore memory data from Notion database"""
        self.logger.info("📝 Attempting restore from Notion...")
        
        if mock:
            self.logger.info("📋 Mock mode enabled for Notion")
            try:
                with open('backup_notion.json', 'r') as f:
                    data = json.load(f)
                if self._validate_backup_integrity(data):
                    self._log_restore_attempt('notion', 'success', data_size=len(str(data)))
                    self.logger.info("✅ Notion restore successful (mock)")
                    return data
                else:
                    self._log_restore_attempt('notion', 'fail', 'Invalid backup structure')
                    return None
            except Exception as e:
                self._log_restore_attempt('notion', 'fail', str(e))
                self.logger.error(f"❌ Notion restore failed (mock): {e}")
                return None
        
        if not self.notion or not self.notion_database_id:
            error = "Notion client or database ID not available"
            self._log_restore_attempt('notion', 'fail', error)
            self.logger.error(f"❌ {error}")
            return None
        
        try:
            # Query the Notion database for backup data
            response = self.notion.databases.query(
                database_id=self.notion_database_id,
                sorts=[{"property": "created_time", "direction": "descending"}],
                page_size=10
            )
            
            if not response.get('results'):
                error = "No data found in Notion database"
                self._log_restore_attempt('notion', 'fail', error)
                self.logger.error(f"❌ {error}")
                return None
            
            # Extract and format data from Notion pages
            notion_data = []
            for page in response['results']:
                properties = page.get('properties', {})
                page_data = {}
                
                for prop_name, prop_value in properties.items():
                    if prop_value.get('type') == 'title':
                        page_data['title'] = prop_value['title'][0]['plain_text'] if prop_value['title'] else ''
                    elif prop_value.get('type') == 'rich_text':
                        page_data[prop_name.lower()] = prop_value['rich_text'][0]['plain_text'] if prop_value['rich_text'] else ''
                    elif prop_value.get('type') == 'date':
                        page_data[prop_name.lower()] = prop_value['date']['start'] if prop_value['date'] else ''
                
                notion_data.append(page_data)
            
            # Format as backup structure
            backup_data = {
                "source": "Notion",
                "data": notion_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": datetime.now().strftime('%Y-%m-%d')
            }
            
            if self._validate_backup_integrity(backup_data):
                self._log_restore_attempt('notion', 'success', data_size=len(str(backup_data)))
                self.logger.info("✅ Notion restore successful")
                return backup_data
            else:
                error = "Invalid backup structure from Notion"
                self._log_restore_attempt('notion', 'fail', error)
                self.logger.error(f"❌ {error}")
                return None
                
        except Exception as e:
            error = f"Notion restore failed: {e}"
            self._log_restore_attempt('notion', 'fail', error)
            self.logger.error(f"❌ {error}")
            return None
    
    def auto_restore(self, mock: bool = False) -> Optional[Dict[str, Any]]:
        """Automatic restore with 4-level fallback priority"""
        self.logger.info("🔄 Starting automatic restore process...")
        self.logger.info("Priority: GitHub → Supabase → Local → Notion")
        
        restore_functions = {
            'github': self.restore_from_github,
            'supabase': self.restore_from_supabase,
            'local': self.restore_from_local,
            'notion': self.restore_from_notion
        }
        
        successful_data = None
        successful_source = None
        
        for source in self.restore_sources:
            self.logger.info(f"🔍 Trying {source.upper()}...")
            
            try:
                data = restore_functions[source](mock=mock)
                if data is not None:
                    successful_data = data
                    successful_source = source
                    self.logger.info(f"✅ Restore successful from {source.upper()}")
                    break
                else:
                    self.logger.warning(f"⚠️ {source.upper()} failed, trying next source...")
            except Exception as e:
                self.logger.error(f"❌ {source.upper()} error: {e}")
                continue
        
        if successful_data is None:
            error = "All restore sources failed"
            self.logger.error(f"❌ {error}")
            self._send_failure_notification(error)
            return None
        
        # Log successful restore
        self.logger.info(f"🎉 Auto-restore completed successfully from {successful_source.upper()}")
        
        # Trigger self-healing if needed
        if not mock:
            self._trigger_self_healing(successful_source, successful_data)
        
        return successful_data
    
    def _send_failure_notification(self, error: str):
        """Send failure notification via webhook"""
        if not self.failure_webhook_url:
            return
        
        try:
            # Get last successful restore date
            last_success = None
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
                    for entry in reversed(history):
                        if entry.get('status') == 'success':
                            last_success = entry.get('timestamp')
                            break
            
            payload = {
                "message": "Memory Recovery System: All restore sources failed",
                "error": error,
                "last_successful_restore": last_success,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            response = requests.post(self.failure_webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                self.logger.info("📢 Failure notification sent successfully")
            else:
                self.logger.warning(f"⚠️ Failure notification failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to send failure notification: {e}")
    
    def _trigger_self_healing(self, successful_source: str, data: Dict[str, Any]):
        """Trigger self-healing to sync data between sources"""
        self.logger.info("🔧 Checking for self-healing opportunities...")
        
        # If restore was successful from Supabase but GitHub failed, sync to GitHub
        if successful_source == 'supabase' and 'github' in self.restore_sources:
            try:
                self._sync_to_github(data)
            except Exception as e:
                self.logger.error(f"❌ Self-healing to GitHub failed: {e}")
    
    def _sync_to_github(self, data: Dict[str, Any]):
        """Sync backup data to GitHub for self-healing"""
        if not self.github_token or not self.github_repo:
            return
        
        try:
            self.logger.info("🔧 Self-healing: Syncing backup to GitHub...")
            
            # Create a temporary backup file
            timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
            backup_filename = f"self_healing_backup_{timestamp}.json"
            
            with open(backup_filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Add version stamp
            data['version'] = datetime.now().strftime('%Y-%m-%d')
            data['self_healing'] = True
            
            # Use git to commit and push
            subprocess.run(['git', 'add', backup_filename], check=True)
            subprocess.run(['git', 'commit', '-m', f'Self-healing backup: {timestamp}'], check=True)
            subprocess.run(['git', 'push'], check=True)
            
            self.logger.info("✅ Self-healing: Backup synced to GitHub")
            
            # Cleanup local file
            Path(backup_filename).unlink()
            
        except Exception as e:
            self.logger.error(f"❌ Self-healing sync failed: {e}")
    
    def get_restore_history(self) -> List[Dict[str, Any]]:
        """Get restore attempt history"""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def get_last_successful_restore(self) -> Optional[Dict[str, Any]]:
        """Get details of the last successful restore"""
        history = self.get_restore_history()
        for entry in reversed(history):
            if entry.get('status') == 'success':
                return entry
        return None


# Convenience functions for direct usage
def restore_from_github(mock: bool = False) -> Optional[Dict[str, Any]]:
    """Direct GitHub restore function"""
    recovery = MemoryRecoverySystem()
    return recovery.restore_from_github(mock=mock)

def restore_from_supabase(mock: bool = False) -> Optional[Dict[str, Any]]:
    """Direct Supabase restore function"""
    recovery = MemoryRecoverySystem()
    return recovery.restore_from_supabase(mock=mock)

def restore_from_local(mock: bool = False) -> Optional[Dict[str, Any]]:
    """Direct local restore function"""
    recovery = MemoryRecoverySystem()
    return recovery.restore_from_local(mock=mock)

def restore_from_notion(mock: bool = False) -> Optional[Dict[str, Any]]:
    """Direct Notion restore function"""
    recovery = MemoryRecoverySystem()
    return recovery.restore_from_notion(mock=mock)

def auto_restore(mock: bool = False) -> Optional[Dict[str, Any]]:
    """Direct auto-restore function"""
    recovery = MemoryRecoverySystem()
    return recovery.auto_restore(mock=mock)

if __name__ == "__main__":
    # Command line execution
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "auto":
            result = auto_restore(mock=True)
            if result:
                print("✅ Auto-restore successful")
                print(f"Source: {result.get('source')}")
            else:
                print("❌ Auto-restore failed")
        else:
            source = sys.argv[1].lower()
            if source in ['github', 'supabase', 'local', 'notion']:
                recovery = MemoryRecoverySystem()
                func = getattr(recovery, f'restore_from_{source}')
                result = func(mock=True)
                if result:
                    print(f"✅ {source.title()} restore successful")
                else:
                    print(f"❌ {source.title()} restore failed")
            else:
                print("Usage: python memory_recovery.py [github|supabase|local|notion|auto]")
    else:
        # Default to auto-restore
        result = auto_restore(mock=True)
        if result:
            print("✅ Auto-restore successful")
        else:
            print("❌ Auto-restore failed")