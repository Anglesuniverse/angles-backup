#!/usr/bin/env python3
"""
Memory Restore System for Angles AI Universe™
Comprehensive restore capability from multiple sources with safety features

This module provides:
- Multi-source restore: Supabase storage, GitHub repository, local files
- AES-256 decryption using existing encryption key
- Full validation and schema checking
- Supabase decision_vault restore with timestamps
- Safety features: dry-run, confirmations, pre-restore snapshots
- Comprehensive logging and error handling

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import zipfile
import argparse
import logging
import tempfile
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from logging.handlers import RotatingFileHandler

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None

try:
    from supabase import create_client, Client as SupabaseClient
except ImportError:
    SupabaseClient = None
    create_client = None

from backup_utils import UnifiedBackupManager, BackupConfig
from notion_backup_logger import create_notion_logger

class MemoryRestoreManager:
    """Manages memory system restoration from multiple sources"""
    
    def __init__(self, dry_run: bool = False):
        """Initialize the restore manager"""
        self.dry_run = dry_run
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
        
        # Restore paths
        self.restore_temp_dir = Path('restore_temp')
        self.backup_dir = Path('backups')
        self.memory_dir = Path('memory')
        
        # Bucket configuration
        self.bucket_name = 'memory_backups'
        
        self.logger.info("🔄 MEMORY RESTORE MANAGER INITIALIZED")
        self.logger.info("=" * 50)
        if self.dry_run:
            self.logger.info("🚨 DRY-RUN MODE ENABLED - No changes will be made")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup restore-specific logging"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('memory_restore')
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Rotating file handler
        file_handler = RotatingFileHandler(
            'logs/restore.log',
            maxBytes=1024*1024,  # 1MB
            backupCount=10,
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
    
    def _init_supabase_client(self):
        """Initialize Supabase client"""
        if not create_client or not self.supabase_url or not self.supabase_key:
            self.logger.warning("Supabase not available or credentials missing")
            return None
        
        try:
            client = create_client(self.supabase_url, self.supabase_key)
            self.logger.info("✅ Supabase client initialized")
            return client
        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase client: {e}")
            return None
    
    def _init_encryption(self):
        """Initialize decryption for backup files"""
        if not Fernet:
            self.logger.warning("Cryptography not available, encrypted backups cannot be restored")
            return None
            
        if not self.backup_encryption_key:
            self.logger.warning("No BACKUP_ENCRYPTION_KEY found, encrypted backups cannot be restored")
            return None
        
        try:
            # If key is provided as base64 string, use it directly
            if len(self.backup_encryption_key) == 44:  # Base64 encoded Fernet key length
                return Fernet(self.backup_encryption_key.encode())
            else:
                self.logger.error("Invalid backup encryption key format")
                return None
        except Exception as e:
            self.logger.error(f"Failed to initialize decryption: {e}")
            return None
    
    def create_pre_restore_snapshot(self) -> Optional[str]:
        """Create a pre-restore snapshot for safety"""
        if self.dry_run:
            self.logger.info("📸 [DRY-RUN] Would create pre-restore snapshot")
            return "dry-run-snapshot"
        
        try:
            self.logger.info("📸 Creating pre-restore snapshot...")
            
            # Create backup using existing backup system
            config = BackupConfig(
                backup_type='manual',
                tag=f"pre-restore-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                include_memory=True,
                include_github=False,  # Just create local backup
                encryption_enabled=True
            )
            
            backup_manager = UnifiedBackupManager(config)
            result = backup_manager.run_unified_backup()
            
            if result.success:
                self.logger.info(f"✅ Pre-restore snapshot created: {result.filename}")
                return result.filename
            else:
                self.logger.warning(f"Failed to create pre-restore snapshot: {result.error_message}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating pre-restore snapshot: {e}")
            return None
    
    def download_from_supabase(self, filename: str, storage_prefix: str = None) -> Optional[str]:
        """Download backup file from Supabase storage"""
        if not self.supabase:
            self.logger.error("Supabase client not available")
            return None
        
        try:
            # Try both prefixes if not specified
            prefixes_to_try = [storage_prefix] if storage_prefix else ['manual', 'daily']
            
            for prefix in prefixes_to_try:
                storage_path = f"{prefix}/{filename}"
                
                try:
                    # Download file from storage
                    response = self.supabase.storage.from_(self.bucket_name).download(storage_path)
                    
                    if response:
                        # Save to temp file
                        temp_path = self.restore_temp_dir / filename
                        with open(temp_path, 'wb') as f:
                            f.write(response)
                        
                        self.logger.info(f"📥 Downloaded from Supabase: {storage_path}")
                        return str(temp_path)
                        
                except Exception as e:
                    self.logger.debug(f"Failed to download from {storage_path}: {e}")
                    continue
            
            self.logger.error(f"File not found in Supabase storage: {filename}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error downloading from Supabase: {e}")
            return None
    
    def download_from_github(self, filename: str, tag: str = None) -> Optional[str]:
        """Download backup file from GitHub repository"""
        if not self.github_token or not self.repo_url:
            self.logger.error("GitHub credentials not available")
            return None
        
        try:
            self.logger.info("📥 Downloading from GitHub repository...")
            
            # Clone or update repository
            repo_dir = Path('github_restore_temp')
            
            if repo_dir.exists():
                shutil.rmtree(repo_dir)
            
            # Clone repository
            clone_url = self.repo_url.replace('https://', f'https://x-access-token:{self.github_token}@')
            result = subprocess.run(['git', 'clone', clone_url, str(repo_dir)], 
                                 capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to clone repository: {result.stderr}")
                return None
            
            # If tag is specified, checkout that commit/tag
            if tag:
                result = subprocess.run(['git', 'checkout', tag], 
                                     cwd=repo_dir, capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.warning(f"Failed to checkout tag {tag}: {result.stderr}")
            
            # Look for backup file in export directory
            export_dir = repo_dir / 'export'
            backup_files = list(export_dir.glob(f"*{filename}*")) if export_dir.exists() else []
            
            if not backup_files:
                backup_files = list(export_dir.glob("*.zip")) if export_dir.exists() else []
            
            if not backup_files:
                self.logger.error(f"Backup file not found in GitHub repository: {filename}")
                return None
            
            # Use the first matching file
            source_file = backup_files[0]
            dest_file = self.restore_temp_dir / source_file.name
            
            shutil.copy2(source_file, dest_file)
            
            # Cleanup
            shutil.rmtree(repo_dir)
            
            self.logger.info(f"📥 Downloaded from GitHub: {source_file.name}")
            return str(dest_file)
            
        except Exception as e:
            self.logger.error(f"Error downloading from GitHub: {e}")
            return None
    
    def get_local_backup(self, filename: str) -> Optional[str]:
        """Get backup file from local backups directory"""
        try:
            # Check multiple possible locations
            possible_paths = [
                self.backup_dir / filename,
                Path(filename),  # Direct path
                Path('export') / filename,
                Path(f'/tmp/{filename}')
            ]
            
            for path in possible_paths:
                if path.exists() and path.is_file():
                    # Return the source path directly - no need to copy yet
                    self.logger.info(f"📁 Using local backup: {path}")
                    return str(path)
            
            self.logger.error(f"Local backup file not found: {filename}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error accessing local backup: {e}")
            return None
    
    def decrypt_backup_file(self, file_path: str) -> Optional[str]:
        """Decrypt backup file if encrypted"""
        if not self.cipher:
            # Check if file appears to be encrypted
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_file:
                    # If we can open as zip, it's not encrypted
                    self.logger.info("📂 Backup file is not encrypted")
                    return file_path
            except:
                self.logger.error("File appears to be encrypted but no decryption key available")
                return None
        
        # Check if file is encrypted (ends with .encrypted or can't be opened as zip)
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # File is already decrypted
                return file_path
        except:
            # File might be encrypted, try to decrypt
            pass
        
        try:
            self.logger.info("🔓 Decrypting backup file...")
            
            with open(file_path, 'rb') as encrypted_file:
                encrypted_data = encrypted_file.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            
            # Save decrypted file
            decrypted_path = file_path.replace('.encrypted', '') if file_path.endswith('.encrypted') else f"{file_path}.decrypted"
            
            with open(decrypted_path, 'wb') as decrypted_file:
                decrypted_file.write(decrypted_data)
            
            self.logger.info("✅ Backup file decrypted successfully")
            return decrypted_path
            
        except Exception as e:
            self.logger.error(f"Failed to decrypt backup file: {e}")
            return None
    
    def validate_backup_structure(self, backup_path: str) -> Dict[str, Any]:
        """Validate backup file structure and contents"""
        validation_result = {
            'valid': False,
            'backup_metadata': None,
            'memory_files': [],
            'decision_vault_data': None,
            'errors': []
        }
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as zip_file:
                file_list = zip_file.namelist()
                
                # Check for metadata file
                if 'backup_metadata.json' in file_list:
                    metadata_content = zip_file.read('backup_metadata.json').decode('utf-8')
                    validation_result['backup_metadata'] = json.loads(metadata_content)
                    self.logger.info("✅ Found backup metadata")
                else:
                    validation_result['errors'].append("Missing backup_metadata.json")
                
                # Check for memory files
                memory_files = ['state.json', 'session_cache.json', 'long_term.db']
                for memory_file in memory_files:
                    if memory_file in file_list:
                        validation_result['memory_files'].append(memory_file)
                
                # Check for decision vault data (might be in a separate file or embedded)
                decision_files = [f for f in file_list if 'decision' in f.lower() and f.endswith('.json')]
                if decision_files:
                    decision_content = zip_file.read(decision_files[0]).decode('utf-8')
                    validation_result['decision_vault_data'] = json.loads(decision_content)
                    self.logger.info(f"✅ Found decision vault data: {decision_files[0]}")
                
                # Mark as valid if we have essential components
                if validation_result['backup_metadata'] and validation_result['memory_files']:
                    validation_result['valid'] = True
                    self.logger.info("✅ Backup structure validation passed")
                else:
                    validation_result['errors'].append("Missing essential backup components")
                    
        except Exception as e:
            validation_result['errors'].append(f"Failed to validate backup: {e}")
            self.logger.error(f"Backup validation failed: {e}")
        
        return validation_result
    
    def extract_backup(self, backup_path: str) -> bool:
        """Extract backup to restore temp directory"""
        try:
            self.logger.info("📦 Extracting backup archive...")
            
            # Clear restore temp directory
            if self.restore_temp_dir.exists():
                shutil.rmtree(self.restore_temp_dir)
            self.restore_temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Ensure we're using the absolute path
            abs_backup_path = Path(backup_path).resolve()
            
            with zipfile.ZipFile(abs_backup_path, 'r') as zip_file:
                zip_file.extractall(self.restore_temp_dir)
            
            self.logger.info(f"✅ Backup extracted to {self.restore_temp_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to extract backup: {e}")
            return False
    
    def restore_memory_files(self) -> bool:
        """Restore memory files from extracted backup"""
        if self.dry_run:
            self.logger.info("📁 [DRY-RUN] Would restore memory files")
            return True
        
        try:
            self.logger.info("📁 Restoring memory files...")
            
            # Ensure memory directory exists
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            
            # Restore individual files
            memory_files = ['state.json', 'session_cache.json', 'long_term.db']
            restored_count = 0
            
            for memory_file in memory_files:
                source_path = self.restore_temp_dir / memory_file
                dest_path = self.memory_dir / memory_file
                
                if source_path.exists():
                    shutil.copy2(source_path, dest_path)
                    self.logger.info(f"📁 Restored: {memory_file}")
                    restored_count += 1
                else:
                    self.logger.warning(f"Memory file not found in backup: {memory_file}")
            
            # Restore indexes directory
            source_indexes = self.restore_temp_dir / 'indexes'
            dest_indexes = self.memory_dir / 'indexes'
            
            if source_indexes.exists() and source_indexes.is_dir():
                if dest_indexes.exists():
                    shutil.rmtree(dest_indexes)
                shutil.copytree(source_indexes, dest_indexes)
                self.logger.info("📁 Restored: indexes directory")
                restored_count += 1
            
            self.logger.info(f"✅ Restored {restored_count} memory components")
            return restored_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to restore memory files: {e}")
            return False
    
    def restore_decision_vault(self, decision_data: List[Dict[str, Any]]) -> bool:
        """Restore decision vault data to Supabase"""
        if not self.supabase:
            self.logger.warning("Supabase not available, skipping decision vault restore")
            return True
        
        if self.dry_run:
            self.logger.info(f"🗄️ [DRY-RUN] Would restore {len(decision_data)} decision vault records")
            return True
        
        try:
            self.logger.info(f"🗄️ Restoring {len(decision_data)} decision vault records...")
            
            restored_count = 0
            updated_count = 0
            
            current_timestamp = datetime.now(timezone.utc).isoformat()
            
            for record in decision_data:
                try:
                    # Add restored_at timestamp
                    record['restored_at'] = current_timestamp
                    
                    # Check if record already exists
                    record_id = record.get('id')
                    if record_id:
                        existing = self.supabase.table('decision_vault').select('*').eq('id', record_id).execute()
                        
                        if existing.data:
                            # Update existing record
                            # Preserve synced_at if it exists
                            if existing.data[0].get('synced_at'):
                                record['synced_at'] = existing.data[0]['synced_at']
                            
                            update_result = self.supabase.table('decision_vault').update(record).eq('id', record_id).execute()
                            if update_result.data:
                                updated_count += 1
                            else:
                                self.logger.warning(f"Failed to update record {record_id}")
                        else:
                            # Insert new record
                            insert_result = self.supabase.table('decision_vault').insert(record).execute()
                            if insert_result.data:
                                restored_count += 1
                            else:
                                self.logger.warning(f"Failed to insert record {record_id}")
                    else:
                        # Insert without ID (let Supabase generate)
                        record.pop('id', None)  # Remove id to let Supabase generate new one
                        insert_result = self.supabase.table('decision_vault').insert(record).execute()
                        if insert_result.data:
                            restored_count += 1
                        else:
                            self.logger.warning("Failed to insert record without ID")
                
                except Exception as e:
                    self.logger.error(f"Failed to restore individual record: {e}")
                    continue
            
            self.logger.info(f"✅ Decision vault restore completed: {restored_count} new, {updated_count} updated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore decision vault: {e}")
            return False
    
    def log_restore_action(self, source: str, filename: str, success: bool, details: str = ""):
        """Log restore action to restore.log and Notion"""
        try:
            # Log to Notion
            status = "Success" if success else "Failure"
            restore_details = f"Source: {source}, File: {filename}"
            if details:
                restore_details += f", {details}"
            
            # Log restore using backup logger with appropriate parameters
            self.notion_logger.log_backup(
                success=success,
                items_processed=1,
                details=f"RESTORE - {restore_details}"
            )
            
            self.logger.info("📝 Logged restore action to Notion")
            
        except Exception as e:
            self.logger.warning(f"Failed to log restore action to Notion: {e}")
    
    def run_restore(self, source: str, filename: str = None, tag: str = None, force: bool = False) -> bool:
        """Execute complete restore process"""
        start_time = datetime.now()
        
        self.logger.info(f"🔄 Starting restore from {source.upper()}")
        if filename:
            self.logger.info(f"📁 Target file: {filename}")
        if tag:
            self.logger.info(f"🏷️ Tag: {tag}")
        
        try:
            # Create restore temp directory
            self.restore_temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Get user confirmation unless force is used
            if not force and not self.dry_run:
                print("\n⚠️ WARNING: This will overwrite existing memory data and decision vault records!")
                print("Are you sure you want to continue? (yes/no): ", end="")
                confirmation = input().strip().lower()
                if confirmation != 'yes':
                    self.logger.info("Restore cancelled by user")
                    return False
            
            # Step 2: Create pre-restore snapshot
            snapshot_filename = self.create_pre_restore_snapshot()
            if not snapshot_filename and not self.dry_run:
                print("Failed to create pre-restore snapshot. Continue anyway? (yes/no): ", end="")
                confirmation = input().strip().lower()
                if confirmation != 'yes':
                    self.logger.info("Restore cancelled due to snapshot failure")
                    return False
            
            # Step 3: Download/get backup file
            backup_file_path = None
            
            if source == 'supabase':
                if not filename:
                    self.logger.error("Filename required for Supabase restore")
                    return False
                backup_file_path = self.download_from_supabase(filename)
            
            elif source == 'github':
                backup_file_path = self.download_from_github(filename or "*.zip", tag)
            
            elif source == 'local':
                if not filename:
                    self.logger.error("Filename required for local restore")
                    return False
                backup_file_path = self.get_local_backup(filename)
            
            else:
                self.logger.error(f"Unknown source: {source}")
                return False
            
            if not backup_file_path:
                self.logger.error("Failed to obtain backup file")
                return False
            
            # Step 4: Decrypt if necessary
            decrypted_path = self.decrypt_backup_file(backup_file_path)
            if not decrypted_path:
                self.logger.error("Failed to decrypt backup file")
                return False
            
            # Step 5: Validate backup structure
            validation = self.validate_backup_structure(decrypted_path)
            if not validation['valid']:
                self.logger.error(f"Backup validation failed: {validation['errors']}")
                return False
            
            # Step 6: Extract backup
            if not self.extract_backup(decrypted_path):
                self.logger.error("Failed to extract backup")
                return False
            
            # Step 7: Restore memory files
            if not self.restore_memory_files():
                self.logger.error("Failed to restore memory files")
                return False
            
            # Step 8: Restore decision vault if data is available
            if validation['decision_vault_data']:
                if not self.restore_decision_vault(validation['decision_vault_data']):
                    self.logger.error("Failed to restore decision vault")
                    return False
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            
            success_message = f"✅ Restore completed successfully in {duration:.2f}s"
            if self.dry_run:
                success_message = f"✅ [DRY-RUN] Restore simulation completed in {duration:.2f}s"
            
            self.logger.info(success_message)
            
            # Log restore action
            details = f"Duration: {duration:.2f}s"
            if snapshot_filename:
                details += f", Pre-restore snapshot: {snapshot_filename}"
            
            self.log_restore_action(source, filename or "auto-detected", True, details)
            
            # Cleanup
            if self.restore_temp_dir.exists():
                shutil.rmtree(self.restore_temp_dir)
            
            return True
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"❌ Restore failed after {duration:.2f}s: {e}")
            
            # Log failure
            self.log_restore_action(source, filename or "unknown", False, f"Error: {e}")
            
            return False

def main():
    """Main entry point for restore system"""
    parser = argparse.ArgumentParser(
        description="Memory Restore System for Angles AI Universe™",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python restore_memory.py --source supabase --file memory_backup_2025-08-07.zip
  python restore_memory.py --source github --tag v2.1.0
  python restore_memory.py --source local --file /backups/backup.zip --force
  python restore_memory.py --source supabase --file backup.zip --dry-run
        """
    )
    
    parser.add_argument(
        '--source',
        required=True,
        choices=['supabase', 'github', 'local'],
        help='Source to restore from'
    )
    
    parser.add_argument(
        '--file',
        type=str,
        help='Backup filename (required for supabase and local sources)'
    )
    
    parser.add_argument(
        '--tag',
        type=str,
        help='Tag or commit to checkout for GitHub source'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompts'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate restore without making changes'
    )
    
    args = parser.parse_args()
    
    try:
        print()
        print("🔄 ANGLES AI UNIVERSE™ MEMORY RESTORE SYSTEM")
        print("=" * 55)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"Source: {args.source.upper()}")
        if args.file:
            print(f"File: {args.file}")
        if args.tag:
            print(f"Tag: {args.tag}")
        if args.dry_run:
            print("Mode: DRY-RUN")
        if args.force:
            print("Force: ENABLED")
        print()
        
        # Initialize restore manager
        restore_manager = MemoryRestoreManager(dry_run=args.dry_run)
        
        # Execute restore
        success = restore_manager.run_restore(
            source=args.source,
            filename=args.file,
            tag=args.tag,
            force=args.force
        )
        
        # Print results
        print()
        print("🏁 RESTORE RESULTS:")
        print("=" * 20)
        
        if success:
            status = "✅ Status: Restore completed successfully" if not args.dry_run else "✅ Status: Dry-run completed successfully"
            print(status)
            print(f"📁 Source: {args.source}")
            if args.file:
                print(f"📄 File: {args.file}")
        else:
            print("❌ Status: Restore failed")
        
        print(f"📝 Logs: logs/restore.log")
        print()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Restore interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Restore failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()