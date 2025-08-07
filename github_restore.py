#!/usr/bin/env python3
"""
GitHub Restore System for Angles AI Universe™ Memory System
Restores AI memory system from backups stored in GitHub repo exports/

This module provides comprehensive disaster recovery capabilities:
- Automatic snapshot detection and selection
- Safe Supabase upserts with conflict resolution
- Optional Notion synchronization
- Comprehensive validation and logging
- Dry-run mode for safety verification

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from logging.handlers import RotatingFileHandler

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from utils.git_helpers import GitHelpers
from utils.json_sanitizer import JSONSanitizer

try:
    from supabase import create_client, Client as SupabaseClient
except ImportError:
    SupabaseClient = None
    create_client = None

try:
    from notion_client import Client as NotionClient
except ImportError:
    NotionClient = None

# Configure logging
def setup_logging() -> logging.Logger:
    """Setup rotating log handler for restore operations"""
    logger = logging.getLogger('github_restore')
    logger.setLevel(logging.INFO)
    
    # Ensure logs directory exists
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Rotating file handler
    file_handler = RotatingFileHandler(
        'logs/restore.log',
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

logger = setup_logging()

class GitHubRestoreSystem:
    """Main class for GitHub-based disaster recovery"""
    
    def __init__(self):
        """Initialize the restore system with environment configuration"""
        logger.info("Initializing GitHub Restore System")
        
        # Load environment variables
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.notion_database_id = os.getenv('NOTION_DATABASE_ID')
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_url = os.getenv('REPO_URL')
        
        # Validate required environment variables
        self._validate_environment()
        
        # Initialize clients
        self.supabase = None
        self.notion = None
        self.git_helpers = GitHelpers()
        self.json_sanitizer = JSONSanitizer()
        
        # Initialize clients
        self._initialize_clients()
        
        logger.info("GitHub Restore System initialized successfully")
    
    def _validate_environment(self) -> None:
        """Validate required environment variables"""
        required_vars = {
            'SUPABASE_URL': self.supabase_url,
            'SUPABASE_KEY': self.supabase_key,
            'GITHUB_TOKEN': self.github_token,
            'REPO_URL': self.repo_url
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Optional variables
        if not self.notion_token:
            logger.info("NOTION_TOKEN not provided - Notion sync will be disabled")
        if not self.notion_database_id:
            logger.info("NOTION_DATABASE_ID not provided - Notion sync will be disabled")
    
    def _initialize_clients(self) -> None:
        """Initialize Supabase and Notion clients"""
        # Initialize Supabase client
        try:
            if SupabaseClient is None or create_client is None:
                logger.error("Supabase client library not available")
                raise ImportError("supabase library not installed")
            
            if not self.supabase_url or not self.supabase_key:
                raise ValueError("Supabase URL and key are required")
            
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            logger.info("✓ Supabase client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
        
        # Initialize Notion client (optional)
        if self.notion_token and self.notion_database_id:
            try:
                if NotionClient is None:
                    logger.warning("Notion client library not available")
                else:
                    self.notion = NotionClient(auth=self.notion_token)
                    logger.info("✓ Notion client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Notion client: {e}")
                self.notion = None
    
    def ensure_git_repository(self) -> Dict[str, Any]:
        """Ensure git repository is set up and up-to-date"""
        logger.info("Ensuring git repository is ready")
        
        # Setup repository
        setup_result = self.git_helpers.ensure_repository()
        if not setup_result['success']:
            return setup_result
        
        # Pull latest changes
        pull_result = self.git_helpers.safe_pull()
        if not pull_result['success']:
            logger.warning(f"Pull failed: {pull_result.get('error', 'Unknown error')}")
            # Continue anyway - we might still have local exports
        
        return {"success": True, "message": "Git repository ready"}
    
    def find_snapshot_files(self, target_date: Optional[str] = None, explicit_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Find snapshot files to restore from
        
        Args:
            target_date: Specific date to restore (YYYY-MM-DD)
            explicit_files: Explicit list of files to restore
            
        Returns:
            Dictionary with found files and metadata
        """
        logger.info("Finding snapshot files")
        
        if explicit_files:
            # Use explicit files
            found_files = []
            for file_path in explicit_files:
                path = Path(file_path)
                if path.exists():
                    found_files.append({
                        "path": str(path),
                        "type": "explicit",
                        "date": "unknown"
                    })
                else:
                    logger.warning(f"Explicit file not found: {file_path}")
            
            return {
                "success": len(found_files) > 0,
                "files": found_files,
                "selection_method": "explicit"
            }
        
        # Look in exports directory
        exports_dir = Path('export')
        if not exports_dir.exists():
            return {
                "success": False,
                "error": "exports/ directory not found",
                "files": []
            }
        
        # Find decision vault files
        vault_pattern = 'decision_vault_*.json' if target_date is None else f'decision_vault_{target_date}.json'
        vault_files = list(exports_dir.glob(vault_pattern))
        
        # Find notion decision files
        notion_pattern = 'notion_decisions_*.json' if target_date is None else f'notion_decisions_{target_date}.json'
        notion_files = list(exports_dir.glob(notion_pattern))
        
        # Find general decision exports
        general_pattern = 'decisions_*.json' if target_date is None else f'decisions_{target_date.replace("-", "")}.json'
        general_files = list(exports_dir.glob(general_pattern))
        
        all_files = []
        
        # Process found files
        for file_path in vault_files:
            date_match = file_path.stem.split('_')[-1]
            all_files.append({
                "path": str(file_path),
                "type": "decision_vault",
                "date": date_match
            })
        
        for file_path in notion_files:
            date_match = file_path.stem.split('_')[-1]
            all_files.append({
                "path": str(file_path),
                "type": "notion_decisions",
                "date": date_match
            })
        
        for file_path in general_files:
            # Extract date from filename like decisions_20250807.json
            date_part = file_path.stem.split('_')[-1]
            if len(date_part) == 8 and date_part.isdigit():
                formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
            else:
                formatted_date = date_part
            all_files.append({
                "path": str(file_path),
                "type": "decisions_export", 
                "date": formatted_date
            })
        
        if target_date is None and all_files:
            # Auto-select latest files
            all_files.sort(key=lambda x: x['date'], reverse=True)
            latest_date = all_files[0]['date']
            selected_files = [f for f in all_files if f['date'] == latest_date]
        else:
            selected_files = all_files
        
        return {
            "success": len(selected_files) > 0,
            "files": selected_files,
            "selection_method": "auto" if target_date is None else "date_specific",
            "target_date": target_date
        }
    
    def load_and_validate_files(self, file_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Load and validate all snapshot files
        
        Args:
            file_list: List of file dictionaries from find_snapshot_files
            
        Returns:
            Dictionary with loaded and validated data
        """
        logger.info(f"Loading and validating {len(file_list)} files")
        
        all_records = []
        file_results = []
        total_errors = 0
        
        for file_info in file_list:
            logger.info(f"Processing file: {file_info['path']}")
            
            validation_result = self.json_sanitizer.validate_json_file(file_info['path'])
            
            if validation_result['success']:
                records = validation_result['records']
                all_records.extend(records)
                
                file_results.append({
                    "file_path": file_info['path'],
                    "file_type": file_info['type'],
                    "file_date": file_info['date'],
                    "total_records": validation_result['total_records'],
                    "valid_records": validation_result['valid_records'],
                    "invalid_records": validation_result['invalid_records'],
                    "success": True
                })
                
                total_errors += validation_result['invalid_records']
                
                logger.info(f"✓ Loaded {validation_result['valid_records']} valid records from {file_info['path']}")
                
                if validation_result['invalid_records'] > 0:
                    logger.warning(f"⚠ Skipped {validation_result['invalid_records']} invalid records")
            else:
                logger.error(f"✗ Failed to load {file_info['path']}: {validation_result['error']}")
                file_results.append({
                    "file_path": file_info['path'],
                    "file_type": file_info['type'],
                    "file_date": file_info['date'],
                    "success": False,
                    "error": validation_result['error']
                })
        
        # Deduplicate records by ID
        unique_records = {}
        for record in all_records:
            record_id = record.get('id') or self.json_sanitizer.create_deterministic_id(record)
            if record_id not in unique_records:
                unique_records[record_id] = self.json_sanitizer.normalize_record(record)
        
        logger.info(f"Total unique records after deduplication: {len(unique_records)}")
        
        return {
            "success": len(unique_records) > 0,
            "records": list(unique_records.values()),
            "total_records": len(all_records),
            "unique_records": len(unique_records),
            "duplicates_removed": len(all_records) - len(unique_records),
            "file_results": file_results,
            "total_errors": total_errors
        }
    
    def restore_to_supabase(self, records: List[Dict[str, Any]], dry_run: bool = False, force: bool = False) -> Dict[str, Any]:
        """
        Restore records to Supabase decision_vault table
        
        Args:
            records: List of normalized records to restore
            dry_run: If True, only simulate the restore
            force: If True, overwrite newer records
            
        Returns:
            Dictionary with restore results
        """
        logger.info(f"{'Simulating' if dry_run else 'Performing'} Supabase restore of {len(records)} records")
        
        if dry_run:
            # Dry run - just log what would be done
            sample_records = records[:3]
            logger.info("DRY RUN - Would restore the following sample records:")
            for i, record in enumerate(sample_records):
                logger.info(f"  {i+1}. ID: {record.get('id', 'N/A')}, Decision: {record.get('decision', 'N/A')[:50]}...")
            
            return {
                "success": True,
                "dry_run": True,
                "total_records": len(records),
                "would_insert": len(records),
                "would_update": 0,
                "would_skip": 0
            }
        
        # Actual restore
        inserted = 0
        updated = 0
        skipped = 0
        failed = 0
        
        for record in records:
            try:
                record_id = record['id']
                
                # Check if record exists
                if not self.supabase:
                    raise ValueError("Supabase client not initialized")
                existing = self.supabase.table('decision_vault').select('*').eq('id', record_id).execute()
                
                if existing.data:
                    # Record exists - check if we should update
                    existing_record = existing.data[0]
                    
                    # Compare updated_at timestamps if both exist
                    if not force and 'updated_at' in existing_record and 'updated_at' in record:
                        try:
                            existing_ts = datetime.fromisoformat(existing_record['updated_at'].replace('Z', '+00:00'))
                            record_ts = datetime.fromisoformat(record['updated_at'].replace('Z', '+00:00'))
                            
                            if existing_ts > record_ts:
                                logger.debug(f"Skipping older record: {record_id}")
                                skipped += 1
                                continue
                        except ValueError:
                            logger.warning(f"Could not compare timestamps for record: {record_id}")
                    
                    # Update existing record
                    if not self.supabase:
                        raise ValueError("Supabase client not initialized")
                    update_result = self.supabase.table('decision_vault').update(record).eq('id', record_id).execute()
                    if update_result.data:
                        updated += 1
                        logger.debug(f"Updated record: {record_id}")
                    else:
                        failed += 1
                        logger.error(f"Failed to update record: {record_id}")
                else:
                    # Insert new record
                    if not self.supabase:
                        raise ValueError("Supabase client not initialized")
                    insert_result = self.supabase.table('decision_vault').insert(record).execute()
                    if insert_result.data:
                        inserted += 1
                        logger.debug(f"Inserted record: {record_id}")
                    else:
                        failed += 1
                        logger.error(f"Failed to insert record: {record_id}")
                        
            except Exception as e:
                failed += 1
                logger.error(f"Error processing record {record.get('id', 'unknown')}: {e}")
        
        success = failed == 0
        
        logger.info(f"Supabase restore completed: {inserted} inserted, {updated} updated, {skipped} skipped, {failed} failed")
        
        return {
            "success": success,
            "dry_run": False,
            "total_records": len(records),
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
            "failed": failed
        }
    
    def restore_to_notion(self, records: List[Dict[str, Any]], dry_run: bool = False) -> Dict[str, Any]:
        """
        Restore records to Notion database (optional)
        
        Args:
            records: List of normalized records to restore
            dry_run: If True, only simulate the restore
            
        Returns:
            Dictionary with restore results
        """
        if not self.notion or not self.notion_database_id:
            return {
                "success": True,
                "skipped": True,
                "reason": "Notion not configured"
            }
        
        logger.info(f"{'Simulating' if dry_run else 'Performing'} Notion restore of {len(records)} records")
        
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "total_records": len(records),
                "would_create": len(records)
            }
        
        # Actual Notion restore
        created = 0
        skipped = 0
        failed = 0
        
        # Get existing pages to avoid duplicates
        try:
            if not self.notion:
                raise ValueError("Notion client not initialized")
            query_result = self.notion.databases.query(database_id=self.notion_database_id)
            existing_pages = query_result.get('results', []) if isinstance(query_result, dict) else []
            existing_decisions = set()
            
            for page in existing_pages:
                props = page.get('properties', {})
                title_prop = props.get('Name', {}) or props.get('Title', {})
                date_prop = props.get('Date', {})
                
                if title_prop.get('title') and date_prop.get('date'):
                    title_text = title_prop['title'][0]['text']['content'] if title_prop['title'] else ''
                    date_value = date_prop['date']['start'] if date_prop['date'] else ''
                    existing_decisions.add((title_text, date_value))
            
        except Exception as e:
            logger.warning(f"Could not fetch existing Notion pages: {e}")
            existing_decisions = set()
        
        for record in records:
            try:
                decision_text = record.get('decision', '')
                decision_date = record.get('date', '')
                
                # Check for duplicates
                if (decision_text, decision_date) in existing_decisions:
                    logger.debug(f"Skipping duplicate Notion page: {decision_text[:50]}...")
                    skipped += 1
                    continue
                
                # Create Notion page
                page_data = {
                    "parent": {"database_id": self.notion_database_id},
                    "properties": {
                        "Name": {
                            "title": [{"text": {"content": decision_text}}]
                        },
                        "Message": {
                            "rich_text": [{"text": {"content": record.get('comment', '')}}]
                        },
                        "Date": {
                            "date": {"start": decision_date}
                        },
                        "Tag": {
                            "multi_select": [{"name": record.get('type', 'unknown')}]
                        }
                    }
                }
                
                result = self.notion.pages.create(**page_data)
                if result:
                    created += 1
                    logger.debug(f"Created Notion page: {decision_text[:50]}...")
                else:
                    failed += 1
                    
            except Exception as e:
                failed += 1
                logger.error(f"Error creating Notion page for record {record.get('id', 'unknown')}: {e}")
        
        logger.info(f"Notion restore completed: {created} created, {skipped} skipped, {failed} failed")
        
        return {
            "success": failed == 0,
            "dry_run": False,
            "total_records": len(records),
            "created": created,
            "skipped": skipped,
            "failed": failed
        }
    
    def run_restore(self, target_date: Optional[str] = None, explicit_files: Optional[List[str]] = None, 
                   dry_run: bool = False, force: bool = False, with_notion: bool = False) -> Dict[str, Any]:
        """
        Run complete restore operation
        
        Args:
            target_date: Specific date to restore (YYYY-MM-DD)
            explicit_files: Explicit list of files to restore
            dry_run: If True, only simulate the restore
            force: If True, overwrite newer records
            with_notion: If True, also restore to Notion
            
        Returns:
            Dictionary with complete restore results
        """
        start_time = datetime.now()
        logger.info(f"Starting {'DRY RUN' if dry_run else 'LIVE'} restore operation")
        
        try:
            # Step 1: Ensure git repository
            git_result = self.ensure_git_repository()
            if not git_result['success']:
                return {
                    "success": False,
                    "error": f"Git setup failed: {git_result.get('error', 'Unknown error')}",
                    "duration": (datetime.now() - start_time).total_seconds()
                }
            
            # Step 2: Find snapshot files
            files_result = self.find_snapshot_files(target_date, explicit_files)
            if not files_result['success']:
                return {
                    "success": False,
                    "error": f"No snapshot files found: {files_result.get('error', 'No files match criteria')}",
                    "duration": (datetime.now() - start_time).total_seconds()
                }
            
            # Step 3: Load and validate data
            data_result = self.load_and_validate_files(files_result['files'])
            if not data_result['success']:
                return {
                    "success": False,
                    "error": "Failed to load valid data from snapshot files",
                    "duration": (datetime.now() - start_time).total_seconds()
                }
            
            # Step 4: Restore to Supabase
            supabase_result = self.restore_to_supabase(data_result['records'], dry_run, force)
            
            # Step 5: Restore to Notion (optional)
            notion_result = None
            if with_notion:
                notion_result = self.restore_to_notion(data_result['records'], dry_run)
            
            # Calculate final results
            duration = (datetime.now() - start_time).total_seconds()
            
            overall_success = supabase_result['success'] and (notion_result is None or notion_result['success'])
            
            result = {
                "success": overall_success,
                "dry_run": dry_run,
                "duration": duration,
                "files_processed": len(files_result['files']),
                "records_loaded": data_result['unique_records'],
                "supabase_result": supabase_result,
                "notion_result": notion_result,
                "snapshot_info": {
                    "selection_method": files_result['selection_method'],
                    "target_date": files_result.get('target_date'),
                    "files": [f['path'] for f in files_result['files']]
                }
            }
            
            logger.info(f"Restore operation completed in {duration:.2f} seconds")
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Restore operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration": duration
            }

def print_results(result: Dict[str, Any]) -> None:
    """Print formatted restore results to console"""
    print()
    print("=" * 60)
    print("ANGLES AI UNIVERSE™ DISASTER RECOVERY")
    print("=" * 60)
    
    if result['success']:
        print("✅ RESTORE SUCCESSFUL")
    else:
        print("❌ RESTORE FAILED")
        print(f"Error: {result.get('error', 'Unknown error')}")
        print("=" * 60)
        return
    
    # Basic info
    print(f"Duration: {result['duration']:.2f} seconds")
    print(f"Mode: {'DRY RUN' if result.get('dry_run') else 'LIVE RESTORE'}")
    print()
    
    # Snapshot info
    snapshot = result.get('snapshot_info', {})
    print("📂 SNAPSHOT INFORMATION:")
    print(f"Selection: {snapshot.get('selection_method', 'unknown')}")
    if snapshot.get('target_date'):
        print(f"Target Date: {snapshot['target_date']}")
    print(f"Files Processed: {result.get('files_processed', 0)}")
    for file_path in snapshot.get('files', []):
        print(f"  - {file_path}")
    print()
    
    # Supabase results
    supabase = result.get('supabase_result', {})
    print("🗃️  SUPABASE RESULTS:")
    print(f"Records Loaded: {result.get('records_loaded', 0)}")
    
    if result.get('dry_run'):
        print(f"Would Insert: {supabase.get('would_insert', 0)}")
        print(f"Would Update: {supabase.get('would_update', 0)}")
        print(f"Would Skip: {supabase.get('would_skip', 0)}")
    else:
        print(f"Inserted: {supabase.get('inserted', 0)}")
        print(f"Updated: {supabase.get('updated', 0)}")
        print(f"Skipped: {supabase.get('skipped', 0)}")
        print(f"Failed: {supabase.get('failed', 0)}")
    print()
    
    # Notion results (if applicable)
    notion = result.get('notion_result')
    if notion and not notion.get('skipped'):
        print("📝 NOTION RESULTS:")
        if result.get('dry_run'):
            print(f"Would Create: {notion.get('would_create', 0)}")
        else:
            print(f"Created: {notion.get('created', 0)}")
            print(f"Skipped: {notion.get('skipped', 0)}")
            print(f"Failed: {notion.get('failed', 0)}")
        print()
    
    print("=" * 60)

def main():
    """Main entry point for GitHub restore system"""
    parser = argparse.ArgumentParser(
        description="Restore Angles AI Universe™ memory system from GitHub backups",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python github_restore.py --dry-run                    # Simulate latest restore
  python github_restore.py --at 2025-08-07             # Restore specific date
  python github_restore.py --with-notion               # Include Notion sync
  python github_restore.py --file exports/backup.json  # Restore specific file
        """
    )
    
    parser.add_argument('--at', type=str, metavar='YYYY-MM-DD',
                       help='Restore from specific date (YYYY-MM-DD)')
    parser.add_argument('--file', type=str, action='append', metavar='PATH',
                       help='Restore from explicit file(s) (can be used multiple times)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be restored without making changes')
    parser.add_argument('--force', action='store_true',
                       help='Overwrite newer records in database')
    parser.add_argument('--with-notion', action='store_true',
                       help='Also restore to Notion database')
    
    args = parser.parse_args()
    
    try:
        # Initialize restore system
        restore_system = GitHubRestoreSystem()
        
        # Run restore
        result = restore_system.run_restore(
            target_date=args.at,
            explicit_files=args.file,
            dry_run=args.dry_run,
            force=args.force,
            with_notion=args.with_notion
        )
        
        # Print results
        print_results(result)
        
        # Exit with appropriate code
        sys.exit(0 if result['success'] else 1)
        
    except KeyboardInterrupt:
        logger.info("Restore interrupted by user")
        print("\nRestore interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"Restore system failed: {e}")
        print(f"FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()