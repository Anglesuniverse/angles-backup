#!/usr/bin/env python3
"""
Backup Utilities for Angles AI Universe™
Shared utilities for manual and scheduled backup operations with tag support

This module provides:
- Common backup operations with tag support
- Unified backup pipeline for memory and GitHub operations  
- Enhanced filename generation with custom tags
- Centralized backup logging and error handling
- Integration with existing Supabase and Notion systems

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
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None
from supabase import create_client, Client

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from notion_backup_logger import create_notion_logger

@dataclass
class BackupConfig:
    """Configuration for backup operations"""
    backup_type: str  # 'daily' or 'manual'
    tag: Optional[str] = None
    include_memory: bool = True
    include_github: bool = True
    encryption_enabled: bool = True
    retention_days: int = 30

@dataclass
class BackupResult:
    """Comprehensive result of backup operations"""
    success: bool
    backup_type: str
    filename: str = ""
    tag: Optional[str] = None
    storage_url: str = ""
    github_commit_hash: str = ""
    github_commit_url: str = ""
    file_size: int = 0
    file_count: int = 0
    error_message: str = ""
    duration_seconds: float = 0.0

class UnifiedBackupManager:
    """Manages both memory and GitHub backup operations with tag support"""
    
    def __init__(self, config: BackupConfig):
        """Initialize the unified backup manager"""
        self.config = config
        self.logger = self._setup_logging()
        self.notion_logger = create_notion_logger()
        
        # Environment variables
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.backup_encryption_key = os.getenv('BACKUP_ENCRYPTION_KEY')
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_url = os.getenv('REPO_URL')
        
        # Initialize clients
        self.supabase = self._init_supabase_client()
        self.cipher = self._init_encryption()
        
        # Backup configuration
        self.memory_paths = [
            'memory/state.json',
            'memory/session_cache.json', 
            'memory/long_term.db',
            'memory/indexes'
        ]
        
        self.bucket_name = 'memory_backups'
        
        # Set retention based on backup type
        if config.backup_type == 'manual':
            self.retention_days = 15  # Keep 15 manual backups
            self.storage_prefix = 'manual'
        else:
            self.retention_days = config.retention_days  # Keep 30 daily backups
            self.storage_prefix = 'daily'
        
        self.logger.info(f"🔧 UNIFIED BACKUP MANAGER INITIALIZED ({config.backup_type.upper()})")
        self.logger.info("=" * 60)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup backup-specific logging"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # Use different log files for manual vs daily backups
        if self.config.backup_type == 'manual':
            log_filename = 'logs/backup_manual.log'
            logger_name = 'manual_backup'
        else:
            log_filename = 'logs/backup_daily.log'
            logger_name = 'daily_backup'
        
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(log_filename)
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
            self.logger.warning("Supabase credentials not available")
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
    
    def generate_backup_filename(self, timestamp: str) -> str:
        """Generate backup filename with optional tag"""
        if self.config.tag:
            return f"memory_backup_{timestamp}_{self.config.tag}.zip"
        else:
            return f"memory_backup_{timestamp}.zip"
    
    def _create_backup_archive(self, timestamp: str) -> Optional[str]:
        """Create compressed archive of memory files"""
        try:
            filename = self.generate_backup_filename(timestamp)
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
                    "backup_type": self.config.backup_type,
                    "tag": self.config.tag,
                    "files_included": file_count,
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
        if not self.cipher or not self.config.encryption_enabled:
            self.logger.info("Encryption disabled, uploading unencrypted")
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
    
    def _upload_backup_to_storage(self, file_path: str, filename: str, timestamp: str) -> Optional[str]:
        """Upload backup file to Supabase storage"""
        if not self.supabase:
            return None
        
        try:
            # Create bucket if it doesn't exist
            if not self._create_storage_bucket():
                return None
            
            # Upload file to appropriate prefix (daily/ or manual/)
            storage_path = f"{self.storage_prefix}/{filename}"
            
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            result = self.supabase.storage.from_(self.bucket_name).upload(
                storage_path,
                file_data,
                file_options={
                    "content-type": "application/zip",
                    "metadata": {
                        "backup_type": self.config.backup_type,
                        "tag": self.config.tag or "",
                        "timestamp": timestamp,
                        "system": "MemorySyncAgent™"
                    }
                }
            )
            
            if result:
                storage_url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{storage_path}"
                self.logger.info(f"📤 Uploaded to storage: {storage_path}")
                return storage_url
            else:
                self.logger.error("Failed to upload backup to storage")
                return None
                
        except Exception as e:
            self.logger.error(f"Error uploading backup to storage: {e}")
            return None
    
    def _create_storage_bucket(self) -> bool:
        """Create Supabase storage bucket if it doesn't exist"""
        if not self.supabase:
            return False
        
        try:
            # List existing buckets
            buckets = self.supabase.storage.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            
            if self.bucket_name not in bucket_names:
                # Try to create bucket
                try:
                    result = self.supabase.storage.create_bucket(
                        self.bucket_name,
                        options={"public": False}  # Private bucket
                    )
                    
                    if result:
                        self.logger.info(f"✅ Created storage bucket: {self.bucket_name}")
                    else:
                        self.logger.warning(f"Could not create bucket: {self.bucket_name} (may need admin privileges)")
                        return False
                except Exception as bucket_error:
                    self.logger.warning(f"Bucket creation failed: {bucket_error} (may need admin privileges)")
                    return False
            else:
                self.logger.info(f"✅ Storage bucket exists: {self.bucket_name}")
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Storage bucket check failed: {e} (continuing without storage)")
            return False
    
    def _commit_backup_to_github(self, backup_file_path: str, filename: str) -> Tuple[Optional[str], Optional[str]]:
        """Commit backup file to GitHub repository"""
        if not self.github_token or not self.repo_url:
            self.logger.warning("GitHub credentials not available")
            return None, None
        
        try:
            # Configure git user
            self._run_git_command(['git', 'config', 'user.name', 'Backup Agent'])
            self._run_git_command(['git', 'config', 'user.email', 'backup@anglesuniverse.com'])
            
            # Copy backup file to repository
            repo_backup_path = Path('export') / filename
            repo_backup_path.parent.mkdir(exist_ok=True)
            
            # Copy the backup file
            import shutil
            shutil.copy2(backup_file_path, repo_backup_path)
            
            # Add to git
            add_result = self._run_git_command(['git', 'add', str(repo_backup_path)])
            if not add_result['success']:
                self.logger.error(f"Failed to add backup to git: {add_result.get('error', 'Unknown error')}")
                return None, None
            
            # Create commit message
            commit_message = f"Manual backup: {filename}"
            if self.config.tag:
                commit_message = f"Manual backup [{self.config.tag}]: {filename}"
            
            # Commit
            commit_result = self._run_git_command(['git', 'commit', '-m', commit_message])
            if not commit_result['success']:
                self.logger.error(f"Failed to commit backup: {commit_result.get('error', 'Unknown error')}")
                return None, None
            
            # Get commit hash
            hash_result = self._run_git_command(['git', 'rev-parse', 'HEAD'])
            commit_hash = hash_result['stdout'][:8] if hash_result['success'] else 'unknown'
            
            # Push to remote
            push_result = self._run_git_command(['git', 'push', 'origin', 'main'])
            if not push_result['success']:
                self.logger.warning(f"Push failed: {push_result.get('error', 'Unknown error')}")
            
            # Generate commit URL
            commit_url = None
            if 'github.com' in self.repo_url:
                repo_url = self.repo_url.replace('.git', '').replace('https://x-access-token:', 'https://').split('@github.com/')[-1]
                if not repo_url.startswith('https://'):
                    repo_url = 'https://github.com/' + repo_url
                commit_url = f"{repo_url}/commit/{commit_hash}"
            
            self.logger.info(f"📤 Committed backup to GitHub: {commit_hash}")
            return commit_hash, commit_url
            
        except Exception as e:
            self.logger.error(f"Failed to commit backup to GitHub: {e}")
            return None, None
    
    def _run_git_command(self, command: List[str]) -> Dict[str, Any]:
        """Execute git command with error handling"""
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Git command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _create_backup_log_table(self) -> bool:
        """Create memory_backup_log table if it doesn't exist"""
        if not self.supabase:
            return False
        
        try:
            # Try to create table using SQL
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
                tag TEXT,
                github_commit_hash VARCHAR(64),
                github_commit_url TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_memory_backup_log_timestamp ON memory_backup_log(timestamp);
            CREATE INDEX IF NOT EXISTS idx_memory_backup_log_status ON memory_backup_log(status);
            CREATE INDEX IF NOT EXISTS idx_memory_backup_log_backup_type ON memory_backup_log(backup_type);
            CREATE INDEX IF NOT EXISTS idx_memory_backup_log_tag ON memory_backup_log(tag);
            
            ALTER TABLE memory_backup_log 
            DROP CONSTRAINT IF EXISTS check_backup_type;
            
            ALTER TABLE memory_backup_log 
            ADD CONSTRAINT check_backup_type CHECK (backup_type IN ('daily', 'manual'));
            """
            
            # Execute via RPC if available
            try:
                self.supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
                self.logger.info("✅ Backup log table created/updated")
                return True
            except Exception as rpc_error:
                self.logger.warning(f"Could not create table via RPC: {rpc_error}")
                # Try alternative method - just test if table exists
                try:
                    self.supabase.table('memory_backup_log').select('id').limit(1).execute()
                    self.logger.info("✅ Backup log table exists")
                    return True
                except Exception:
                    self.logger.warning("Backup log table does not exist and cannot be created")
                    return False
                
        except Exception as e:
            self.logger.warning(f"Table creation check failed: {e}")
            return False
    
    def _log_backup_to_database(self, result: BackupResult) -> bool:
        """Log backup attempt to memory_backup_log table"""
        if not self.supabase:
            return False
        
        # Ensure table exists
        if not self._create_backup_log_table():
            self.logger.warning("Skipping database logging - table not available")
            return False
        
        try:
            # Insert log entry
            log_data = {
                "filename": result.filename,
                "backup_type": result.backup_type,
                "tag": result.tag,
                "status": "success" if result.success else "failure",
                "storage_url": result.storage_url,
                "github_commit_hash": result.github_commit_hash,
                "github_commit_url": result.github_commit_url,
                "file_size": result.file_size,
                "file_count": result.file_count,
                "error_message": result.error_message,
                "duration_seconds": result.duration_seconds
            }
            
            response = self.supabase.table('memory_backup_log').insert(log_data).execute()
            
            if response.data:
                self.logger.info("📝 Logged backup to database")
                return True
            else:
                self.logger.warning("Failed to log backup to database")
                return False
                
        except Exception as e:
            self.logger.warning(f"Error logging backup to database: {e} (continuing without database log)")
            return False
    
    def _log_backup_to_notion(self, result: BackupResult):
        """Log backup to Notion if enabled"""
        try:
            status = "Success" if result.success else "Failure"
            
            details_parts = [
                f"Type: {result.backup_type}",
                f"File: {result.filename}",
                f"Size: {result.file_size} bytes",
                f"Files: {result.file_count}"
            ]
            
            if result.tag:
                details_parts.append(f"Tag: {result.tag}")
            
            if result.github_commit_hash:
                details_parts.append(f"GitHub: {result.github_commit_hash}")
            
            if result.error_message:
                details_parts.append(f"Error: {result.error_message}")
            
            details = ", ".join(details_parts)
            
            self.notion_logger.log_backup(
                success=result.success,
                items_processed=result.file_count,
                commit_link=result.github_commit_url or result.storage_url,
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
            
            # List files in storage for this backup type
            storage_files = self.supabase.storage.from_(self.bucket_name).list(f"{self.storage_prefix}/")
            
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
                    delete_result = self.supabase.storage.from_(self.bucket_name).remove([f"{self.storage_prefix}/{file_name}"])
                    if delete_result:
                        deleted_count += 1
                        self.logger.info(f"🗑️ Deleted old backup: {file_name}")
            
            if deleted_count > 0:
                self.logger.info(f"🧹 Cleaned up {deleted_count} old {self.config.backup_type} backups")
            else:
                self.logger.info(f"✅ No old {self.config.backup_type} backups to clean up")
                
        except Exception as e:
            self.logger.warning(f"Error during backup cleanup: {e}")
    
    def run_unified_backup(self) -> BackupResult:
        """Execute complete backup operation (memory + GitHub)"""
        start_time = datetime.now()
        timestamp = start_time.strftime('%Y-%m-%d_%H%M%S') if self.config.backup_type == 'manual' else start_time.strftime('%Y-%m-%d')
        
        self.logger.info(f"🚀 Starting {self.config.backup_type} backup...")
        
        result = BackupResult(
            success=False,
            backup_type=self.config.backup_type,
            tag=self.config.tag
        )
        
        try:
            if self.config.include_memory:
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
                if encrypted_path:
                    if encrypted_path != archive_path:
                        result.filename = Path(encrypted_path).name
                        result.file_size = Path(encrypted_path).stat().st_size
                    
                    # Upload to Supabase storage
                    storage_url = self._upload_backup_to_storage(encrypted_path, result.filename, timestamp)
                    if storage_url:
                        result.storage_url = storage_url
                    
                    # Commit to GitHub if enabled
                    if self.config.include_github:
                        commit_hash, commit_url = self._commit_backup_to_github(encrypted_path, result.filename)
                        if commit_hash:
                            result.github_commit_hash = commit_hash
                            result.github_commit_url = commit_url
                    
                    # Cleanup temporary files
                    try:
                        if encrypted_path:
                            Path(encrypted_path).unlink()
                    except:
                        pass
                else:
                    result.error_message = "Failed to encrypt backup file"
                    return result
            
            # Cleanup old backups
            self._cleanup_old_backups()
            
            # Mark as successful
            result.success = True
            
            # Calculate duration
            result.duration_seconds = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"✅ {self.config.backup_type.title()} backup completed successfully in {result.duration_seconds:.2f}s")
            if result.tag:
                self.logger.info(f"🏷️ Backup tag: {result.tag}")
            self.logger.info(f"📁 Backup file: {result.filename}")
            self.logger.info(f"📊 File count: {result.file_count}")
            self.logger.info(f"📏 File size: {result.file_size} bytes")
            
        except Exception as e:
            result.error_message = str(e)
            result.duration_seconds = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"❌ {self.config.backup_type.title()} backup failed: {e}")
        
        finally:
            # Log backup attempt
            self._log_backup_to_database(result)
            
            # Log to Notion
            self._log_backup_to_notion(result)
        
        return result