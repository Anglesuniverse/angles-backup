#!/usr/bin/env python3
"""
Angles AI Universe™ Log Retention & Rotation System
Comprehensive log management with archive, compression, and cleanup

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import gzip
import shutil
import logging
import glob
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import json

# Import alert manager
try:
    from alerts.notify import AlertManager
except ImportError:
    AlertManager = None

class LogManager:
    """Comprehensive log retention and rotation system"""
    
    def __init__(self):
        """Initialize log manager"""
        self.setup_logging()
        self.load_configuration()
        self.alert_manager = AlertManager() if AlertManager else None
        
        # Ensure directories exist
        os.makedirs("logs/active", exist_ok=True)
        os.makedirs("logs/archive", exist_ok=True)
        os.makedirs("logs/compressed", exist_ok=True)
        
        self.logger.info("🗂️ Angles AI Universe™ Log Manager Initialized")
    
    def setup_logging(self):
        """Setup logging for log manager"""
        self.logger = logging.getLogger('log_manager')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/active/log_manager.log"
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
    
    def load_configuration(self):
        """Load log retention configuration"""
        self.config = {
            # Retention policies (days)
            'active_logs_retention': 7,  # Keep in active for 7 days
            'archive_retention': 30,     # Keep in archive for 30 days
            'compressed_retention': 90,  # Keep compressed for 90 days
            
            # Size limits (MB)
            'max_log_size': 50,         # Rotate when log exceeds 50MB
            'max_total_size': 500,      # Alert when total size exceeds 500MB
            
            # Log patterns to manage
            'log_patterns': [
                'logs/active/*.log',
                'logs/health/*.json',
                'logs/alerts/*.json',
                'logs/schema/*.json',
                'logs/*.log'
            ],
            
            # Files to exclude from rotation
            'exclude_patterns': [
                'logs/active/log_manager.log',  # Don't rotate our own log
                'logs/health/latest_snapshot.json'  # Keep latest snapshot
            ],
            
            # Compression settings
            'compress_after_days': 7,
            'compression_level': 6
        }
        
        self.logger.info("📋 Log retention configuration loaded")
    
    def get_log_files(self) -> List[Tuple[str, os.stat_result]]:
        """Get all log files with their stats"""
        log_files = []
        
        for pattern in self.config['log_patterns']:
            for file_path in glob.glob(pattern):
                if any(exclude in file_path for exclude in self.config['exclude_patterns']):
                    continue
                
                try:
                    stat_info = os.stat(file_path)
                    log_files.append((file_path, stat_info))
                except OSError:
                    continue
        
        return log_files
    
    def check_file_age(self, file_path: str, stat_info: os.stat_result) -> int:
        """Check file age in days"""
        file_time = datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc)
        age = (datetime.now(timezone.utc) - file_time).days
        return age
    
    def check_file_size(self, stat_info: os.stat_result) -> float:
        """Check file size in MB"""
        return stat_info.st_size / (1024 * 1024)
    
    def rotate_large_files(self) -> Dict[str, Any]:
        """Rotate files that exceed size limits"""
        self.logger.info("🔄 Checking for large files to rotate...")
        
        rotation_stats = {
            'files_rotated': 0,
            'files_checked': 0,
            'total_size_freed': 0,
            'errors': []
        }
        
        log_files = self.get_log_files()
        
        for file_path, stat_info in log_files:
            rotation_stats['files_checked'] += 1
            file_size_mb = self.check_file_size(stat_info)
            
            if file_size_mb > self.config['max_log_size']:
                self.logger.info(f"🔄 Rotating large file: {file_path} ({file_size_mb:.1f}MB)")
                
                try:
                    # Create timestamped archive name
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    archive_name = f"{Path(file_path).stem}_{timestamp}.log"
                    archive_path = f"logs/archive/{archive_name}"
                    
                    # Move to archive
                    shutil.move(file_path, archive_path)
                    
                    # Create new empty log file
                    Path(file_path).touch()
                    
                    rotation_stats['files_rotated'] += 1
                    rotation_stats['total_size_freed'] += file_size_mb
                    
                    self.logger.info(f"✅ Rotated {file_path} to {archive_path}")
                    
                except Exception as e:
                    error_msg = f"Failed to rotate {file_path}: {str(e)}"
                    rotation_stats['errors'].append(error_msg)
                    self.logger.error(f"❌ {error_msg}")
        
        self.logger.info(f"🔄 Rotation complete: {rotation_stats['files_rotated']} files rotated, {rotation_stats['total_size_freed']:.1f}MB freed")
        return rotation_stats
    
    def archive_old_files(self) -> Dict[str, Any]:
        """Archive files older than retention period"""
        self.logger.info("📦 Archiving old active log files...")
        
        archive_stats = {
            'files_archived': 0,
            'files_checked': 0,
            'total_size_archived': 0,
            'errors': []
        }
        
        log_files = self.get_log_files()
        cutoff_days = self.config['active_logs_retention']
        
        for file_path, stat_info in log_files:
            if 'logs/active/' not in file_path:
                continue
                
            archive_stats['files_checked'] += 1
            age_days = self.check_file_age(file_path, stat_info)
            
            if age_days > cutoff_days:
                file_size_mb = self.check_file_size(stat_info)
                self.logger.info(f"📦 Archiving old file: {file_path} ({age_days} days old)")
                
                try:
                    # Create archive path
                    file_name = Path(file_path).name
                    timestamp = datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y%m%d')
                    archive_name = f"{Path(file_name).stem}_{timestamp}.log"
                    archive_path = f"logs/archive/{archive_name}"
                    
                    # Move to archive
                    shutil.move(file_path, archive_path)
                    
                    archive_stats['files_archived'] += 1
                    archive_stats['total_size_archived'] += file_size_mb
                    
                    self.logger.info(f"✅ Archived {file_path} to {archive_path}")
                    
                except Exception as e:
                    error_msg = f"Failed to archive {file_path}: {str(e)}"
                    archive_stats['errors'].append(error_msg)
                    self.logger.error(f"❌ {error_msg}")
        
        self.logger.info(f"📦 Archiving complete: {archive_stats['files_archived']} files archived, {archive_stats['total_size_archived']:.1f}MB")
        return archive_stats
    
    def compress_archive_files(self) -> Dict[str, Any]:
        """Compress archived files older than compression threshold"""
        self.logger.info("🗜️ Compressing old archive files...")
        
        compression_stats = {
            'files_compressed': 0,
            'files_checked': 0,
            'compression_ratio': 0,
            'space_saved': 0,
            'errors': []
        }
        
        archive_files = glob.glob("logs/archive/*.log")
        cutoff_days = self.config['compress_after_days']
        total_original_size = 0
        total_compressed_size = 0
        
        for file_path in archive_files:
            compression_stats['files_checked'] += 1
            
            try:
                stat_info = os.stat(file_path)
                age_days = self.check_file_age(file_path, stat_info)
                
                if age_days > cutoff_days:
                    file_size_mb = self.check_file_size(stat_info)
                    self.logger.info(f"🗜️ Compressing archive file: {file_path} ({age_days} days old)")
                    
                    # Create compressed file path
                    compressed_path = f"logs/compressed/{Path(file_path).name}.gz"
                    
                    # Compress file
                    with open(file_path, 'rb') as f_in:
                        with gzip.open(compressed_path, 'wb', compresslevel=self.config['compression_level']) as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Get compressed file size
                    compressed_size = os.path.getsize(compressed_path) / (1024 * 1024)
                    
                    # Remove original
                    os.remove(file_path)
                    
                    compression_stats['files_compressed'] += 1
                    total_original_size += file_size_mb
                    total_compressed_size += compressed_size
                    
                    self.logger.info(f"✅ Compressed {file_path} ({file_size_mb:.1f}MB → {compressed_size:.1f}MB)")
                    
            except Exception as e:
                error_msg = f"Failed to compress {file_path}: {str(e)}"
                compression_stats['errors'].append(error_msg)
                self.logger.error(f"❌ {error_msg}")
        
        if total_original_size > 0:
            compression_stats['compression_ratio'] = (total_compressed_size / total_original_size) * 100
            compression_stats['space_saved'] = total_original_size - total_compressed_size
        
        self.logger.info(f"🗜️ Compression complete: {compression_stats['files_compressed']} files, {compression_stats['compression_ratio']:.1f}% ratio, {compression_stats['space_saved']:.1f}MB saved")
        return compression_stats
    
    def cleanup_old_compressed_files(self) -> Dict[str, Any]:
        """Remove compressed files older than retention period"""
        self.logger.info("🗑️ Cleaning up old compressed files...")
        
        cleanup_stats = {
            'files_deleted': 0,
            'files_checked': 0,
            'space_freed': 0,
            'errors': []
        }
        
        compressed_files = glob.glob("logs/compressed/*.gz")
        cutoff_days = self.config['compressed_retention']
        
        for file_path in compressed_files:
            cleanup_stats['files_checked'] += 1
            
            try:
                stat_info = os.stat(file_path)
                age_days = self.check_file_age(file_path, stat_info)
                
                if age_days > cutoff_days:
                    file_size_mb = self.check_file_size(stat_info)
                    self.logger.info(f"🗑️ Deleting old compressed file: {file_path} ({age_days} days old)")
                    
                    os.remove(file_path)
                    
                    cleanup_stats['files_deleted'] += 1
                    cleanup_stats['space_freed'] += file_size_mb
                    
                    self.logger.info(f"✅ Deleted {file_path}")
                    
            except Exception as e:
                error_msg = f"Failed to delete {file_path}: {str(e)}"
                cleanup_stats['errors'].append(error_msg)
                self.logger.error(f"❌ {error_msg}")
        
        self.logger.info(f"🗑️ Cleanup complete: {cleanup_stats['files_deleted']} files deleted, {cleanup_stats['space_freed']:.1f}MB freed")
        return cleanup_stats
    
    def check_disk_usage(self) -> Dict[str, Any]:
        """Check total disk usage for logs"""
        disk_stats = {
            'total_size_mb': 0,
            'active_logs_mb': 0,
            'archive_logs_mb': 0,
            'compressed_logs_mb': 0,
            'health_logs_mb': 0,
            'file_counts': {},
            'warnings': []
        }
        
        directories = {
            'active': 'logs/active',
            'archive': 'logs/archive',
            'compressed': 'logs/compressed',
            'health': 'logs/health',
            'alerts': 'logs/alerts',
            'schema': 'logs/schema'
        }
        
        for category, directory in directories.items():
            if os.path.exists(directory):
                total_size = 0
                file_count = 0
                
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            size = os.path.getsize(file_path)
                            total_size += size
                            file_count += 1
                        except OSError:
                            continue
                
                size_mb = total_size / (1024 * 1024)
                disk_stats[f'{category}_logs_mb'] = size_mb
                disk_stats['file_counts'][category] = file_count
                disk_stats['total_size_mb'] += size_mb
        
        # Check for warnings
        if disk_stats['total_size_mb'] > self.config['max_total_size']:
            warning = f"Total log size ({disk_stats['total_size_mb']:.1f}MB) exceeds limit ({self.config['max_total_size']}MB)"
            disk_stats['warnings'].append(warning)
            self.logger.warning(f"⚠️ {warning}")
        
        return disk_stats
    
    def generate_log_report(self) -> Dict[str, Any]:
        """Generate comprehensive log management report"""
        self.logger.info("📊 Generating log management report...")
        
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'disk_usage': self.check_disk_usage(),
            'rotation_needed': [],
            'archive_candidates': [],
            'compression_candidates': [],
            'cleanup_candidates': []
        }
        
        # Identify files needing attention
        log_files = self.get_log_files()
        
        for file_path, stat_info in log_files:
            age_days = self.check_file_age(file_path, stat_info)
            size_mb = self.check_file_size(stat_info)
            
            # Check for rotation
            if size_mb > self.config['max_log_size']:
                report['rotation_needed'].append({
                    'file': file_path,
                    'size_mb': size_mb,
                    'age_days': age_days
                })
            
            # Check for archiving
            if 'logs/active/' in file_path and age_days > self.config['active_logs_retention']:
                report['archive_candidates'].append({
                    'file': file_path,
                    'age_days': age_days,
                    'size_mb': size_mb
                })
        
        # Check compressed files for cleanup
        compressed_files = glob.glob("logs/compressed/*.gz")
        for file_path in compressed_files:
            try:
                stat_info = os.stat(file_path)
                age_days = self.check_file_age(file_path, stat_info)
                
                if age_days > self.config['compressed_retention']:
                    report['cleanup_candidates'].append({
                        'file': file_path,
                        'age_days': age_days,
                        'size_mb': self.check_file_size(stat_info)
                    })
            except OSError:
                continue
        
        return report
    
    def run_maintenance(self) -> Dict[str, Any]:
        """Run complete log maintenance cycle"""
        self.logger.info("🧹 Starting comprehensive log maintenance...")
        self.logger.info("=" * 60)
        
        start_time = datetime.now(timezone.utc)
        
        maintenance_result = {
            'timestamp': start_time.isoformat(),
            'disk_usage_before': self.check_disk_usage(),
            'rotation_stats': {},
            'archive_stats': {},
            'compression_stats': {},
            'cleanup_stats': {},
            'disk_usage_after': {},
            'total_space_freed': 0,
            'duration_seconds': 0,
            'errors': []
        }
        
        try:
            # Step 1: Rotate large files
            self.logger.info("1️⃣ Rotating large files...")
            maintenance_result['rotation_stats'] = self.rotate_large_files()
            
            # Step 2: Archive old active files
            self.logger.info("2️⃣ Archiving old files...")
            maintenance_result['archive_stats'] = self.archive_old_files()
            
            # Step 3: Compress old archives
            self.logger.info("3️⃣ Compressing archives...")
            maintenance_result['compression_stats'] = self.compress_archive_files()
            
            # Step 4: Cleanup old compressed files
            self.logger.info("4️⃣ Cleaning up old files...")
            maintenance_result['cleanup_stats'] = self.cleanup_old_compressed_files()
            
            # Step 5: Final disk usage check
            maintenance_result['disk_usage_after'] = self.check_disk_usage()
            
            # Calculate total space freed
            space_before = maintenance_result['disk_usage_before']['total_size_mb']
            space_after = maintenance_result['disk_usage_after']['total_size_mb']
            maintenance_result['total_space_freed'] = space_before - space_after
            
            # Calculate duration
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            maintenance_result['duration_seconds'] = duration
            
            # Collect all errors
            for stats in [maintenance_result['rotation_stats'], maintenance_result['archive_stats'], 
                         maintenance_result['compression_stats'], maintenance_result['cleanup_stats']]:
                maintenance_result['errors'].extend(stats.get('errors', []))
            
            # Log summary
            self.logger.info("=" * 60)
            self.logger.info("🎉 Log maintenance complete!")
            self.logger.info(f"   Duration: {duration:.2f} seconds")
            self.logger.info(f"   Space freed: {maintenance_result['total_space_freed']:.1f}MB")
            self.logger.info(f"   Files rotated: {maintenance_result['rotation_stats']['files_rotated']}")
            self.logger.info(f"   Files archived: {maintenance_result['archive_stats']['files_archived']}")
            self.logger.info(f"   Files compressed: {maintenance_result['compression_stats']['files_compressed']}")
            self.logger.info(f"   Files deleted: {maintenance_result['cleanup_stats']['files_deleted']}")
            
            if maintenance_result['errors']:
                self.logger.warning(f"⚠️ {len(maintenance_result['errors'])} errors occurred")
            
            # Save maintenance report
            self.save_maintenance_report(maintenance_result)
            
            # Send alert if needed
            if maintenance_result['errors'] and self.alert_manager:
                self.send_maintenance_alert(maintenance_result)
            
            return maintenance_result
            
        except Exception as e:
            error_msg = f"Log maintenance failed: {str(e)}"
            maintenance_result['errors'].append(error_msg)
            self.logger.error(f"💥 {error_msg}")
            
            # Send critical alert
            if self.alert_manager:
                self.alert_manager.send_alert(
                    title="Log Management Critical Failure",
                    message=f"Log maintenance failed with error: {str(e)}",
                    severity="critical",
                    tags=['log-management', 'critical', 'failure']
                )
            
            return maintenance_result
    
    def save_maintenance_report(self, maintenance_result: Dict):
        """Save maintenance report to file"""
        try:
            os.makedirs("logs/maintenance", exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = f"logs/maintenance/maintenance_report_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(maintenance_result, f, indent=2, default=str)
            
            self.logger.info(f"📊 Maintenance report saved: {report_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save maintenance report: {str(e)}")
    
    def send_maintenance_alert(self, maintenance_result: Dict):
        """Send alert for maintenance issues"""
        if not self.alert_manager:
            return
        
        error_count = len(maintenance_result['errors'])
        title = f"Log Maintenance Alert: {error_count} errors"
        
        message = f"**Log Maintenance Report**\\n"
        message += f"**Timestamp:** {maintenance_result['timestamp']}\\n"
        message += f"**Duration:** {maintenance_result['duration_seconds']:.2f} seconds\\n"
        message += f"**Space Freed:** {maintenance_result['total_space_freed']:.1f}MB\\n\\n"
        
        message += f"**Operations:**\\n"
        message += f"- Files rotated: {maintenance_result['rotation_stats']['files_rotated']}\\n"
        message += f"- Files archived: {maintenance_result['archive_stats']['files_archived']}\\n"
        message += f"- Files compressed: {maintenance_result['compression_stats']['files_compressed']}\\n"
        message += f"- Files deleted: {maintenance_result['cleanup_stats']['files_deleted']}\\n\\n"
        
        if maintenance_result['errors']:
            message += f"**Errors ({error_count}):**\\n"
            for error in maintenance_result['errors'][:5]:  # Limit to first 5 errors
                message += f"- {error}\\n"
        
        message += "\\n**Next Actions:**\\n"
        message += "1. Review maintenance logs in `logs/active/log_manager.log`\\n"
        message += "2. Check disk space and permissions\\n"
        message += "3. Re-run maintenance: `python log_manager.py --maintain`\\n"
        
        severity = 'warning' if error_count < 5 else 'critical'
        
        self.alert_manager.send_alert(
            title=title,
            message=message,
            severity=severity,
            tags=['log-management', 'maintenance', 'errors'],
            github_labels=['log-management', 'maintenance']
        )

def main():
    """Main entry point for log manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive log retention and rotation system')
    parser.add_argument('--maintain', action='store_true', help='Run full maintenance cycle')
    parser.add_argument('--report', action='store_true', help='Generate log report only')
    parser.add_argument('--rotate', action='store_true', help='Rotate large files only')
    parser.add_argument('--archive', action='store_true', help='Archive old files only')
    parser.add_argument('--compress', action='store_true', help='Compress archive files only')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup old compressed files only')
    parser.add_argument('--status', action='store_true', help='Show disk usage status')
    
    args = parser.parse_args()
    
    try:
        log_manager = LogManager()
        
        if args.maintain:
            result = log_manager.run_maintenance()
            print(f"\\n🧹 Maintenance Results:")
            print(f"  Space freed: {result['total_space_freed']:.1f}MB")
            print(f"  Duration: {result['duration_seconds']:.2f}s")
            print(f"  Errors: {len(result['errors'])}")
        
        elif args.report:
            report = log_manager.generate_log_report()
            print(f"\\n📊 Log Report:")
            print(f"  Total size: {report['disk_usage']['total_size_mb']:.1f}MB")
            print(f"  Files needing rotation: {len(report['rotation_needed'])}")
            print(f"  Files to archive: {len(report['archive_candidates'])}")
            print(f"  Files to cleanup: {len(report['cleanup_candidates'])}")
        
        elif args.rotate:
            stats = log_manager.rotate_large_files()
            print(f"\\n🔄 Rotation Results:")
            print(f"  Files rotated: {stats['files_rotated']}")
            print(f"  Space freed: {stats['total_size_freed']:.1f}MB")
        
        elif args.archive:
            stats = log_manager.archive_old_files()
            print(f"\\n📦 Archive Results:")
            print(f"  Files archived: {stats['files_archived']}")
            print(f"  Size archived: {stats['total_size_archived']:.1f}MB")
        
        elif args.compress:
            stats = log_manager.compress_archive_files()
            print(f"\\n🗜️ Compression Results:")
            print(f"  Files compressed: {stats['files_compressed']}")
            print(f"  Compression ratio: {stats['compression_ratio']:.1f}%")
            print(f"  Space saved: {stats['space_saved']:.1f}MB")
        
        elif args.cleanup:
            stats = log_manager.cleanup_old_compressed_files()
            print(f"\\n🗑️ Cleanup Results:")
            print(f"  Files deleted: {stats['files_deleted']}")
            print(f"  Space freed: {stats['space_freed']:.1f}MB")
        
        elif args.status:
            usage = log_manager.check_disk_usage()
            print(f"\\n📊 Disk Usage Status:")
            print(f"  Total: {usage['total_size_mb']:.1f}MB")
            print(f"  Active: {usage['active_logs_mb']:.1f}MB")
            print(f"  Archive: {usage['archive_logs_mb']:.1f}MB")
            print(f"  Compressed: {usage['compressed_logs_mb']:.1f}MB")
            if usage['warnings']:
                print(f"  ⚠️ Warnings: {len(usage['warnings'])}")
        
        else:
            # Default: show status
            usage = log_manager.check_disk_usage()
            print(f"\\n📊 Log Manager Status:")
            print(f"  Total log size: {usage['total_size_mb']:.1f}MB")
            print(f"  Use --maintain to run full maintenance")
            print(f"  Use --help for all options")
    
    except KeyboardInterrupt:
        print("\\n🛑 Log manager interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Log manager failed: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()