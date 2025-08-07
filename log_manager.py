#!/usr/bin/env python3
"""
Angles AI Universe™ Log Management System
Archives logs older than 30 days and compresses them to save space

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import gzip
import shutil
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Tuple

class LogManager:
    """Automated log archival and compression system"""
    
    def __init__(self):
        """Initialize log manager"""
        self.setup_logging()
        self.active_dir = Path("logs/active")
        self.archive_dir = Path("logs/archive")
        self.retention_days = 30
        
        # Ensure directories exist
        self.active_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("📦 Angles AI Universe™ Log Manager Initialized")
        self.logger.info(f"   Active logs: {self.active_dir}")
        self.logger.info(f"   Archive logs: {self.archive_dir}")
        self.logger.info(f"   Retention period: {self.retention_days} days")
    
    def setup_logging(self):
        """Setup logging for log manager"""
        os.makedirs("logs/active", exist_ok=True)
        
        # Configure logger
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
    
    def get_old_files(self) -> List[Tuple[Path, datetime]]:
        """Get list of files older than retention period"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        old_files = []
        
        self.logger.info(f"🔍 Scanning for files older than {cutoff_date.strftime('%Y-%m-%d')}")
        
        for file_path in self.active_dir.iterdir():
            if file_path.is_file() and file_path.suffix in ['.log', '.json']:
                try:
                    # Get file modification time
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                    
                    if mtime < cutoff_date:
                        old_files.append((file_path, mtime))
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not check file {file_path}: {str(e)}")
        
        # Sort by modification time (oldest first)
        old_files.sort(key=lambda x: x[1])
        
        self.logger.info(f"📄 Found {len(old_files)} files to archive")
        return old_files
    
    def compress_file(self, source_path: Path, target_path: Path) -> bool:
        """Compress a file using gzip"""
        try:
            with open(source_path, 'rb') as f_in:
                with gzip.open(target_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Verify compression
            original_size = source_path.stat().st_size
            compressed_size = target_path.stat().st_size
            compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
            
            self.logger.info(f"✅ Compressed {source_path.name}: {original_size:,} → {compressed_size:,} bytes ({compression_ratio:.1f}% saved)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to compress {source_path}: {str(e)}")
            return False
    
    def archive_old_files(self) -> int:
        """Archive old files to compressed format"""
        old_files = self.get_old_files()
        
        if not old_files:
            self.logger.info("✅ No old files to archive")
            return 0
        
        archived_count = 0
        total_original_size = 0
        total_compressed_size = 0
        
        for file_path, mtime in old_files:
            try:
                # Create archive filename with date prefix
                date_prefix = mtime.strftime('%Y-%m-%d')
                archive_filename = f"{date_prefix}_{file_path.name}.gz"
                archive_path = self.archive_dir / archive_filename
                
                # Compress and archive
                if self.compress_file(file_path, archive_path):
                    # Track size savings
                    original_size = file_path.stat().st_size
                    compressed_size = archive_path.stat().st_size
                    total_original_size += original_size
                    total_compressed_size += compressed_size
                    
                    # Remove original file
                    file_path.unlink()
                    archived_count += 1
                    
                    self.logger.info(f"📦 Archived: {file_path.name} → {archive_filename}")
                else:
                    self.logger.error(f"❌ Failed to archive {file_path.name}")
                    
            except Exception as e:
                self.logger.error(f"❌ Error archiving {file_path}: {str(e)}")
                continue
        
        # Log summary
        if archived_count > 0:
            total_savings = (1 - total_compressed_size / total_original_size) * 100 if total_original_size > 0 else 0
            self.logger.info(f"📊 Archive Summary:")
            self.logger.info(f"   Files archived: {archived_count}")
            self.logger.info(f"   Original size: {total_original_size:,} bytes")
            self.logger.info(f"   Compressed size: {total_compressed_size:,} bytes")
            self.logger.info(f"   Space saved: {total_savings:.1f}%")
        
        return archived_count
    
    def cleanup_old_archives(self, archive_retention_days: int = 365) -> int:
        """Clean up archive files older than specified days"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=archive_retention_days)
        cleaned_count = 0
        
        self.logger.info(f"🧹 Cleaning archives older than {cutoff_date.strftime('%Y-%m-%d')}")
        
        for archive_path in self.archive_dir.iterdir():
            if archive_path.is_file() and archive_path.suffix == '.gz':
                try:
                    mtime = datetime.fromtimestamp(archive_path.stat().st_mtime, tz=timezone.utc)
                    
                    if mtime < cutoff_date:
                        archive_path.unlink()
                        cleaned_count += 1
                        self.logger.info(f"🗑️ Removed old archive: {archive_path.name}")
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not clean archive {archive_path}: {str(e)}")
        
        if cleaned_count > 0:
            self.logger.info(f"✅ Cleaned {cleaned_count} old archive files")
        else:
            self.logger.info("✅ No old archives to clean")
        
        return cleaned_count
    
    def get_storage_summary(self) -> dict:
        """Get storage summary for active and archived logs"""
        try:
            active_files = list(self.active_dir.glob('*'))
            archive_files = list(self.archive_dir.glob('*.gz'))
            
            active_size = sum(f.stat().st_size for f in active_files if f.is_file())
            archive_size = sum(f.stat().st_size for f in archive_files if f.is_file())
            
            summary = {
                'active_files': len(active_files),
                'active_size_bytes': active_size,
                'archive_files': len(archive_files),
                'archive_size_bytes': archive_size,
                'total_size_bytes': active_size + archive_size
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get storage summary: {str(e)}")
            return {}
    
    def run_log_management(self) -> bool:
        """Run complete log management process"""
        self.logger.info("🚀 Starting Log Management Process")
        self.logger.info("=" * 60)
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get initial storage summary
            initial_summary = self.get_storage_summary()
            
            self.logger.info("📊 Initial Storage Status:")
            self.logger.info(f"   Active files: {initial_summary.get('active_files', 0)}")
            self.logger.info(f"   Active size: {initial_summary.get('active_size_bytes', 0):,} bytes")
            self.logger.info(f"   Archive files: {initial_summary.get('archive_files', 0)}")
            self.logger.info(f"   Archive size: {initial_summary.get('archive_size_bytes', 0):,} bytes")
            
            # Archive old files
            archived_count = self.archive_old_files()
            
            # Clean up old archives (keep for 1 year)
            cleaned_count = self.cleanup_old_archives(archive_retention_days=365)
            
            # Get final storage summary
            final_summary = self.get_storage_summary()
            
            # Calculate duration
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Log final summary
            self.logger.info("=" * 60)
            self.logger.info("🎉 Log Management Completed")
            self.logger.info(f"   Duration: {duration:.2f} seconds")
            self.logger.info(f"   Files archived: {archived_count}")
            self.logger.info(f"   Archives cleaned: {cleaned_count}")
            self.logger.info(f"   Final active files: {final_summary.get('active_files', 0)}")
            self.logger.info(f"   Final archive files: {final_summary.get('archive_files', 0)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"💥 Log management failed: {str(e)}")
            return False

def main():
    """Main entry point for log manager"""
    try:
        log_manager = LogManager()
        success = log_manager.run_log_management()
        
        if success:
            print("\n🎉 Log management completed successfully!")
            sys.exit(0)
        else:
            print("\n⚠️ Log management completed with issues")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Log management interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Log management failed: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()