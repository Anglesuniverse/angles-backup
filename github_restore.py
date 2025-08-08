#!/usr/bin/env python3
"""
Angles AI Universe™ GitHub Restore System
Intelligent restoration with drift detection and data integrity validation

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import tempfile
import shutil
import logging
import requests
import subprocess
import hashlib
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
import difflib

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

class GitHubRestoreSystem:
    """Comprehensive GitHub restore system with drift detection"""
    
    def __init__(self):
        """Initialize GitHub restore system"""
        self.setup_logging()
        self.load_environment()
        self.git_helper = GitHelper() if GitHelper else None
        self.alert_manager = AlertManager() if AlertManager else None
        
        # Restore configuration
        self.config = {
            'temp_dir_prefix': 'restore_temp_',
            'backup_dir': 'backups',
            'export_dir': 'export',
            'max_drift_threshold': 10,  # Max % difference before alert
            'critical_drift_threshold': 25,  # % difference for critical alert
            'dry_run_mode': False,
            'verify_checksums': True,
            'compare_with_live': True,
            'restore_tables': ['decision_vault', 'memory_log', 'agent_activity'],
            'excluded_restore_paths': [
                'logs/',
                '__pycache__/',
                '.git/',
                'node_modules/',
                '*.tmp',
                '*.temp',
                '*.log'
            ]
        }
        
        # Restore results tracking
        self.restore_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'restore_id': f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'status': 'unknown',
            'mode': 'dry_run' if self.config['dry_run_mode'] else 'live',
            'backup_source': None,
            'files_restored': 0,
            'files_skipped': 0,
            'drift_detected': False,
            'drift_analysis': {},
            'checksum_verification': {},
            'data_comparison': {},
            'errors': [],
            'warnings': [],
            'recommendations': [],
            'duration_seconds': 0
        }
        
        self.logger.info("🔄 Angles AI Universe™ GitHub Restore System Initialized")
    
    def setup_logging(self):
        """Setup logging for restore system"""
        os.makedirs("logs/restore", exist_ok=True)
        
        self.logger = logging.getLogger('github_restore')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/restore/github_restore.log"
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
        
        self.logger.info("📋 Environment loaded for GitHub restore")
    
    def clone_backup_repository(self, temp_dir: str) -> bool:
        """Clone backup repository to temporary directory"""
        try:
            if not self.env['repo_url']:
                self.logger.error("❌ REPO_URL not configured")
                return False
            
            self.logger.info(f"📥 Cloning backup repository to {temp_dir}...")
            
            # Use git clone
            cmd = ['git', 'clone', self.env['repo_url'], temp_dir]
            
            if self.env['github_token']:
                # Add authentication
                auth_url = self.env['repo_url'].replace('https://', f"https://{self.env['github_token']}@")
                cmd = ['git', 'clone', auth_url, temp_dir]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info("✅ Repository cloned successfully")
                return True
            else:
                self.logger.error(f"❌ Git clone failed: {result.stderr}")
                self.restore_results['errors'].append(f"Git clone failed: {result.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"❌ Clone operation failed: {e}")
            self.restore_results['errors'].append(f"Clone operation failed: {e}")
            return False
    
    def find_latest_backup(self, repo_dir: str) -> Optional[str]:
        """Find the latest backup archive in repository"""
        try:
            backup_dir = os.path.join(repo_dir, self.config['backup_dir'])
            
            if not os.path.exists(backup_dir):
                self.logger.error(f"❌ Backup directory not found: {backup_dir}")
                return None
            
            # Find all backup files
            backup_files = []
            for filename in os.listdir(backup_dir):
                if filename.endswith('.zip') and filename.startswith('backup_'):
                    backup_files.append(filename)
            
            if not backup_files:
                self.logger.error("❌ No backup files found")
                return None
            
            # Sort by filename (contains timestamp)
            backup_files.sort(reverse=True)
            latest_backup = backup_files[0]
            
            self.logger.info(f"📦 Latest backup found: {latest_backup}")
            return os.path.join(backup_dir, latest_backup)
        
        except Exception as e:
            self.logger.error(f"❌ Error finding backup: {e}")
            return None
    
    def verify_backup_checksums(self, backup_path: str) -> bool:
        """Verify backup archive checksums"""
        if not self.config['verify_checksums']:
            return True
        
        try:
            checksum_file = backup_path + '.checksums'
            
            if not os.path.exists(checksum_file):
                self.logger.warning("⚠️ Checksum file not found, skipping verification")
                return True
            
            self.logger.info("🔍 Verifying backup checksums...")
            
            with open(checksum_file, 'r') as f:
                stored_checksums = json.load(f)
            
            # Extract backup to temp dir for verification
            with tempfile.TemporaryDirectory() as verify_dir:
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(verify_dir)
                
                verified = 0
                failed = 0
                
                for file_path, expected_checksum in stored_checksums.items():
                    extracted_file = os.path.join(verify_dir, file_path)
                    
                    if os.path.exists(extracted_file):
                        actual_checksum = self.calculate_checksum(extracted_file)
                        
                        if actual_checksum == expected_checksum:
                            verified += 1
                        else:
                            failed += 1
                            self.logger.error(f"❌ Checksum mismatch: {file_path}")
                            self.restore_results['errors'].append(f"Checksum mismatch: {file_path}")
                    else:
                        failed += 1
                        self.logger.error(f"❌ Missing file in backup: {file_path}")
            
            self.restore_results['checksum_verification'] = {
                'verified': verified,
                'failed': failed,
                'success_rate': (verified / (verified + failed)) * 100 if (verified + failed) > 0 else 0
            }
            
            if failed == 0:
                self.logger.info(f"✅ All {verified} checksums verified successfully")
                return True
            else:
                self.logger.error(f"❌ {failed} checksum verification failures out of {verified + failed}")
                return False
        
        except Exception as e:
            self.logger.error(f"❌ Checksum verification failed: {e}")
            self.restore_results['errors'].append(f"Checksum verification failed: {e}")
            return False
    
    def calculate_checksum(self, file_path: str) -> str:
        """Calculate file checksum"""
        hash_func = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception:
            return ""
    
    def analyze_data_drift(self, backup_data: Dict[str, List], live_data: Dict[str, List]) -> Dict[str, Any]:
        """Analyze drift between backup and live data"""
        drift_analysis = {
            'total_drift_score': 0,
            'tables': {},
            'critical_issues': [],
            'recommendations': []
        }
        
        total_tables = 0
        total_drift = 0
        
        for table_name in self.config['restore_tables']:
            backup_records = backup_data.get(table_name, [])
            live_records = live_data.get(table_name, [])
            
            table_analysis = self.analyze_table_drift(table_name, backup_records, live_records)
            drift_analysis['tables'][table_name] = table_analysis
            
            total_tables += 1
            total_drift += table_analysis['drift_percentage']
            
            # Check for critical drift
            if table_analysis['drift_percentage'] > self.config['critical_drift_threshold']:
                drift_analysis['critical_issues'].append(
                    f"{table_name}: {table_analysis['drift_percentage']:.1f}% drift (critical threshold: {self.config['critical_drift_threshold']}%)"
                )
        
        # Calculate overall drift score
        drift_analysis['total_drift_score'] = total_drift / total_tables if total_tables > 0 else 0
        
        # Generate recommendations
        if drift_analysis['total_drift_score'] > self.config['critical_drift_threshold']:
            drift_analysis['recommendations'].append("CRITICAL: Consider full system restore due to high data drift")
        elif drift_analysis['total_drift_score'] > self.config['max_drift_threshold']:
            drift_analysis['recommendations'].append("WARNING: Investigate data inconsistencies before restore")
        else:
            drift_analysis['recommendations'].append("Data drift within acceptable limits")
        
        return drift_analysis
    
    def analyze_table_drift(self, table_name: str, backup_records: List[Dict], live_records: List[Dict]) -> Dict[str, Any]:
        """Analyze drift for a specific table"""
        analysis = {
            'backup_count': len(backup_records),
            'live_count': len(live_records),
            'missing_in_live': 0,
            'missing_in_backup': 0,
            'modified_records': 0,
            'drift_percentage': 0,
            'sample_differences': []
        }
        
        # Create ID-based lookups
        backup_by_id = {str(record.get('id', '')): record for record in backup_records}
        live_by_id = {str(record.get('id', '')): record for record in live_records}
        
        # Check missing records
        backup_ids = set(backup_by_id.keys())
        live_ids = set(live_by_id.keys())
        
        analysis['missing_in_live'] = len(backup_ids - live_ids)
        analysis['missing_in_backup'] = len(live_ids - backup_ids)
        
        # Check modified records
        common_ids = backup_ids & live_ids
        for record_id in list(common_ids)[:10]:  # Sample first 10
            backup_record = backup_by_id[record_id]
            live_record = live_by_id[record_id]
            
            # Compare key fields (excluding timestamps)
            backup_content = {k: v for k, v in backup_record.items() if k not in ['created_at', 'updated_at']}
            live_content = {k: v for k, v in live_record.items() if k not in ['created_at', 'updated_at']}
            
            if backup_content != live_content:
                analysis['modified_records'] += 1
                
                # Store sample difference
                if len(analysis['sample_differences']) < 3:
                    analysis['sample_differences'].append({
                        'id': record_id,
                        'backup': backup_content,
                        'live': live_content
                    })
        
        # Calculate drift percentage
        total_changes = analysis['missing_in_live'] + analysis['missing_in_backup'] + analysis['modified_records']
        total_records = max(analysis['backup_count'], analysis['live_count'])
        
        if total_records > 0:
            analysis['drift_percentage'] = (total_changes / total_records) * 100
        
        return analysis
    
    def fetch_live_data(self) -> Dict[str, List]:
        """Fetch current live data from Supabase"""
        live_data = {}
        
        if not self.env['supabase_url'] or not self.env['supabase_key']:
            self.logger.warning("⚠️ Supabase credentials not available")
            return live_data
        
        try:
            headers = {
                'apikey': self.env['supabase_key'],
                'Authorization': f"Bearer {self.env['supabase_key']}",
                'Content-Type': 'application/json'
            }
            
            for table in self.config['restore_tables']:
                try:
                    url = f"{self.env['supabase_url']}/rest/v1/{table}"
                    params = {'select': '*', 'order': 'created_at.desc'}
                    
                    response = requests.get(url, headers=headers, params=params, timeout=30)
                    
                    if response.status_code == 200:
                        live_data[table] = response.json()
                        self.logger.info(f"📊 Fetched {len(live_data[table])} live records from {table}")
                    else:
                        self.logger.error(f"❌ Failed to fetch live data from {table}: HTTP {response.status_code}")
                        live_data[table] = []
                
                except Exception as e:
                    self.logger.error(f"❌ Error fetching live data from {table}: {e}")
                    live_data[table] = []
        
        except Exception as e:
            self.logger.error(f"❌ Live data fetch failed: {e}")
        
        return live_data
    
    def load_backup_data(self, extracted_dir: str) -> Dict[str, List]:
        """Load data from backup exports"""
        backup_data = {}
        export_dir = os.path.join(extracted_dir, self.config['export_dir'])
        
        if not os.path.exists(export_dir):
            self.logger.warning("⚠️ Export directory not found in backup")
            return backup_data
        
        try:
            for filename in os.listdir(export_dir):
                if filename.endswith('.json'):
                    # Extract table name from filename
                    table_name = filename.split('_')[0]
                    
                    if table_name in self.config['restore_tables']:
                        file_path = os.path.join(export_dir, filename)
                        
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            backup_data[table_name] = data
                            self.logger.info(f"📥 Loaded {len(data)} backup records from {table_name}")
        
        except Exception as e:
            self.logger.error(f"❌ Error loading backup data: {e}")
        
        return backup_data
    
    def should_exclude_path(self, path: str) -> bool:
        """Check if path should be excluded from restore"""
        for pattern in self.config['excluded_restore_paths']:
            if pattern in path or path.endswith(pattern.replace('*', '')):
                return True
        return False
    
    def restore_files(self, extracted_dir: str, target_dir: str = '.') -> bool:
        """Restore files from extracted backup"""
        if self.config['dry_run_mode']:
            self.logger.info("🔍 DRY RUN: Simulating file restore...")
            return True
        
        try:
            restored_count = 0
            skipped_count = 0
            
            for root, dirs, files in os.walk(extracted_dir):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if not self.should_exclude_path(os.path.join(root, d))]
                
                for file in files:
                    source_path = os.path.join(root, file)
                    relative_path = os.path.relpath(source_path, extracted_dir)
                    target_path = os.path.join(target_dir, relative_path)
                    
                    if self.should_exclude_path(relative_path):
                        skipped_count += 1
                        continue
                    
                    try:
                        # Create target directory if needed
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        
                        # Copy file
                        shutil.copy2(source_path, target_path)
                        restored_count += 1
                        
                        if restored_count % 100 == 0:
                            self.logger.info(f"📁 Restored {restored_count} files...")
                    
                    except Exception as e:
                        self.logger.error(f"❌ Failed to restore {relative_path}: {e}")
                        self.restore_results['errors'].append(f"Failed to restore {relative_path}")
            
            self.restore_results['files_restored'] = restored_count
            self.restore_results['files_skipped'] = skipped_count
            
            self.logger.info(f"✅ Restored {restored_count} files, skipped {skipped_count}")
            return True
        
        except Exception as e:
            self.logger.error(f"❌ File restore failed: {e}")
            self.restore_results['errors'].append(f"File restore failed: {e}")
            return False
    
    def run_restore_verification(self, backup_source: Optional[str] = None) -> Dict[str, Any]:
        """Run complete restore verification process"""
        self.logger.info("🔄 Starting GitHub restore verification...")
        self.logger.info("=" * 60)
        
        if self.config['dry_run_mode']:
            self.logger.info("🔍 RUNNING IN DRY-RUN MODE - No actual changes will be made")
        
        start_time = datetime.now()
        
        try:
            with tempfile.TemporaryDirectory(prefix=self.config['temp_dir_prefix']) as temp_dir:
                repo_dir = os.path.join(temp_dir, 'repo')
                
                # Step 1: Clone backup repository
                self.logger.info("📥 Step 1: Cloning backup repository...")
                if not self.clone_backup_repository(repo_dir):
                    self.restore_results['status'] = 'failed'
                    return self.restore_results
                
                # Step 2: Find latest backup
                self.logger.info("🔍 Step 2: Finding latest backup...")
                backup_path = backup_source or self.find_latest_backup(repo_dir)
                
                if not backup_path:
                    self.restore_results['status'] = 'failed'
                    self.restore_results['errors'].append("No backup found")
                    return self.restore_results
                
                self.restore_results['backup_source'] = os.path.basename(backup_path)
                
                # Step 3: Verify backup checksums
                self.logger.info("🔍 Step 3: Verifying backup integrity...")
                if not self.verify_backup_checksums(backup_path):
                    self.restore_results['warnings'].append("Backup integrity verification failed")
                
                # Step 4: Extract backup
                self.logger.info("📦 Step 4: Extracting backup archive...")
                extract_dir = os.path.join(temp_dir, 'extracted')
                
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(extract_dir)
                
                # Step 5: Compare with live data (drift detection)
                if self.config['compare_with_live']:
                    self.logger.info("📊 Step 5: Analyzing data drift...")
                    
                    backup_data = self.load_backup_data(extract_dir)
                    live_data = self.fetch_live_data()
                    
                    drift_analysis = self.analyze_data_drift(backup_data, live_data)
                    self.restore_results['drift_analysis'] = drift_analysis
                    
                    if drift_analysis['total_drift_score'] > self.config['max_drift_threshold']:
                        self.restore_results['drift_detected'] = True
                        self.logger.warning(f"⚠️ Significant data drift detected: {drift_analysis['total_drift_score']:.1f}%")
                    else:
                        self.logger.info(f"✅ Data drift within acceptable limits: {drift_analysis['total_drift_score']:.1f}%")
                    
                    self.restore_results['recommendations'].extend(drift_analysis['recommendations'])
                
                # Step 6: Restore files
                self.logger.info("📁 Step 6: Restoring files...")
                if not self.restore_files(extract_dir):
                    self.restore_results['status'] = 'partial'
                else:
                    self.restore_results['status'] = 'success'
            
            # Calculate duration
            duration = datetime.now() - start_time
            self.restore_results['duration_seconds'] = duration.total_seconds()
            
            # Send alerts if needed
            self.send_restore_alert()
            
            # Final summary
            self.logger.info("\n" + "=" * 60)
            self.logger.info("🏁 RESTORE VERIFICATION COMPLETE")
            self.logger.info("=" * 60)
            self.logger.info(f"📊 SUMMARY:")
            self.logger.info(f"   Status: {self.restore_results['status'].upper()}")
            self.logger.info(f"   Mode: {self.restore_results['mode'].upper()}")
            self.logger.info(f"   Backup source: {self.restore_results['backup_source']}")
            self.logger.info(f"   Files restored: {self.restore_results['files_restored']}")
            self.logger.info(f"   Files skipped: {self.restore_results['files_skipped']}")
            self.logger.info(f"   Drift detected: {'YES' if self.restore_results['drift_detected'] else 'NO'}")
            
            if self.restore_results.get('drift_analysis'):
                drift_score = self.restore_results['drift_analysis']['total_drift_score']
                self.logger.info(f"   Data drift score: {drift_score:.1f}%")
            
            self.logger.info(f"   Errors: {len(self.restore_results['errors'])}")
            self.logger.info(f"   Duration: {self.restore_results['duration_seconds']:.1f} seconds")
            
            if self.restore_results['errors']:
                self.logger.error("❌ ERRORS ENCOUNTERED:")
                for error in self.restore_results['errors']:
                    self.logger.error(f"   • {error}")
            
            if self.restore_results['recommendations']:
                self.logger.info("💡 RECOMMENDATIONS:")
                for rec in self.restore_results['recommendations']:
                    self.logger.info(f"   • {rec}")
            
            self.logger.info("=" * 60)
            
            return self.restore_results
        
        except Exception as e:
            self.restore_results['status'] = 'failed'
            self.restore_results['errors'].append(f"Restore verification failed: {e}")
            self.logger.error(f"💥 Restore verification failed: {e}")
            return self.restore_results
    
    def send_restore_alert(self):
        """Send alert notification about restore status"""
        if not self.alert_manager:
            return
        
        try:
            status = self.restore_results['status']
            drift_detected = self.restore_results['drift_detected']
            files_restored = self.restore_results['files_restored']
            
            if status == 'success' and not drift_detected:
                title = "✅ Restore Verification Successful"
                message = f"Restore verification completed successfully!\n"
                message += f"• Files verified: {files_restored}\n"
                message += f"• Data drift: Within acceptable limits"
                severity = "info"
            elif status == 'success' and drift_detected:
                title = "⚠️ Restore Verification - Drift Detected"
                drift_score = self.restore_results['drift_analysis']['total_drift_score']
                message = f"Restore verification completed with drift warning!\n"
                message += f"• Files verified: {files_restored}\n"
                message += f"• Data drift: {drift_score:.1f}% (threshold: {self.config['max_drift_threshold']}%)"
                severity = "warning"
            else:
                title = "❌ Restore Verification Failed"
                errors = len(self.restore_results['errors'])
                message = f"Restore verification failed!\n"
                message += f"• Errors encountered: {errors}\n"
                if self.restore_results['errors']:
                    message += f"• Latest error: {self.restore_results['errors'][-1]}"
                severity = "critical"
            
            self.alert_manager.send_alert(
                title=title,
                message=message,
                severity=severity,
                tags=['restore', 'github', 'verification', 'drift-detection']
            )
            
            self.logger.info("📢 Restore alert sent")
        
        except Exception as e:
            self.logger.error(f"❌ Failed to send restore alert: {e}")

def main():
    """Main entry point for restore system"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitHub Restore System')
    parser.add_argument('--run', action='store_true', help='Run restore verification')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode (no actual restore)')
    parser.add_argument('--backup-file', type=str, help='Specific backup file to restore from')
    parser.add_argument('--no-drift-check', action='store_true', help='Skip data drift analysis')
    parser.add_argument('--no-checksum-verify', action='store_true', help='Skip checksum verification')
    parser.add_argument('--drift-threshold', type=float, default=10, help='Max drift threshold percentage')
    
    args = parser.parse_args()
    
    try:
        restore_system = GitHubRestoreSystem()
        
        # Override configuration based on args
        if args.dry_run:
            restore_system.config['dry_run_mode'] = True
        if args.no_drift_check:
            restore_system.config['compare_with_live'] = False
        if args.no_checksum_verify:
            restore_system.config['verify_checksums'] = False
        if args.drift_threshold:
            restore_system.config['max_drift_threshold'] = args.drift_threshold
        
        if args.run or not any(vars(args).values()):
            results = restore_system.run_restore_verification(args.backup_file)
            
            # Exit codes based on results
            if results['status'] == 'success':
                if results['drift_detected']:
                    sys.exit(1)  # Warning: drift detected
                else:
                    sys.exit(0)  # Success
            else:
                sys.exit(2)  # Error
        
    except KeyboardInterrupt:
        print("\n🛑 Restore verification interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Restore system failure: {e}")
        sys.exit(255)

if __name__ == "__main__":
    main()