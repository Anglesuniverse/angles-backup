#!/usr/bin/env python3
"""
Angles AI Universe™ AutoSync Files
File change detection and decision vault integration

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import hashlib
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Set

try:
    import requests
except ImportError:
    print("❌ Missing required dependency: requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def setup_logging():
    """Setup logging for autosync"""
    os.makedirs("logs/active", exist_ok=True)
    
    logger = logging.getLogger('autosync')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler
    file_handler = logging.FileHandler('logs/active/autosync.log')
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

class FileAutoSync:
    """File change detection and auto-sync to decision vault"""
    
    def __init__(self, dry_run: bool = False):
        self.logger = setup_logging()
        self.dry_run = dry_run
        
        # Configuration
        self.manifest_file = "export/file_manifest.json"
        self.excluded_dirs = {'.git', 'logs', '__pycache__', 'venv', '.venv', 'node_modules', 'temp_backup_*'}
        self.excluded_files = {'.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.log'}
        self.key_files = {
            'operations.py',
            'architects_table_model.py', 
            'memory_bridge.py',
            'run_migration.py',
            'memory_sync.py',
            'backend_monitor.py'
        }
        
        # Supabase configuration
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            self.logger.warning("⚠️ Supabase not configured - file changes will be logged only")
            self.supabase_enabled = False
        else:
            self.supabase_enabled = True
            self.supabase_headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
        
        self.changes_detected = []
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.logger.warning(f"⚠️ Could not hash {file_path}: {e}")
            return ""
    
    def should_include_file(self, file_path: Path) -> bool:
        """Check if file should be included in scanning"""
        # Skip excluded directories
        for part in file_path.parts:
            if any(part.startswith(exc.rstrip('*')) for exc in self.excluded_dirs):
                return False
        
        # Skip excluded file extensions
        if file_path.suffix in self.excluded_files:
            return False
        
        # Skip hidden files
        if file_path.name.startswith('.') and file_path.name not in {'.env.example'}:
            return False
        
        # Skip very large files (> 10MB)
        try:
            if file_path.stat().st_size > 10 * 1024 * 1024:
                return False
        except:
            return False
        
        return True
    
    def scan_repository(self) -> Dict[str, Dict[str, Any]]:
        """Scan repository and build file manifest"""
        self.logger.info("🔍 Scanning repository for files...")
        
        manifest = {}
        file_count = 0
        
        try:
            repo_root = Path('.')
            
            for file_path in repo_root.rglob('*'):
                if file_path.is_file() and self.should_include_file(file_path):
                    try:
                        file_hash = self.calculate_file_hash(file_path)
                        file_stat = file_path.stat()
                        
                        relative_path = str(file_path.relative_to(repo_root))
                        
                        manifest[relative_path] = {
                            'hash': file_hash,
                            'size': file_stat.st_size,
                            'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                            'scanned_at': datetime.now(timezone.utc).isoformat()
                        }
                        
                        file_count += 1
                        
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error processing {file_path}: {e}")
            
            self.logger.info(f"📁 Scanned {file_count} files")
            return manifest
            
        except Exception as e:
            self.logger.error(f"❌ Error scanning repository: {e}")
            return {}
    
    def load_existing_manifest(self) -> Dict[str, Dict[str, Any]]:
        """Load existing file manifest"""
        try:
            if os.path.exists(self.manifest_file):
                with open(self.manifest_file, 'r') as f:
                    manifest = json.load(f)
                    self.logger.info(f"📋 Loaded existing manifest with {len(manifest)} files")
                    return manifest
            else:
                self.logger.info("📋 No existing manifest found")
                return {}
        except Exception as e:
            self.logger.error(f"❌ Error loading manifest: {e}")
            return {}
    
    def save_manifest(self, manifest: Dict[str, Dict[str, Any]]) -> bool:
        """Save file manifest"""
        try:
            os.makedirs(os.path.dirname(self.manifest_file), exist_ok=True)
            
            with open(self.manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2, default=str)
            
            self.logger.info(f"💾 Saved manifest: {self.manifest_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error saving manifest: {e}")
            return False
    
    def detect_changes(self, old_manifest: Dict, new_manifest: Dict) -> List[Dict[str, Any]]:
        """Detect file changes between manifests"""
        changes = []
        
        # Check for new and modified files
        for file_path, new_info in new_manifest.items():
            if file_path not in old_manifest:
                changes.append({
                    'path': file_path,
                    'type': 'added',
                    'hash': new_info['hash'],
                    'size': new_info['size'],
                    'timestamp': new_info['scanned_at']
                })
            elif old_manifest[file_path]['hash'] != new_info['hash']:
                changes.append({
                    'path': file_path,
                    'type': 'modified',
                    'old_hash': old_manifest[file_path]['hash'],
                    'new_hash': new_info['hash'],
                    'size': new_info['size'],
                    'timestamp': new_info['scanned_at']
                })
        
        # Check for deleted files
        for file_path in old_manifest:
            if file_path not in new_manifest:
                changes.append({
                    'path': file_path,
                    'type': 'deleted',
                    'hash': old_manifest[file_path]['hash'],
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
        
        return changes
    
    def log_agent_activity(self, changes: List[Dict[str, Any]]) -> bool:
        """Log file changes to agent_activity table"""
        if not self.supabase_enabled or self.dry_run:
            return True
        
        try:
            for change in changes:
                activity_data = {
                    'agent_name': 'autosync',
                    'action': 'file_change',
                    'details': json.dumps(change),
                    'status': 'detected'
                }
                
                response = requests.post(
                    f"{self.supabase_url}/rest/v1/agent_activity",
                    headers=self.supabase_headers,
                    json=activity_data,
                    timeout=10
                )
                
                if response.status_code not in [200, 201]:
                    self.logger.warning(f"⚠️ Failed to log activity for {change['path']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error logging agent activity: {e}")
            return False
    
    def create_decision_vault_entry(self, file_path: str, change_type: str) -> bool:
        """Create decision vault entry for key file changes"""
        if not self.supabase_enabled or self.dry_run:
            self.logger.info(f"🔍 [DRY RUN] Would create decision entry for: {file_path}")
            return True
        
        # Only create entries for key files
        file_name = os.path.basename(file_path)
        if file_name not in self.key_files:
            return True
        
        try:
            decision_text = f"File updated: {file_path}"
            comment = f"AutoSync detected {change_type} in key system file"
            
            decision_data = {
                'decision': decision_text,
                'type': 'technical',
                'comment': comment,
                'active': True,
                'synced': False
            }
            
            response = requests.post(
                f"{self.supabase_url}/rest/v1/decision_vault",
                headers=self.supabase_headers,
                json=decision_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                self.logger.info(f"📝 Created decision entry for key file: {file_path}")
                return True
            else:
                self.logger.warning(f"⚠️ Failed to create decision entry for {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error creating decision entry: {e}")
            return False
    
    def process_changes(self, changes: List[Dict[str, Any]]) -> bool:
        """Process detected file changes"""
        if not changes:
            self.logger.info("✅ No file changes detected")
            return True
        
        self.logger.info(f"📝 Processing {len(changes)} file changes...")
        
        for change in changes:
            change_type = change['type']
            file_path = change['path']
            
            self.logger.info(f"   {change_type.upper()}: {file_path}")
            
            # Log to agent activity
            self.log_agent_activity([change])
            
            # Create decision vault entry for key files
            if change_type in ['added', 'modified']:
                self.create_decision_vault_entry(file_path, change_type)
        
        self.changes_detected = changes
        return True
    
    def run_once(self) -> bool:
        """Run file scan once"""
        self.logger.info("🚀 Starting AutoSync file scan...")
        self.logger.info(f"📍 Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        
        # Load existing manifest
        old_manifest = self.load_existing_manifest()
        
        # Scan current state
        new_manifest = self.scan_repository()
        
        # Detect changes
        changes = self.detect_changes(old_manifest, new_manifest)
        
        # Process changes
        self.process_changes(changes)
        
        # Save new manifest
        if not self.dry_run:
            self.save_manifest(new_manifest)
        
        self.logger.info(f"✅ AutoSync completed - {len(changes)} changes detected")
        return True
    
    def run_watch(self, interval: int = 60) -> None:
        """Run continuous file watching"""
        self.logger.info(f"👁️ Starting AutoSync file watcher (interval: {interval}s)")
        self.logger.info("🛑 Press Ctrl+C to stop")
        
        try:
            while True:
                self.run_once()
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 AutoSync watcher stopped by user")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='AutoSync Files - File change detection')
    parser.add_argument('--once', action='store_true', help='Run scan once and exit')
    parser.add_argument('--watch', action='store_true', help='Run continuous watching (poll every 60s)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    parser.add_argument('--interval', type=int, default=60, help='Watch interval in seconds (default: 60)')
    
    args = parser.parse_args()
    
    try:
        autosync = FileAutoSync(dry_run=args.dry_run)
        
        if args.watch:
            autosync.run_watch(args.interval)
        else:
            success = autosync.run_once()
            sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"💥 AutoSync failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()