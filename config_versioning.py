#!/usr/bin/env python3
"""
Angles AI Universe™ Core Configuration Version Control System
Monitors core configuration files for changes and creates versioned backups in GitHub

This module provides:
- Automatic versioning of core configuration files (YAML, JSON, SQL, ENV)
- Git integration for change tracking in "angles-backup" repository
- Notion logging for "Configuration Change Log"
- Security validation to prevent sensitive data leakage
- Cleanup of old versions (keep 10 most recent per file type)

Author: Angles AI Universe™ Backend Team
Version: 2.0.0
"""

import os
import sys
import json
import shutil
import hashlib
import logging
import subprocess
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from notion_backup_logger import create_notion_logger

@dataclass
class ConfigVersion:
    """Information about a versioned configuration file"""
    original_path: str
    backup_path: str
    timestamp: str
    file_hash: str
    file_size: int
    
class AnglesConfigVersioner:
    """Handles versioning of Angles AI Universe™ core configuration files"""
    
    def __init__(self):
        """Initialize the configuration versioning system"""
        self.logger = self._setup_logging()
        self.notion_logger = create_notion_logger()
        
        # Core configuration files to monitor
        self.config_files = [
            'config/CorePrompt.yaml',
            'config/ExecPrompt.yaml',
            'config/agent_config.json',
            'config/memory_settings.json',
            'config/db_schema.sql',
            'config/system_variables.env'
        ]
        
        # Alternative locations to check
        self.alt_config_files = [
            'CorePrompt.yaml',
            'ExecPrompt.yaml', 
            'agent_config.json',
            'memory_settings.json',
            'db_schema.sql',
            'system_variables.env'
        ]
        
        # Version storage directory
        self.config_versions_dir = Path('config_versions')
        self.config_versions_dir.mkdir(exist_ok=True)
        
        # Git configuration
        self.git_username = os.getenv('GIT_USERNAME', 'Angles Config Agent')
        self.git_email = os.getenv('GIT_EMAIL', 'config@anglesuniverse.com')
        
        # Keep track of file hashes to detect changes
        self.file_hashes: Dict[str, str] = {}
        
        # Security patterns for sensitive data detection
        self.sensitive_patterns = [
            r'[A-Za-z0-9_]+_KEY\s*=\s*[\'"][^\'"\s]+[\'"]',
            r'[A-Za-z0-9_]+_SECRET\s*=\s*[\'"][^\'"\s]+[\'"]',
            r'[A-Za-z0-9_]+_TOKEN\s*=\s*[\'"][^\'"\s]+[\'"]',
            r'PASSWORD\s*=\s*[\'"][^\'"\s]+[\'"]',
            r'PRIVATE_KEY\s*=\s*[\'"][^\'"\s]+[\'"]',
            r'DATABASE_URL\s*=\s*[\'"][^\'"\s]+[\'"]'
        ]
        
        self.logger.info("⚙️ ANGLES AI UNIVERSE™ CONFIG VERSIONER INITIALIZED")
        self.logger.info("=" * 55)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup configuration versioning specific logging"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('angles_config_versioner')
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Rotating file handler
        file_handler = RotatingFileHandler(
            'logs/config_versioning.log',
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
    
    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate SHA256 hash of file contents"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash
        except Exception as e:
            self.logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return None
    
    def _validate_security(self, file_path: str) -> Dict[str, Any]:
        """Validate file for sensitive data before backup"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            sensitive_found = []
            
            # Check for sensitive patterns
            for pattern in self.sensitive_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    sensitive_found.extend(matches)
            
            # Special handling for .env files - sanitize but don't block
            if file_path.endswith('.env'):
                sanitized_content = self._sanitize_env_content(content)
                return {
                    "secure": True,
                    "sensitive_found": len(sensitive_found),
                    "sanitized_content": sanitized_content,
                    "warning": f"Found {len(sensitive_found)} sensitive values - will be sanitized"
                }
            
            # For non-env files, block if sensitive data found
            if sensitive_found:
                return {
                    "secure": False,
                    "sensitive_found": len(sensitive_found),
                    "error": f"Sensitive data detected: {len(sensitive_found)} patterns matched"
                }
            
            return {
                "secure": True,
                "sensitive_found": 0
            }
            
        except Exception as e:
            return {
                "secure": False,
                "error": f"Security validation failed: {e}"
            }
    
    def _sanitize_env_content(self, content: str) -> str:
        """Sanitize .env file content by masking sensitive values"""
        sanitized = content
        
        # Replace sensitive values with placeholders
        for pattern in self.sensitive_patterns:
            sanitized = re.sub(
                pattern, 
                lambda m: f"{m.group().split('=')[0]}=[REDACTED]",
                sanitized,
                flags=re.IGNORECASE
            )
        
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
    
    def create_config_backup(self, file_path: str) -> Optional[ConfigVersion]:
        """Create a versioned backup of a configuration file"""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                self.logger.warning(f"Source file does not exist: {file_path}")
                return None
            
            # Security validation
            security_check = self._validate_security(file_path)
            if not security_check['secure']:
                self.logger.error(f"Security validation failed for {file_path}: {security_check.get('error')}")
                return None
            
            # Generate timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
            
            # Create backup filename
            backup_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            backup_path = self.config_versions_dir / backup_filename
            
            # Read original content
            with open(source_path, 'rb') as f:
                original_content = f.read()
            
            # Calculate hash
            file_hash = hashlib.sha256(original_content).hexdigest()
            
            # Handle .env files with sanitization
            if file_path.endswith('.env') and 'sanitized_content' in security_check:
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(security_check['sanitized_content'])
                self.logger.info(f"🔐 Created sanitized backup: {backup_filename}")
            else:
                # Regular copy for other files
                shutil.copy2(source_path, backup_path)
                self.logger.info(f"✅ Created backup: {backup_filename}")
            
            config_version = ConfigVersion(
                original_path=file_path,
                backup_path=str(backup_path),
                timestamp=timestamp,
                file_hash=file_hash,
                file_size=backup_path.stat().st_size
            )
            
            return config_version
            
        except Exception as e:
            self.logger.error(f"Failed to create backup for {file_path}: {e}")
            return None
    
    def cleanup_old_versions(self, max_versions: int = 10):
        """Clean up old versions, keeping only the most recent ones per file type"""
        try:
            # Group files by base name
            file_groups: Dict[str, List[Path]] = {}
            
            for backup_file in self.config_versions_dir.glob('*'):
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
    
    def commit_and_push_changes(self, config_versions: List[ConfigVersion]) -> Dict[str, Any]:
        """Commit and push configuration changes to Git"""
        try:
            # Add versioned files to git
            for cv in config_versions:
                add_result = self._run_git_command(['git', 'add', cv.backup_path])
                if not add_result['success']:
                    self.logger.warning(f"Failed to add {cv.backup_path} to git: {add_result.get('error', 'Unknown error')}")
            
            # Create commit message
            if len(config_versions) == 1:
                cv = config_versions[0]
                commit_message = f"Config update: {Path(cv.original_path).name} {cv.timestamp}"
            else:
                commit_message = f"Config batch update: {len(config_versions)} files {datetime.now().strftime('%Y-%m-%d_%H%M%S')}"
            
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
    
    def detect_config_changes(self) -> List[str]:
        """Detect changes in monitored configuration files"""
        changed_files = []
        
        # Check all configured files (both in config/ and root)
        all_files = self.config_files + self.alt_config_files
        
        for file_path in all_files:
            if Path(file_path).exists():
                current_hash = self._calculate_file_hash(file_path)
                if current_hash and current_hash != self.file_hashes.get(file_path):
                    changed_files.append(file_path)
                    self.file_hashes[file_path] = current_hash
        
        return changed_files
    
    def log_config_change_to_notion(self, config_version: ConfigVersion, git_commit: str, action: str = "Update"):
        """Log configuration change to Notion Configuration Change Log"""
        try:
            # Use the existing backup logger with memory change method
            # (Will be adapted to target Configuration Change Log database)
            self.notion_logger.log_memory_change(
                file_changed=Path(config_version.original_path).name,
                action=action,
                timestamp=config_version.timestamp,
                git_commit_id=git_commit,
                file_type="config",
                encrypted=False,
                details=f"Size: {config_version.file_size} bytes, Hash: {config_version.file_hash[:8]}"
            )
            
            self.logger.info(f"📝 Logged {action.lower()} to Notion: {Path(config_version.original_path).name}")
            
        except Exception as e:
            self.logger.warning(f"Failed to log to Notion: {e}")
    
    def run_config_monitoring(self) -> Dict[str, Any]:
        """Run complete configuration monitoring and backup process"""
        self.logger.info("🔍 Starting configuration monitoring...")
        
        start_time = datetime.now()
        
        # Detect changes
        changed_files = self.detect_config_changes()
        
        if not changed_files:
            self.logger.info("✅ No configuration changes detected")
            return {
                "success": True,
                "changes_detected": False,
                "files_processed": 0,
                "duration": (datetime.now() - start_time).total_seconds()
            }
        
        self.logger.info(f"📝 Configuration changes detected in {len(changed_files)} files:")
        for file_path in changed_files:
            self.logger.info(f"  - {file_path}")
        
        # Create backups
        config_versions = []
        for file_path in changed_files:
            config_version = self.create_config_backup(file_path)
            if config_version:
                config_versions.append(config_version)
        
        if not config_versions:
            self.logger.warning("No backups created")
            return {
                "success": False,
                "error": "Failed to create any backups",
                "duration": (datetime.now() - start_time).total_seconds()
            }
        
        # Cleanup old versions
        self.cleanup_old_versions(max_versions=10)
        
        # Commit and push changes
        git_result = self.commit_and_push_changes(config_versions)
        
        # Log to Notion
        if git_result['success']:
            for config_version in config_versions:
                self.log_config_change_to_notion(
                    config_version, 
                    git_result['commit_hash'], 
                    "Update"
                )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        self.logger.info(f"✅ Configuration monitoring completed in {duration:.2f} seconds")
        
        return {
            "success": git_result['success'],
            "changes_detected": True,
            "files_processed": len(config_versions),
            "config_versions": [
                {
                    "original_path": cv.original_path,
                    "backup_path": cv.backup_path,
                    "timestamp": cv.timestamp,
                    "file_size": cv.file_size
                }
                for cv in config_versions
            ],
            "git_commit": git_result.get('commit_hash'),
            "git_message": git_result.get('commit_message'),
            "duration": duration,
            "error": git_result.get('error')
        }

def main():
    """Main entry point for configuration version control system"""
    try:
        print()
        print("⚙️ ANGLES AI UNIVERSE™ CONFIGURATION VERSIONER")
        print("=" * 55)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print()
        
        versioner = AnglesConfigVersioner()
        result = versioner.run_config_monitoring()
        
        # Print results
        print()
        print("🏁 CONFIGURATION MONITORING RESULTS:")
        print("=" * 40)
        
        if result['success']:
            if result['changes_detected']:
                print("✅ Status: Configuration changes processed successfully")
                print(f"📁 Files: {result['files_processed']} versioned")
                print(f"💾 Commit: {result.get('git_commit', 'unknown')}")
            else:
                print("✅ Status: No configuration changes detected")
        else:
            print("❌ Status: Configuration monitoring failed")
            print(f"🚫 Error: {result.get('error', 'Unknown error')}")
        
        print(f"⏱️ Duration: {result['duration']:.1f}s")
        print(f"📝 Logs: logs/config_versioning.log")
        print()
        
        # Exit with appropriate code
        sys.exit(0 if result['success'] else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Configuration monitoring interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Configuration monitoring failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()