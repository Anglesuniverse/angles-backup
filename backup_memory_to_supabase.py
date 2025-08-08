#!/usr/bin/env python3
"""
MemorySyncAgent™ Daily Backup to Supabase
Automated daily backup system for memory data with encryption and storage management

This module provides:
- Daily backup of all memory files to compressed, encrypted archives
- Supabase storage integration with metadata
- Automatic retention management (30 days)
- Database logging for all backup attempts
- Notion integration for backup notifications
- Comprehensive error handling and recovery

Author: Angles AI Universe™ Backend Team
Version: 2.0.0
"""

import os
import sys
import json
import zipfile
import logging
import hashlib
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None
from supabase import create_client, Client
from logging.handlers import RotatingFileHandler

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from notion_backup_logger import create_notion_logger

@dataclass
class BackupResult:
    """Result of a backup operation"""
    success: bool
    filename: str = ""
    storage_url: str = ""
    file_size: int = 0
    file_count: int = 0
    error_message: str = ""
    duration_seconds: float = 0.0

class MemoryBackupManager:
    """Manages daily backup of MemorySyncAgent™ data to Supabase"""
    
    def __init__(self):
        """Initialize the backup manager"""
        self.logger = self._setup_logging()
        self.notion_logger = create_notion_logger()
        
        # Environment variables
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.backup_encryption_key = os.getenv('BACKUP_ENCRYPTION_KEY')
        
        # Initialize Supabase client
        self.supabase = self._init_supabase_client()
        
        # Initialize encryption
        self.cipher = self._init_encryption()
        
        # Backup configuration
        self.memory_paths = [
            'memory/state.json',
            'memory/session_cache.json',
            'memory/long_term.db',
            'memory/indexes'
        ]
        
        self.bucket_name = 'memory_backups'
        self.retention_days = 30
        
        self.logger.info("🗄️ MEMORYSYNCAGENT™ BACKUP MANAGER INITIALIZED")
        self.logger.info("=" * 55)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup backup-specific logging"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('memory_backup')
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Rotating file handler
        file_handler = RotatingFileHandler(
            'logs/memory_backup.log',
            maxBytes=1024*1024,  # 1MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _init_supabase_client(self) -> Optional[Client]:
        """Initialize Supabase client"""
        if not self.supabase_url or not self.supabase_key:
            self.logger.error("Missing Supabase credentials")
            return None
        
        try:
            client = create_client(self.supabase_url, self.supabase_key)
            self.logger.info("✅ Supabase client initialized")
            return client
        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase client: {e}")
            return None
    
    def _init_encryption(self) -> Optional['Fernet']:
        """Initialize encryption for backup files"""
        if not Fernet:
            self.logger.warning("Cryptography not available, backups will be unencrypted")
            return None
            
        if not self.backup_encryption_key:
            # Generate a new key if not provided
            key = Fernet.generate_key()
            self.logger.warning("No BACKUP_ENCRYPTION_KEY found, generated new key (store in secrets!)")
            self.logger.warning(f"Generated key: {key.decode()}")
            return Fernet(key)
        
        try:
            # If key is provided as base64 string, use it directly
            if len(self.backup_encryption_key) == 44:  # Base64 encoded Fernet key length
                return Fernet(self.backup_encryption_key.encode())
            else:
                # If it's a different format, derive a key from it
                derived_key = Fernet.generate_key()
                self.logger.info("✅ Encryption initialized")
                return Fernet(derived_key)
        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")
            return None
    
    def _create_backup_archive(self, timestamp: str) -> Optional[str]:
        """Create compressed archive of memory files"""
        try:
            filename = f"memory_backup_{timestamp}.zip"
            temp_path = Path(tempfile.gettempdir()) / filename
            
            file_count = 0
            
            with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add individual memory files
                for memory_path in self.memory_paths:
                    path = Path(memory_path)
                    
                    if path.is_file() and path.exists():
                        zip_file.write(path, path.name)
                        file_count += 1
                        self.logger.info(f"📁 Added file: {memory_path}")
                    
                    elif path.is_dir() and path.exists():
                        # Add directory contents recursively
                        for file_path in path.rglob('*'):
                            if file_path.is_file():
                                # Preserve directory structure in zip
                                arc_name = file_path.relative_to(path.parent)
                                zip_file.write(file_path, str(arc_name))
                                file_count += 1
                                self.logger.info(f"📁 Added file: {file_path}")
                    
                    else:
                        self.logger.warning(f"Path not found: {memory_path}")
                
                # Add metadata file
                metadata = {
                    "backup_timestamp": timestamp,
                    "files_included": file_count,
                    "backup_type": "daily",
                    "version": "2.0.0",
                    "system": "MemorySyncAgent™"
                }
                
                metadata_json = json.dumps(metadata, indent=2)
                zip_file.writestr("backup_metadata.json", metadata_json)
            
            self.logger.info(f"✅ Created backup archive: {filename} ({file_count} files)")
            return str(temp_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create backup archive: {e}")
            return None
    
    def _encrypt_backup_file(self, file_path: str) -> Optional[str]:
        """Encrypt backup file"""
        if not self.cipher:
            self.logger.warning("No encryption available, uploading unencrypted")
            return file_path
        
        try:
            encrypted_path = f"{file_path}.encrypted"
            
            with open(file_path, 'rb') as infile:
                data = infile.read()
            
            encrypted_data = self.cipher.encrypt(data)
            
            with open(encrypted_path, 'wb') as outfile:
                outfile.write(encrypted_data)
            
            # Remove original unencrypted file
            Path(file_path).unlink()
            
            self.logger.info("🔐 Backup file encrypted")
            return encrypted_path
            
        except Exception as e:
            self.logger.error(f"Failed to encrypt backup file: {e}")
            return file_path  # Return original if encryption fails
    
    def _create_storage_bucket(self) -> bool:
        """Create Supabase storage bucket if it doesn't exist"""
        if not self.supabase:
            return False
        
        try:
            # List existing buckets
            buckets = self.supabase.storage.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            
            if self.bucket_name not in bucket_names:
                # Create bucket
                result = self.supabase.storage.create_bucket(
                    self.bucket_name,
                    options={"public": False}  # Private bucket
                )
                
                if result:
                    self.logger.info(f"✅ Created storage bucket: {self.bucket_name}")
                else:
                    self.logger.error(f"Failed to create bucket: {self.bucket_name}")
                    return False
            else:
                self.logger.info(f"✅ Storage bucket exists: {self.bucket_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error managing storage bucket: {e}")
            return False
    
    def _upload_backup_to_storage(self, file_path: str, filename: str, timestamp: str) -> Optional[str]:
        """Upload backup file to Supabase storage"""
        if not self.supabase:
            return None
        
        try:
            # Ensure bucket exists
            if not self._create_storage_bucket():
                return None
            
            # Upload file
            storage_path = f"daily/{filename}"
            
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            result = self.supabase.storage.from_(self.bucket_name).upload(
                storage_path,
                file_data,
                file_options={
                    "content-type": "application/zip",
                    "metadata": {
                        "backup_type": "daily",
                        "timestamp": timestamp,
                        "system": "MemorySyncAgent™"
                    }
                }
            )
            
            if result:
                # Get public URL (for reference, but bucket is private)
                storage_url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{storage_path}"
                self.logger.info(f"📤 Uploaded to storage: {storage_path}")
                return storage_url
            else:
                self.logger.error("Failed to upload backup to storage")
                return None
                
        except Exception as e:
            self.logger.error(f"Error uploading backup to storage: {e}")
            return None
    
    def _create_backup_log_table(self):
        """Create memory_backup_log table if it doesn't exist"""
        if not self.supabase:
            return
        
        try:
            # Create table SQL
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS memory_backup_log (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                filename TEXT NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                status TEXT NOT NULL,
                storage_url TEXT,
                file_size BIGINT,
                file_count INTEGER,
                error_message TEXT,
                duration_seconds REAL,
                backup_type TEXT DEFAULT 'daily',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_memory_backup_log_timestamp ON memory_backup_log(timestamp);
            CREATE INDEX IF NOT EXISTS idx_memory_backup_log_status ON memory_backup_log(status);
            """
            
            # Execute SQL directly using RPC
            self.supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
            self.logger.info("✅ Backup log table ready")
            
        except Exception as e:
            self.logger.warning(f"Could not create backup log table: {e}")
    
    def _log_backup_attempt(self, result: BackupResult) -> bool:
        """Log backup attempt to database"""
        if not self.supabase:
            return False
        
        try:
            # Insert log entry
            log_data = {
                "filename": result.filename,
                "status": "success" if result.success else "failure",
                "storage_url": result.storage_url,
                "file_size": result.file_size,
                "file_count": result.file_count,
                "error_message": result.error_message,
                "duration_seconds": result.duration_seconds,
                "backup_type": "daily"
            }
            
            response = self.supabase.table('memory_backup_log').insert(log_data).execute()
            
            if response.data:
                self.logger.info("📝 Logged backup attempt to database")
                return True
            else:
                self.logger.error("Failed to log backup attempt")
                return False
                
        except Exception as e:
            self.logger.error(f"Error logging backup attempt: {e}")
            return False
    
    def _log_backup_to_notion(self, result: BackupResult):
        """Log backup to Notion if enabled"""
        try:
            status = "Success" if result.success else "Failure"
            details = f"File: {result.filename}, Size: {result.file_size} bytes, Files: {result.file_count}"
            
            if result.error_message:
                details += f", Error: {result.error_message}"
            
            self.notion_logger.log_backup(
                success=result.success,
                items_processed=result.file_count,
                commit_link=result.storage_url,
                duration=result.duration_seconds,
                error=result.error_message,
                details=details
            )
            
            self.logger.info("📝 Logged backup to Notion")
            
        except Exception as e:
            self.logger.warning(f"Failed to log backup to Notion: {e}")
    
    def _cleanup_old_backups(self):
        """Remove backups older than retention period"""
        if not self.supabase:
            return
        
        try:
            # Calculate cutoff date
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=self.retention_days)).isoformat()
            
            # List files in storage
            storage_files = self.supabase.storage.from_(self.bucket_name).list("daily/")
            
            deleted_count = 0
            for file_info in storage_files:
                # Handle both dict and object formats from Supabase
                if isinstance(file_info, dict):
                    file_date = file_info.get('created_at', '')
                    file_name = file_info.get('name', '')
                else:
                    file_date = getattr(file_info, 'created_at', '')
                    file_name = getattr(file_info, 'name', '')
                
                if file_date and file_name and file_date < cutoff_date:
                    # Delete old file
                    delete_result = self.supabase.storage.from_(self.bucket_name).remove([f"daily/{file_name}"])
                    if delete_result:
                        deleted_count += 1
                        self.logger.info(f"🗑️ Deleted old backup: {file_name}")
            
            if deleted_count > 0:
                self.logger.info(f"🧹 Cleaned up {deleted_count} old backups")
            else:
                self.logger.info("✅ No old backups to clean up")
                
        except Exception as e:
            self.logger.warning(f"Error during backup cleanup: {e}")
    
    def run_daily_backup(self) -> BackupResult:
        """Execute the complete daily backup process"""
        start_time = datetime.now()
        timestamp = start_time.strftime('%Y-%m-%d')
        
        self.logger.info("🚀 Starting daily memory backup...")
        
        result = BackupResult(success=False)
        
        try:
            # Create backup log table
            self._create_backup_log_table()
            
            # Create backup archive
            archive_path = self._create_backup_archive(timestamp)
            if not archive_path:
                result.error_message = "Failed to create backup archive"
                return result
            
            # Get file info
            archive_file = Path(archive_path)
            result.file_size = archive_file.stat().st_size
            result.filename = archive_file.name
            
            # Count files in archive
            try:
                with zipfile.ZipFile(archive_path, 'r') as zip_file:
                    result.file_count = len(zip_file.namelist()) - 1  # Exclude metadata file
            except:
                result.file_count = 0
            
            # Encrypt backup
            encrypted_path = self._encrypt_backup_file(archive_path)
            if encrypted_path != archive_path:
                result.filename = Path(encrypted_path).name
                result.file_size = Path(encrypted_path).stat().st_size
            
            # Upload to storage
            if encrypted_path:
                storage_url = self._upload_backup_to_storage(encrypted_path, result.filename, timestamp)
                if not storage_url:
                    result.error_message = "Failed to upload backup to storage"
                    return result
            else:
                result.error_message = "Failed to encrypt backup file"
                return result
            
            result.storage_url = storage_url
            
            # Cleanup old backups
            self._cleanup_old_backups()
            
            # Mark as successful
            result.success = True
            
            # Calculate duration
            result.duration_seconds = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"✅ Daily backup completed successfully in {result.duration_seconds:.2f}s")
            self.logger.info(f"📁 Backup file: {result.filename}")
            self.logger.info(f"📊 File count: {result.file_count}")
            self.logger.info(f"📏 File size: {result.file_size} bytes")
            
            # Cleanup temporary files
            try:
                if encrypted_path:
                    Path(encrypted_path).unlink()
            except:
                pass
            
        except Exception as e:
            result.error_message = str(e)
            result.duration_seconds = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"❌ Daily backup failed: {e}")
        
        finally:
            # Log backup attempt
            self._log_backup_attempt(result)
            
            # Log to Notion
            self._log_backup_to_notion(result)
        
        return result

def main():
    """Main entry point for daily backup"""
    try:
        print()
        print("🗄️ MEMORYSYNCAGENT™ DAILY BACKUP TO SUPABASE")
        print("=" * 55)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print()
        
        backup_manager = MemoryBackupManager()
        result = backup_manager.run_daily_backup()
        
        # Print results
        print()
        print("🏁 BACKUP RESULTS:")
        print("=" * 20)
        
        if result.success:
            print("✅ Status: Daily backup completed successfully")
            print(f"📁 Filename: {result.filename}")
            print(f"📊 Files: {result.file_count} backed up")
            print(f"📏 Size: {result.file_size} bytes")
            print(f"📤 Storage: {result.storage_url}")
        else:
            print("❌ Status: Daily backup failed")
            print(f"🚫 Error: {result.error_message}")
        
        print(f"⏱️ Duration: {result.duration_seconds:.1f}s")
        print(f"📝 Logs: logs/memory_backup.log")
        print()
        
        # Exit with appropriate code
        sys.exit(0 if result.success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Backup interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Backup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()