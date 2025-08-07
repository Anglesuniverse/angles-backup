#!/usr/bin/env python3
"""
Configuration and Memory State Rollback System for Angles AI Universe™
Allows rollback of config files and MemorySyncAgent™ state to previous versions

This module provides:
- Interactive rollback selection for config and memory files
- Decryption of encrypted memory backups
- Git commit tracking for rollback operations
- Notion logging for rollback activities
- Safety validation before rollback execution

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import shutil
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from cryptography.fernet import Fernet

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from notion_backup_logger import create_notion_logger

@dataclass
class BackupFile:
    """Information about a backup file"""
    backup_path: Path
    original_path: str
    timestamp: str
    file_type: str
    encrypted: bool
    file_size: int
    
class ConfigMemoryRollback:
    """Handles rollback of both config files and memory state files"""
    
    def __init__(self):
        """Initialize the rollback system"""
        self.logger = self._setup_logging()
        self.notion_logger = create_notion_logger()
        
        # Version storage directories
        self.config_versions_dir = Path('config_versions')
        self.memory_versions_dir = Path('memory_versions')
        
        # Encryption setup for memory files
        self.encryption_key = self._load_encryption_key()
        
        # Git configuration
        self.git_username = os.getenv('GIT_USERNAME', 'MemorySync Agent')
        self.git_email = os.getenv('GIT_EMAIL', 'memory@anglesuniverse.com')
        
        self.logger.info("⏪ CONFIG & MEMORY ROLLBACK SYSTEM INITIALIZED")
        self.logger.info("=" * 50)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup rollback-specific logging"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('config_memory_rollback')
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler('logs/rollback.log')
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
    
    def _load_encryption_key(self) -> Optional[Fernet]:
        """Load encryption key for memory files"""
        key_file = Path('memory_encryption.key')
        
        if not key_file.exists():
            self.logger.warning("🔐 Encryption key not found - encrypted memory files cannot be restored")
            return None
        
        try:
            with open(key_file, 'rb') as f:
                key = f.read()
            return Fernet(key)
        except Exception as e:
            self.logger.error(f"Failed to load encryption key: {e}")
            return None
    
    def _decrypt_file_content(self, encrypted_content: bytes) -> bytes:
        """Decrypt file content"""
        if not self.encryption_key:
            raise ValueError("Encryption key not available")
        return self.encryption_key.decrypt(encrypted_content)
    
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
    
    def list_available_backups(self, file_type: Optional[str] = None) -> Dict[str, List[BackupFile]]:
        """List all available backup files"""
        backups: Dict[str, List[BackupFile]] = {}
        
        # Determine which directories to scan
        dirs_to_scan = []
        if file_type is None or file_type == 'config':
            dirs_to_scan.append(('config', self.config_versions_dir))
        if file_type is None or file_type == 'memory':
            dirs_to_scan.append(('memory', self.memory_versions_dir))
        
        for backup_type, backup_dir in dirs_to_scan:
            if not backup_dir.exists():
                continue
            
            for backup_file in backup_dir.glob('*'):
                if backup_file.is_file():
                    try:
                        # Parse filename to extract information
                        name_parts = backup_file.stem.split('_')
                        if len(name_parts) >= 3:
                            # Extract timestamp (last two parts: date_time)
                            timestamp = '_'.join(name_parts[-2:])
                            base_name = '_'.join(name_parts[:-2])
                            
                            # Reconstruct original path
                            if backup_type == 'config':
                                original_path = f"{base_name}{backup_file.suffix}"
                            else:  # memory
                                if base_name in ['state', 'session_cache']:
                                    original_path = f"memory/{base_name}.json"
                                elif base_name == 'long_term':
                                    original_path = f"memory/{base_name}.db"
                                else:
                                    original_path = f"memory/indexes/{base_name}"
                            
                            # Check if file is encrypted (memory files might be)
                            encrypted = backup_type == 'memory'
                            try:
                                # Try to detect if file is encrypted by reading first few bytes
                                with open(backup_file, 'rb') as f:
                                    first_bytes = f.read(16)
                                    # Fernet encrypted files start with specific patterns
                                    encrypted = backup_type == 'memory' and not first_bytes.startswith(b'{')
                            except:
                                encrypted = backup_type == 'memory'
                            
                            backup_info = BackupFile(
                                backup_path=backup_file,
                                original_path=original_path,
                                timestamp=timestamp,
                                file_type=backup_type,
                                encrypted=encrypted,
                                file_size=backup_file.stat().st_size
                            )
                            
                            if original_path not in backups:
                                backups[original_path] = []
                            backups[original_path].append(backup_info)
                            
                    except Exception as e:
                        self.logger.debug(f"Could not parse backup file {backup_file}: {e}")
        
        # Sort backups by timestamp (newest first)
        for file_path in backups:
            backups[file_path].sort(key=lambda x: x.timestamp, reverse=True)
        
        return backups
    
    def display_backup_selection_menu(self, backups: Dict[str, List[BackupFile]]) -> Optional[BackupFile]:
        """Display interactive menu for backup selection"""
        if not backups:
            print("❌ No backup files found")
            return None
        
        print("\n📁 AVAILABLE BACKUP FILES:")
        print("=" * 40)
        
        # Create numbered list of all backups
        backup_list = []
        for file_path, file_backups in backups.items():
            print(f"\n📄 {file_path}:")
            for backup in file_backups:
                backup_list.append(backup)
                index = len(backup_list)
                
                # Format file size
                size_kb = backup.file_size / 1024
                size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
                
                # Format display
                encryption_marker = "🔐" if backup.encrypted else "📄"
                type_marker = "⚙️" if backup.file_type == 'config' else "🧠"
                
                print(f"  {index:2d}. {encryption_marker} {type_marker} {backup.timestamp} ({size_str})")
        
        print(f"\n   0. Cancel rollback")
        print()
        
        # Get user selection
        while True:
            try:
                choice = input("Select backup to restore (0 to cancel): ").strip()
                
                if choice == '0':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(backup_list):
                    selected_backup = backup_list[choice_num - 1]
                    
                    # Confirm selection
                    print(f"\n📋 SELECTED BACKUP:")
                    print(f"   File: {selected_backup.original_path}")
                    print(f"   Type: {selected_backup.file_type}")
                    print(f"   Timestamp: {selected_backup.timestamp}")
                    print(f"   Encrypted: {'Yes' if selected_backup.encrypted else 'No'}")
                    
                    confirm = input("\nConfirm restore? (y/N): ").strip().lower()
                    if confirm == 'y':
                        return selected_backup
                    else:
                        print("❌ Rollback cancelled")
                        return None
                else:
                    print(f"❌ Invalid selection. Please choose 1-{len(backup_list)} or 0 to cancel")
                    
            except ValueError:
                print("❌ Invalid input. Please enter a number")
            except KeyboardInterrupt:
                print("\n❌ Rollback cancelled by user")
                return None
    
    def restore_backup_file(self, backup: BackupFile, dry_run: bool = False) -> Dict[str, Any]:
        """Restore a backup file to its original location"""
        try:
            self.logger.info(f"{'🧪 DRY RUN:' if dry_run else '⏪'} Restoring {backup.original_path} from {backup.timestamp}")
            
            # Ensure original directory exists
            original_path = Path(backup.original_path)
            original_path.parent.mkdir(parents=True, exist_ok=True)
            
            if dry_run:
                # Just validate that we can read the backup
                if backup.encrypted:
                    if not self.encryption_key:
                        return {
                            "success": False,
                            "error": "Cannot decrypt backup - encryption key not available"
                        }
                    
                    try:
                        with open(backup.backup_path, 'rb') as f:
                            encrypted_content = f.read()
                        self._decrypt_file_content(encrypted_content)
                    except Exception as e:
                        return {
                            "success": False,
                            "error": f"Cannot decrypt backup: {e}"
                        }
                
                self.logger.info(f"✅ DRY RUN: Backup can be restored to {backup.original_path}")
                return {"success": True, "dry_run": True}
            
            # Create backup of current file if it exists
            if original_path.exists():
                current_backup = f"{original_path}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.rollback_backup"
                shutil.copy2(original_path, current_backup)
                self.logger.info(f"📋 Created current file backup: {current_backup}")
            
            # Restore the file
            if backup.encrypted:
                if not self.encryption_key:
                    return {
                        "success": False,
                        "error": "Cannot decrypt backup - encryption key not available"
                    }
                
                # Read and decrypt
                with open(backup.backup_path, 'rb') as f:
                    encrypted_content = f.read()
                
                decrypted_content = self._decrypt_file_content(encrypted_content)
                
                # Write decrypted content
                with open(original_path, 'wb') as f:
                    f.write(decrypted_content)
            else:
                # Simple copy for unencrypted files
                shutil.copy2(backup.backup_path, original_path)
            
            self.logger.info(f"✅ Successfully restored {backup.original_path}")
            
            return {
                "success": True,
                "original_path": backup.original_path,
                "backup_timestamp": backup.timestamp,
                "file_type": backup.file_type
            }
            
        except Exception as e:
            self.logger.error(f"Failed to restore {backup.original_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def commit_rollback_changes(self, backup: BackupFile) -> Dict[str, Any]:
        """Commit and push rollback changes to Git"""
        try:
            # Add restored file to git
            add_result = self._run_git_command(['git', 'add', backup.original_path])
            if not add_result['success']:
                return {
                    "success": False,
                    "error": f"Failed to add {backup.original_path} to git: {add_result.get('error', 'Unknown error')}"
                }
            
            # Create rollback commit message
            commit_message = f"{backup.file_type.title()} rollback: {Path(backup.original_path).name} {backup.timestamp}"
            
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
            
            self.logger.info(f"📤 Committed rollback: {commit_hash}")
            
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
    
    def log_rollback_to_notion(self, backup: BackupFile, git_commit: str):
        """Log rollback to Notion Memory Change Log"""
        try:
            # Log using the backup logger (will be extended to support memory changes)
            self.notion_logger.log_memory_change(
                file_changed=Path(backup.original_path).name,
                action="Rollback",
                timestamp=backup.timestamp,
                git_commit_id=git_commit,
                file_type=backup.file_type,
                encrypted=backup.encrypted
            )
            
            self.logger.info(f"📝 Logged rollback to Notion: {Path(backup.original_path).name}")
            
        except Exception as e:
            self.logger.warning(f"Failed to log rollback to Notion: {e}")
    
    def run_interactive_rollback(self, file_type: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
        """Run interactive rollback process"""
        start_time = datetime.now()
        
        self.logger.info(f"🔍 {'DRY RUN: ' if dry_run else ''}Starting interactive rollback...")
        
        # List available backups
        backups = self.list_available_backups(file_type)
        
        if not backups:
            return {
                "success": False,
                "error": "No backup files found",
                "duration": (datetime.now() - start_time).total_seconds()
            }
        
        # Display selection menu
        selected_backup = self.display_backup_selection_menu(backups)
        
        if not selected_backup:
            return {
                "success": False,
                "error": "Rollback cancelled by user",
                "duration": (datetime.now() - start_time).total_seconds()
            }
        
        # Restore the selected backup
        restore_result = self.restore_backup_file(selected_backup, dry_run)
        
        if not restore_result['success']:
            return {
                "success": False,
                "error": restore_result['error'],
                "duration": (datetime.now() - start_time).total_seconds()
            }
        
        if dry_run:
            duration = (datetime.now() - start_time).total_seconds()
            return {
                "success": True,
                "dry_run": True,
                "selected_backup": {
                    "original_path": selected_backup.original_path,
                    "timestamp": selected_backup.timestamp,
                    "file_type": selected_backup.file_type
                },
                "duration": duration
            }
        
        # Commit changes to git
        git_result = self.commit_rollback_changes(selected_backup)
        
        # Log to Notion
        if git_result['success']:
            self.log_rollback_to_notion(selected_backup, git_result['commit_hash'])
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": git_result['success'],
            "selected_backup": {
                "original_path": selected_backup.original_path,
                "timestamp": selected_backup.timestamp,
                "file_type": selected_backup.file_type
            },
            "git_commit": git_result.get('commit_hash'),
            "git_message": git_result.get('commit_message'),
            "duration": duration,
            "error": git_result.get('error')
        }

def main():
    """Main entry point for rollback system"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Config and Memory State Rollback System")
    parser.add_argument('--type', choices=['config', 'memory'], help='File type to rollback')
    parser.add_argument('--dry-run', action='store_true', help='Preview rollback without making changes')
    
    args = parser.parse_args()
    
    try:
        print()
        print("⏪ ANGLES AI UNIVERSE™ CONFIG & MEMORY ROLLBACK")
        print("=" * 55)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        if args.dry_run:
            print("🧪 DRY RUN MODE - No changes will be made")
        print()
        
        rollback_system = ConfigMemoryRollback()
        result = rollback_system.run_interactive_rollback(args.type, args.dry_run)
        
        # Print results
        print()
        print("🏁 ROLLBACK RESULTS:")
        print("=" * 25)
        
        if result['success']:
            if result.get('dry_run'):
                print("✅ Status: Dry run completed successfully")
                print(f"📄 Would restore: {result['selected_backup']['original_path']}")
                print(f"⏰ From: {result['selected_backup']['timestamp']}")
            else:
                print("✅ Status: Rollback completed successfully")
                print(f"📄 Restored: {result['selected_backup']['original_path']}")
                print(f"⏰ From: {result['selected_backup']['timestamp']}")
                print(f"💾 Commit: {result.get('git_commit', 'unknown')}")
        else:
            print("❌ Status: Rollback failed")
            print(f"🚫 Error: {result.get('error', 'Unknown error')}")
        
        print(f"⏱️ Duration: {result['duration']:.1f}s")
        print(f"📝 Logs: logs/rollback.log")
        print()
        
        # Exit with appropriate code
        sys.exit(0 if result['success'] else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Rollback interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Rollback failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()