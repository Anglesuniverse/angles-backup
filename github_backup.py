#!/usr/bin/env python3
"""
Angles AI Universe™ GitHub Backup System
High-performance backup with SHA256 checksums, compression, and sanitization

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import gzip
import hashlib
import tempfile
import shutil
import logging
import requests
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import zipfile
import base64

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from git_helpers import GitHelper
except ImportError:
    GitHelper = None

try:
    from alerts.notify import AlertManager
except ImportError:
    AlertManager = None

class GitHubBackupSystem:
    """Comprehensive GitHub backup system with checksums and sanitization"""
    
    def __init__(self):
        """Initialize GitHub backup system"""
        self.setup_logging()
        self.load_environment()
        self.git_helper = GitHelper() if GitHelper else None
        self.alert_manager = AlertManager() if AlertManager else None
        
        # Backup configuration
        self.config = {
            'export_dir': 'export',
            'backup_dir': 'backups',
            'compression_level': 6,
            'max_file_size_mb': 100,
            'checksum_algorithm': 'sha256',
            'retention_days': 30,
            'batch_size': 50,
            'sanitize_secrets': True,
            'include_logs': False  # Exclude logs by default for security
        }
        
        # Secret patterns to sanitize
        self.secret_patterns = [
            r'sk-[a-zA-Z0-9]{48,}',  # OpenAI API keys
            r'ghp_[a-zA-Z0-9]{36}',  # GitHub personal access tokens
            r'["\']?SUPABASE_[A-Z_]*["\']?\s*[:=]\s*["\']?[a-zA-Z0-9._-]+["\']?',
            r'["\']?NOTION_[A-Z_]*["\']?\s*[:=]\s*["\']?[a-zA-Z0-9._-]+["\']?',
            r'["\']?GITHUB_[A-Z_]*["\']?\s*[:=]\s*["\']?[a-zA-Z0-9._-]+["\']?',
            r'password\s*[:=]\s*["\']?[^"\'\\s]+["\']?',
            r'secret\s*[:=]\s*["\']?[^"\'\\s]+["\']?',
            r'token\s*[:=]\s*["\']?[^"\'\\s]+["\']?'
        ]
        
        # Backup results tracking
        self.backup_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'backup_id': f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'status': 'unknown',
            'files_backed_up': 0,
            'total_size_mb': 0,
            'compressed_size_mb': 0,
            'compression_ratio': 0,
            'checksums': {},
            'sanitized_files': [],
            'errors': [],
            'warnings': [],
            'duration_seconds': 0
        }
        
        self.logger.info("📦 Angles AI Universe™ GitHub Backup System Initialized")
    
    def setup_logging(self):
        """Setup logging for backup system"""
        os.makedirs("logs/backup", exist_ok=True)
        
        self.logger = logging.getLogger('github_backup')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/backup/github_backup.log"
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
        """Load environment variables"""
        self.env = {
            'github_token': os.getenv('GITHUB_TOKEN'),
            'repo_url': os.getenv('REPO_URL'),
            'supabase_url': os.getenv('SUPABASE_URL'),
            'supabase_key': os.getenv('SUPABASE_KEY')
        }
        
        if not self.env['github_token']:
            self.logger.warning("⚠️ GITHUB_TOKEN not set - Git operations may fail")
        
        self.logger.info("📋 Environment loaded for GitHub backup")
    
    def calculate_checksum(self, file_path: str, algorithm: str = 'sha256') -> str:
        """Calculate file checksum"""
        hash_func = hashlib.new(algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate checksum for {file_path}: {e}")
            return ""
    
    def sanitize_content(self, content: str, file_path: str) -> tuple[str, bool]:
        """Sanitize content by removing secrets"""
        if not self.config['sanitize_secrets']:
            return content, False
        
        original_content = content
        sanitized = False
        
        import re
        for pattern in self.secret_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                content = re.sub(pattern, '[SANITIZED]', content, flags=re.IGNORECASE)
                sanitized = True
        
        if sanitized:
            self.backup_results['sanitized_files'].append(file_path)
            self.logger.warning(f"🔒 Sanitized secrets in {file_path}")
        
        return content, sanitized
    
    def should_exclude_file(self, file_path: str) -> bool:
        """Check if file should be excluded from backup"""
        exclude_patterns = [
            '__pycache__',
            '.pyc',
            '.env',
            '.env.local',
            '.env.production',
            'node_modules',
            '.git',
            '*.tmp',
            '*.temp',
            '*.log',
            'sync_queue.jsonl',
            '*.lock',
            '*.pid'
        ]
        
        # Skip logs if configured
        if not self.config['include_logs'] and 'logs/' in file_path:
            return True
        
        for pattern in exclude_patterns:
            if pattern in file_path or file_path.endswith(pattern.replace('*', '')):
                return True
        
        return False
    
    def export_supabase_data(self) -> bool:
        """Export data from Supabase tables"""
        if not self.env['supabase_url'] or not self.env['supabase_key']:
            self.logger.warning("⚠️ Supabase credentials not available, skipping data export")
            return True
        
        try:
            headers = {
                'apikey': self.env['supabase_key'],
                'Authorization': f"Bearer {self.env['supabase_key']}",
                'Content-Type': 'application/json'
            }
            
            tables = ['decision_vault', 'memory_log', 'agent_activity', 'memory_backups']
            os.makedirs(self.config['export_dir'], exist_ok=True)
            
            for table in tables:
                try:
                    url = f"{self.env['supabase_url']}/rest/v1/{table}"
                    params = {'select': '*', 'order': 'created_at.desc'}
                    
                    response = requests.get(url, headers=headers, params=params, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Export as JSON
                        export_file = f"{self.config['export_dir']}/{table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        with open(export_file, 'w') as f:
                            json.dump(data, f, indent=2, default=str)
                        
                        # Calculate checksum
                        checksum = self.calculate_checksum(export_file)
                        self.backup_results['checksums'][export_file] = checksum
                        
                        self.logger.info(f"✅ Exported {len(data)} records from {table}")
                    else:
                        self.logger.error(f"❌ Failed to export {table}: HTTP {response.status_code}")
                        self.backup_results['errors'].append(f"Failed to export {table}")
                
                except Exception as e:
                    self.logger.error(f"❌ Error exporting {table}: {e}")
                    self.backup_results['errors'].append(f"Error exporting {table}: {e}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"❌ Supabase export failed: {e}")
            self.backup_results['errors'].append(f"Supabase export failed: {e}")
            return False
    
    def create_backup_archive(self) -> Optional[str]:
        """Create compressed backup archive with checksums"""
        try:
            backup_filename = f"{self.backup_results['backup_id']}.zip"
            backup_path = os.path.join(self.config['backup_dir'], backup_filename)
            
            os.makedirs(self.config['backup_dir'], exist_ok=True)
            
            total_size = 0
            files_added = 0
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=self.config['compression_level']) as zipf:
                
                # Add project files
                for root, dirs, files in os.walk('.'):
                    # Skip backup directory and other excluded paths
                    dirs[:] = [d for d in dirs if not self.should_exclude_file(os.path.join(root, d))]
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        if self.should_exclude_file(file_path):
                            continue
                        
                        try:
                            # Check file size
                            file_size = os.path.getsize(file_path)
                            if file_size > self.config['max_file_size_mb'] * 1024 * 1024:
                                self.logger.warning(f"⚠️ Skipping large file: {file_path} ({file_size / (1024*1024):.1f}MB)")
                                continue
                            
                            # Read and potentially sanitize content
                            if file_path.endswith(('.py', '.js', '.json', '.md', '.txt', '.yml', '.yaml')):
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                
                                sanitized_content, was_sanitized = self.sanitize_content(content, file_path)
                                zipf.writestr(file_path, sanitized_content)
                            else:
                                zipf.write(file_path, file_path)
                            
                            # Calculate checksum of original file
                            checksum = self.calculate_checksum(file_path)
                            self.backup_results['checksums'][file_path] = checksum
                            
                            total_size += file_size
                            files_added += 1
                            
                        except Exception as e:
                            self.logger.error(f"❌ Failed to add {file_path} to backup: {e}")
                            self.backup_results['errors'].append(f"Failed to backup {file_path}")
            
            # Calculate compression stats
            compressed_size = os.path.getsize(backup_path)
            self.backup_results['files_backed_up'] = files_added
            self.backup_results['total_size_mb'] = total_size / (1024 * 1024)
            self.backup_results['compressed_size_mb'] = compressed_size / (1024 * 1024)
            self.backup_results['compression_ratio'] = (1 - compressed_size / total_size) * 100 if total_size > 0 else 0
            
            # Create checksum manifest
            manifest_path = backup_path + '.checksums'
            with open(manifest_path, 'w') as f:
                json.dump(self.backup_results['checksums'], f, indent=2)
            
            self.logger.info(f"✅ Created backup archive: {backup_filename}")
            self.logger.info(f"   Files: {files_added}")
            self.logger.info(f"   Original size: {self.backup_results['total_size_mb']:.1f}MB")
            self.logger.info(f"   Compressed size: {self.backup_results['compressed_size_mb']:.1f}MB")
            self.logger.info(f"   Compression ratio: {self.backup_results['compression_ratio']:.1f}%")
            
            return backup_path
        
        except Exception as e:
            self.logger.error(f"❌ Failed to create backup archive: {e}")
            self.backup_results['errors'].append(f"Archive creation failed: {e}")
            return None
    
    def push_to_github(self, backup_path: str) -> bool:
        """Push backup to GitHub repository"""
        if not self.git_helper:
            self.logger.warning("⚠️ Git helper not available, attempting basic Git operations")
            return self.basic_git_push(backup_path)
        
        try:
            # Use GitHelper for safe commit and push
            files_to_commit = [backup_path, backup_path + '.checksums']
            commit_message = f"Automated backup {self.backup_results['backup_id']}"
            
            result = self.git_helper.safe_commit_and_push(files_to_commit, commit_message)
            
            if result.get('success', False):
                self.logger.info("✅ Backup pushed to GitHub successfully")
                return True
            else:
                error_msg = result.get('error', 'Unknown error')
                self.logger.error(f"❌ GitHub push failed: {error_msg}")
                self.backup_results['errors'].append(f"GitHub push failed: {error_msg}")
                return False
        
        except Exception as e:
            self.logger.error(f"❌ Git helper error: {e}")
            self.backup_results['errors'].append(f"Git helper error: {e}")
            return False
    
    def basic_git_push(self, backup_path: str) -> bool:
        """Basic Git operations without GitHelper"""
        try:
            files_to_add = [backup_path, backup_path + '.checksums']
            
            # Git add
            for file_path in files_to_add:
                result = subprocess.run(['git', 'add', file_path], capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    self.logger.error(f"❌ Git add failed for {file_path}: {result.stderr}")
                    return False
            
            # Git commit
            commit_msg = f"Automated backup {self.backup_results['backup_id']}"
            result = subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                self.logger.error(f"❌ Git commit failed: {result.stderr}")
                return False
            
            # Git push
            result = subprocess.run(['git', 'push'], capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                self.logger.info("✅ Basic Git push successful")
                return True
            else:
                self.logger.error(f"❌ Git push failed: {result.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"❌ Basic Git operations failed: {e}")
            return False
    
    def cleanup_old_backups(self):
        """Remove old backup files based on retention policy"""
        try:
            if not os.path.exists(self.config['backup_dir']):
                return
            
            cutoff_date = datetime.now() - timedelta(days=self.config['retention_days'])
            removed_count = 0
            
            for filename in os.listdir(self.config['backup_dir']):
                file_path = os.path.join(self.config['backup_dir'], filename)
                
                if os.path.isfile(file_path):
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_mtime < cutoff_date:
                        try:
                            os.remove(file_path)
                            removed_count += 1
                            self.logger.info(f"🗑️ Removed old backup: {filename}")
                        except Exception as e:
                            self.logger.error(f"❌ Failed to remove {filename}: {e}")
            
            if removed_count > 0:
                self.logger.info(f"✅ Cleaned up {removed_count} old backup files")
        
        except Exception as e:
            self.logger.error(f"❌ Backup cleanup failed: {e}")
    
    def send_backup_alert(self):
        """Send alert notification about backup status"""
        if not self.alert_manager:
            return
        
        try:
            status = self.backup_results['status']
            files_count = self.backup_results['files_backed_up']
            size_mb = self.backup_results['compressed_size_mb']
            errors = len(self.backup_results['errors'])
            
            if status == 'success':
                message = f"Backup completed successfully!\n"
                message += f"• Files backed up: {files_count}\n"
                message += f"• Compressed size: {size_mb:.1f}MB\n"
                message += f"• Compression ratio: {self.backup_results['compression_ratio']:.1f}%"
                
                if self.backup_results['sanitized_files']:
                    message += f"\n• Sanitized files: {len(self.backup_results['sanitized_files'])}"
                
                severity = "info"
                title = "✅ GitHub Backup Successful"
            else:
                message = f"Backup failed with {errors} errors!\n"
                message += f"• Files processed: {files_count}\n"
                if self.backup_results['errors']:
                    message += f"• Latest error: {self.backup_results['errors'][-1]}"
                
                severity = "critical"
                title = "❌ GitHub Backup Failed"
            
            self.alert_manager.send_alert(
                title=title,
                message=message,
                severity=severity,
                tags=['backup', 'github', 'automated']
            )
            
            self.logger.info("📢 Backup alert sent")
        
        except Exception as e:
            self.logger.error(f"❌ Failed to send backup alert: {e}")
    
    def run_full_backup(self) -> Dict[str, Any]:
        """Run complete backup process"""
        self.logger.info("🚀 Starting full GitHub backup process...")
        self.logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Export Supabase data
            self.logger.info("📤 Step 1: Exporting Supabase data...")
            if not self.export_supabase_data():
                self.backup_results['warnings'].append("Supabase export had issues")
            
            # Step 2: Create backup archive
            self.logger.info("📦 Step 2: Creating backup archive...")
            backup_path = self.create_backup_archive()
            
            if not backup_path:
                self.backup_results['status'] = 'failed'
                self.backup_results['errors'].append("Failed to create backup archive")
                return self.backup_results
            
            # Step 3: Push to GitHub
            self.logger.info("🚀 Step 3: Pushing to GitHub...")
            if self.push_to_github(backup_path):
                self.backup_results['status'] = 'success'
            else:
                self.backup_results['status'] = 'partial'
                self.backup_results['errors'].append("GitHub push failed")
            
            # Step 4: Cleanup old backups
            self.logger.info("🗑️ Step 4: Cleaning up old backups...")
            self.cleanup_old_backups()
            
            # Calculate duration
            duration = datetime.now() - start_time
            self.backup_results['duration_seconds'] = duration.total_seconds()
            
            # Step 5: Send alerts
            self.send_backup_alert()
            
            # Final summary
            self.logger.info("\n" + "=" * 60)
            self.logger.info("🏁 BACKUP PROCESS COMPLETE")
            self.logger.info("=" * 60)
            self.logger.info(f"📊 SUMMARY:")
            self.logger.info(f"   Status: {self.backup_results['status'].upper()}")
            self.logger.info(f"   Files backed up: {self.backup_results['files_backed_up']}")
            self.logger.info(f"   Total size: {self.backup_results['total_size_mb']:.1f}MB")
            self.logger.info(f"   Compressed size: {self.backup_results['compressed_size_mb']:.1f}MB")
            self.logger.info(f"   Compression ratio: {self.backup_results['compression_ratio']:.1f}%")
            self.logger.info(f"   Sanitized files: {len(self.backup_results['sanitized_files'])}")
            self.logger.info(f"   Errors: {len(self.backup_results['errors'])}")
            self.logger.info(f"   Duration: {self.backup_results['duration_seconds']:.1f} seconds")
            
            if self.backup_results['errors']:
                self.logger.error("❌ ERRORS ENCOUNTERED:")
                for error in self.backup_results['errors']:
                    self.logger.error(f"   • {error}")
            
            if self.backup_results['warnings']:
                self.logger.warning("⚠️ WARNINGS:")
                for warning in self.backup_results['warnings']:
                    self.logger.warning(f"   • {warning}")
            
            self.logger.info("=" * 60)
            
            return self.backup_results
        
        except Exception as e:
            self.backup_results['status'] = 'failed'
            self.backup_results['errors'].append(f"Backup process failed: {e}")
            self.logger.error(f"💥 Backup process failed: {e}")
            return self.backup_results

def main():
    """Main entry point for backup system"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitHub Backup System')
    parser.add_argument('--run', action='store_true', help='Run full backup process')
    parser.add_argument('--export-only', action='store_true', help='Export Supabase data only')
    parser.add_argument('--include-logs', action='store_true', help='Include log files in backup')
    parser.add_argument('--no-sanitize', action='store_true', help='Disable secret sanitization')
    parser.add_argument('--retention-days', type=int, default=30, help='Backup retention period in days')
    
    args = parser.parse_args()
    
    try:
        backup_system = GitHubBackupSystem()
        
        # Override configuration based on args
        if args.include_logs:
            backup_system.config['include_logs'] = True
        if args.no_sanitize:
            backup_system.config['sanitize_secrets'] = False
        if args.retention_days:
            backup_system.config['retention_days'] = args.retention_days
        
        if args.export_only:
            backup_system.export_supabase_data()
        elif args.run:
            results = backup_system.run_full_backup()
            exit_code = 0 if results['status'] == 'success' else 1
            sys.exit(exit_code)
        else:
            # Default: run full backup
            results = backup_system.run_full_backup()
            exit_code = 0 if results['status'] == 'success' else 1
            sys.exit(exit_code)
    
    except KeyboardInterrupt:
        print("\n🛑 Backup interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Backup system failure: {e}")
        sys.exit(255)

if __name__ == "__main__":
    main()