#!/usr/bin/env python3
"""
Configuration and Memory State Version Control for Angles AI Universe™
Monitors config files and MemorySyncAgent™ state files for changes and creates versioned backups

This module provides:
- Automatic versioning of configuration files
- MemorySyncAgent™ state backup and versioning
- Git integration for change tracking
- Encrypted storage of sensitive memory data
- Notion logging for all version control operations
- Cleanup of old versions (keep 20 most recent)

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import shutil
import hashlib
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from cryptography.fernet import Fernet
from logging.handlers import RotatingFileHandler

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from notion_backup_logger import create_notion_logger

@dataclass
class VersionedFile:
    """Information about a versioned file"""
    original_path: str
    backup_path: str
    file_type: str  # 'config' or 'memory'
    timestamp: str
    file_hash: str
    encrypted: bool = False
    
class ConfigMemoryVersioner:
    """Handles versioning of both config files and memory state files"""
    
    def __init__(self):
        """Initialize the versioning system"""
        self.logger = self._setup_logging()
        self.notion_logger = create_notion_logger()
        
        # File monitoring configuration
        self.config_files = [
            'config.py',
            'config_old.py',
            'pyproject.toml',
            'uv.lock'
        ]
        
        self.memory_files = [
            'memory/state.json',
            'memory/session_cache.json', 
            'memory/long_term.db'
        ]
        
        self.memory_directories = [
            'memory/indexes'
        ]
        
        # Version storage directories
        self.config_versions_dir = Path('config_versions')
        self.memory_versions_dir = Path('memory_versions')
        
        # Create directories
        self.config_versions_dir.mkdir(exist_ok=True)
        self.memory_versions_dir.mkdir(exist_ok=True)
        
        # Encryption setup for memory files
        self.encryption_key = self._get_or_create_encryption_key()
        
        # Git configuration
        self.git_username = os.getenv('GIT_USERNAME', 'MemorySync Agent')
        self.git_email = os.getenv('GIT_EMAIL', 'memory@anglesuniverse.com')
        
        # Keep track of file hashes to detect changes
        self.file_hashes: Dict[str, str] = {}
        
        self.logger.info("📁 CONFIG & MEMORY VERSIONER INITIALIZED")
        self.logger.info("=" * 50)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup versioning-specific logging"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('config_memory_versioner')
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Rotating file handler
        file_handler = RotatingFileHandler(
            'logs/version_control.log',
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
    
    def _get_or_create_encryption_key(self) -> Fernet:
        """Get or create encryption key for memory files"""
        key_file = Path('memory_encryption.key')
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            self.logger.info("🔐 Generated new encryption key for memory files")
        
        return Fernet(key)
    
    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate SHA256 hash of file contents"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash
        except Exception as e:
            self.logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return None
    
    def _encrypt_file_content(self, content: bytes) -> bytes:
        """Encrypt file content for secure storage"""
        return self.encryption_key.encrypt(content)
    
    def _decrypt_file_content(self, encrypted_content: bytes) -> bytes:
        """Decrypt file content"""
        return self.encryption_key.decrypt(encrypted_content)
    
    def _sanitize_memory_content(self, content: str, file_path: str) -> str:
        """Sanitize memory content to remove sensitive data before backup"""
        try:
            # Parse JSON content
            data = json.loads(content)
            
            # Remove potentially sensitive fields
            sensitive_fields = [
                'user_data', 'personal_info', 'email', 'phone', 'address',
                'api_key', 'token', 'password', 'secret', 'private_key'
            ]
            
            def sanitize_dict(obj):
                if isinstance(obj, dict):
                    sanitized = {}
                    for key, value in obj.items():
                        # Remove sensitive fields
                        if any(field in key.lower() for field in sensitive_fields):
                            sanitized[key] = "[REDACTED]"
                        elif isinstance(value, (dict, list)):
                            sanitized[key] = sanitize_dict(value)
                        else:
                            sanitized[key] = value
                    return sanitized
                elif isinstance(obj, list):
                    return [sanitize_dict(item) for item in obj]
                else:
                    return obj
            
            sanitized_data = sanitize_dict(data)
            return json.dumps(sanitized_data, indent=2)
            
        except json.JSONDecodeError:
            # If not JSON, apply basic text sanitization
            sanitized = content
            for field in ['password', 'token', 'key', 'secret']:
                # Replace patterns like "password": "value"
                import re
                pattern = rf'("{field}":\s*")[^"]*(")'
                sanitized = re.sub(pattern, r'\1[REDACTED]\2', sanitized, flags=re.IGNORECASE)
            
            return sanitized
    
    def _run_git_command(self, command: List[str]) -> Dict[str, Any]:
        """Execute git command with error handling"""
        try:
            # Configure git user
            subprocess.run(['git', 'config', 'user.name', self.git_username], 
                         capture_output=True, check=False)
            subprocess.run(['git', 'config', 'user.email', self.git_email], 
                         capture_output=True, check=False)
            
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
    
    def create_version_backup(self, file_path: str, file_type: str) -> Optional[VersionedFile]:
        """Create a versioned backup of a file"""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                self.logger.warning(f"Source file does not exist: {file_path}")
                return None
            
            # Generate timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
            
            # Determine backup directory and filename
            if file_type == 'config':
                backup_dir = self.config_versions_dir
                backup_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            else:  # memory
                backup_dir = self.memory_versions_dir
                backup_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            
            backup_path = backup_dir / backup_filename
            
            # Read and process file content
            with open(source_path, 'rb') as f:
                original_content = f.read()
            
            # Calculate hash
            file_hash = hashlib.sha256(original_content).hexdigest()
            
            # For memory files, sanitize and encrypt
            if file_type == 'memory':
                try:
                    # Sanitize content
                    content_str = original_content.decode('utf-8')
                    sanitized_content = self._sanitize_memory_content(content_str, file_path)
                    
                    # Encrypt sanitized content
                    encrypted_content = self._encrypt_file_content(sanitized_content.encode('utf-8'))
                    
                    # Write encrypted backup
                    with open(backup_path, 'wb') as f:
                        f.write(encrypted_content)
                    
                    encrypted = True
                    
                except Exception as e:
                    self.logger.warning(f"Failed to encrypt {file_path}, storing as plain text: {e}")
                    shutil.copy2(source_path, backup_path)
                    encrypted = False
            else:
                # For config files, just copy
                shutil.copy2(source_path, backup_path)
                encrypted = False
            
            versioned_file = VersionedFile(
                original_path=file_path,
                backup_path=str(backup_path),
                file_type=file_type,
                timestamp=timestamp,
                file_hash=file_hash,
                encrypted=encrypted
            )
            
            self.logger.info(f"✅ Created backup: {backup_filename}")
            return versioned_file
            
        except Exception as e:
            self.logger.error(f"Failed to create backup for {file_path}: {e}")
            return None
    
    def cleanup_old_versions(self, file_type: str, max_versions: int = 20):
        """Clean up old versions, keeping only the most recent ones"""
        try:
            if file_type == 'config':
                backup_dir = self.config_versions_dir
            else:
                backup_dir = self.memory_versions_dir
            
            # Group files by base name
            file_groups: Dict[str, List[Path]] = {}
            
            for backup_file in backup_dir.glob('*'):
                if backup_file.is_file():
                    # Extract base name (everything before the timestamp)
                    name_parts = backup_file.stem.split('_')
                    if len(name_parts) >= 3:
                        base_name = '_'.join(name_parts[:-2])  # Remove timestamp parts
                        if base_name not in file_groups:
                            file_groups[base_name] = []
                        file_groups[base_name].append(backup_file)
            
            # Clean up each group
            for base_name, files in file_groups.items():
                if len(files) > max_versions:
                    # Sort by modification time (newest first)
                    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    
                    # Remove oldest files
                    files_to_remove = files[max_versions:]
                    for old_file in files_to_remove:
                        old_file.unlink()
                        self.logger.info(f"🗑️ Removed old version: {old_file.name}")
                    
                    self.logger.info(f"📁 Cleaned up {len(files_to_remove)} old versions of {base_name}")
        
        except Exception as e:
            self.logger.error(f"Failed to cleanup old versions: {e}")
    
    def commit_and_push_changes(self, versioned_files: List[VersionedFile]) -> Dict[str, Any]:
        """Commit and push version changes to Git"""
        try:
            # Add versioned files to git
            for vf in versioned_files:
                add_result = self._run_git_command(['git', 'add', vf.backup_path])
                if not add_result['success']:
                    self.logger.warning(f"Failed to add {vf.backup_path} to git: {add_result.get('error', 'Unknown error')}")
            
            # Create commit message
            if len(versioned_files) == 1:
                vf = versioned_files[0]
                commit_message = f"{vf.file_type.title()} state update: {Path(vf.original_path).name} {vf.timestamp}"
            else:
                config_count = sum(1 for vf in versioned_files if vf.file_type == 'config')
                memory_count = sum(1 for vf in versioned_files if vf.file_type == 'memory')
                commit_message = f"Batch update: {config_count} config, {memory_count} memory files {datetime.now().strftime('%Y-%m-%d_%H%M%S')}"
            
            # Commit changes
            commit_result = self._run_git_command(['git', 'commit', '-m', commit_message])
            if not commit_result['success']:
                return {
                    "success": False,
                    "error": f"Commit failed: {commit_result.get('stderr', 'Unknown error')}"
                }
            
            # Get commit hash
            hash_result = self._run_git_command(['git', 'rev-parse', 'HEAD'])
            commit_hash = hash_result['stdout'][:8] if hash_result['success'] else 'unknown'
            
            # Push to remote
            push_result = self._run_git_command(['git', 'push', 'origin', 'main'])
            if not push_result['success']:
                self.logger.warning(f"Push failed: {push_result.get('stderr', 'Unknown error')}")
                # Don't fail the operation if push fails - commit was successful
            
            self.logger.info(f"📤 Committed and pushed changes: {commit_hash}")
            
            return {
                "success": True,
                "commit_hash": commit_hash,
                "commit_message": commit_message
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def detect_changes(self) -> List[str]:
        """Detect changes in monitored files"""
        changed_files = []
        
        # Check config files
        for file_path in self.config_files:
            if Path(file_path).exists():
                current_hash = self._calculate_file_hash(file_path)
                if current_hash and current_hash != self.file_hashes.get(file_path):
                    changed_files.append(file_path)
                    self.file_hashes[file_path] = current_hash
        
        # Check memory files
        for file_path in self.memory_files:
            if Path(file_path).exists():
                current_hash = self._calculate_file_hash(file_path)
                if current_hash and current_hash != self.file_hashes.get(file_path):
                    changed_files.append(file_path)
                    self.file_hashes[file_path] = current_hash
        
        # Check memory directories (simplified - check if any files changed)
        for dir_path in self.memory_directories:
            dir_path_obj = Path(dir_path)
            if dir_path_obj.exists():
                for file_path in dir_path_obj.rglob('*'):
                    if file_path.is_file():
                        file_str = str(file_path)
                        current_hash = self._calculate_file_hash(file_str)
                        if current_hash and current_hash != self.file_hashes.get(file_str):
                            changed_files.append(file_str)
                            self.file_hashes[file_str] = current_hash
        
        return changed_files
    
    def log_version_change_to_notion(self, versioned_file: VersionedFile, git_commit: str, action: str = "Update"):
        """Log version change to Notion Memory Change Log"""
        try:
            # Create a simplified log entry for the backup logger
            # Since we don't have a specific memory change logger, we'll extend the backup logger
            self.notion_logger.log_memory_change(
                file_changed=Path(versioned_file.original_path).name,
                action=action,
                timestamp=versioned_file.timestamp,
                git_commit_id=git_commit,
                file_type=versioned_file.file_type,
                encrypted=versioned_file.encrypted
            )
            
            self.logger.info(f"📝 Logged {action.lower()} to Notion: {Path(versioned_file.original_path).name}")
            
        except Exception as e:
            self.logger.warning(f"Failed to log to Notion: {e}")
    
    def run_version_check(self) -> Dict[str, Any]:
        """Run complete version control check and backup process"""
        self.logger.info("🔍 Starting version control check...")
        
        start_time = datetime.now()
        
        # Detect changes
        changed_files = self.detect_changes()
        
        if not changed_files:
            self.logger.info("✅ No changes detected")
            return {
                "success": True,
                "changes_detected": False,
                "files_processed": 0,
                "duration": (datetime.now() - start_time).total_seconds()
            }
        
        self.logger.info(f"📝 Changes detected in {len(changed_files)} files:")
        for file_path in changed_files:
            self.logger.info(f"  - {file_path}")
        
        # Create backups
        versioned_files = []
        for file_path in changed_files:
            # Determine file type
            if file_path in self.config_files:
                file_type = 'config'
            else:
                file_type = 'memory'
            
            versioned_file = self.create_version_backup(file_path, file_type)
            if versioned_file:
                versioned_files.append(versioned_file)
        
        if not versioned_files:
            self.logger.warning("No backups created")
            return {
                "success": False,
                "error": "Failed to create any backups",
                "duration": (datetime.now() - start_time).total_seconds()
            }
        
        # Cleanup old versions
        self.cleanup_old_versions('config', max_versions=20)
        self.cleanup_old_versions('memory', max_versions=20)
        
        # Commit and push changes
        git_result = self.commit_and_push_changes(versioned_files)
        
        # Log to Notion
        if git_result['success']:
            for versioned_file in versioned_files:
                self.log_version_change_to_notion(
                    versioned_file, 
                    git_result['commit_hash'], 
                    "Update"
                )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        self.logger.info(f"✅ Version control completed in {duration:.2f} seconds")
        
        return {
            "success": git_result['success'],
            "changes_detected": True,
            "files_processed": len(versioned_files),
            "versioned_files": [
                {
                    "original_path": vf.original_path,
                    "backup_path": vf.backup_path,
                    "file_type": vf.file_type,
                    "encrypted": vf.encrypted
                }
                for vf in versioned_files
            ],
            "git_commit": git_result.get('commit_hash'),
            "git_message": git_result.get('commit_message'),
            "duration": duration,
            "error": git_result.get('error')
        }

def main():
    """Main entry point for version control system"""
    try:
        print()
        print("📁 ANGLES AI UNIVERSE™ CONFIG & MEMORY VERSIONER")
        print("=" * 55)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print()
        
        versioner = ConfigMemoryVersioner()
        result = versioner.run_version_check()
        
        # Print results
        print()
        print("🏁 VERSION CONTROL RESULTS:")
        print("=" * 30)
        
        if result['success']:
            if result['changes_detected']:
                print("✅ Status: Changes processed successfully")
                print(f"📁 Files: {result['files_processed']} versioned")
                print(f"💾 Commit: {result.get('git_commit', 'unknown')}")
            else:
                print("✅ Status: No changes detected")
        else:
            print("❌ Status: Version control failed")
            print(f"🚫 Error: {result.get('error', 'Unknown error')}")
        
        print(f"⏱️ Duration: {result['duration']:.1f}s")
        print(f"📝 Logs: logs/version_control.log")
        print()
        
        # Exit with appropriate code
        sys.exit(0 if result['success'] else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Version control interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Version control failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()