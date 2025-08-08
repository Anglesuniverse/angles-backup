#!/usr/bin/env python3
"""
Angles AI Universe™ Restore from GitHub
Safe restore with collision handling

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import requests
except ImportError:
    print("❌ Missing required dependency: requests")
    sys.exit(1)

try:
    from utils.git_helpers import GitHelpers
except ImportError:
    print("❌ utils.git_helpers not available")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def setup_logging():
    """Setup logging for restore runner"""
    os.makedirs("logs/active", exist_ok=True)
    
    logger = logging.getLogger('restore_runner')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler
    file_handler = logging.FileHandler('logs/active/restore_runner.log')
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class RestoreRunner:
    """GitHub restore with collision-safe upserts"""
    
    def __init__(self, dry_run: bool = False):
        self.logger = setup_logging()
        self.dry_run = dry_run
        
        # Configuration
        self.repo_url = os.getenv('REPO_URL')
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        # Paths
        self.safe_export_dir = Path('export/safe')
        
        # Git helper
        self.git_helper = GitHelpers()
        
        # Supabase headers
        if self.supabase_url and self.supabase_key:
            self.supabase_headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            self.supabase_enabled = True
        else:
            self.supabase_enabled = False
        
        self.restore_stats = {
            'files_pulled': 0,
            'decisions_processed': 0,
            'decisions_restored': 0,
            'decisions_skipped': 0,
            'decisions_failed': 0
        }
    
    def pull_latest_from_github(self) -> bool:
        """Pull latest changes from GitHub"""
        self.logger.info("⬇️ Pulling latest changes from GitHub...")
        
        if not self.repo_url or not self.github_token:
            self.logger.error("❌ GitHub not configured (missing REPO_URL or GITHUB_TOKEN)")
            return False
        
        try:
            # Setup git repository
            if not self.git_helper.init_repo_if_needed():
                return False
            
            # Pull latest changes
            result = self.git_helper.safe_pull_with_rebase()
            
            if result:
                self.logger.info("✅ Successfully pulled latest changes")
                return True
            else:
                self.logger.error("❌ Failed to pull changes from GitHub")
                return False
        
        except Exception as e:
            self.logger.error(f"❌ Error pulling from GitHub: {e}")
            return False
    
    def load_decision_file(self, file_path: Path) -> Optional[List[Dict[str, Any]]]:
        """Load decisions from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Look for decisions in various possible keys
                for key in ['decisions', 'data', 'items', 'records']:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                
                # If it's a single decision object, wrap in list
                if 'decision' in data or 'id' in data:
                    return [data]
            
            self.logger.warning(f"⚠️ Unrecognized JSON structure in {file_path}")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error loading {file_path}: {e}")
            return None
    
    def decision_exists(self, decision_text: str, decision_date: str) -> Optional[str]:
        """Check if decision already exists in Supabase"""
        if not self.supabase_enabled:
            return None
        
        try:
            # Query for existing decision with same text and date
            query_params = [
                f"decision=eq.{decision_text}",
                f"date=eq.{decision_date}",
                "select=id"
            ]
            query_string = "&".join(query_params)
            
            response = requests.get(
                f"{self.supabase_url}/rest/v1/decision_vault?{query_string}",
                headers=self.supabase_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                if results:
                    return results[0]['id']
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error checking decision existence: {e}")
            return None
    
    def upsert_decision(self, decision_data: Dict[str, Any]) -> bool:
        """Upsert decision to Supabase with collision handling"""
        if not self.supabase_enabled:
            self.logger.warning("⚠️ Supabase not configured, skipping decision restore")
            return False
        
        if self.dry_run:
            self.logger.info(f"🔍 [DRY RUN] Would restore: {decision_data.get('decision', 'Unknown decision')[:50]}...")
            return True
        
        try:
            decision_text = decision_data.get('decision', '')
            decision_date = decision_data.get('date', datetime.now().date().isoformat())
            
            # Check if decision already exists
            existing_id = self.decision_exists(decision_text, decision_date)
            
            if existing_id:
                self.logger.info(f"   ⏭️ Decision already exists, skipping: {decision_text[:50]}...")
                self.restore_stats['decisions_skipped'] += 1
                return True
            
            # Prepare decision data for insert
            insert_data = {
                'decision': decision_text,
                'date': decision_date,
                'type': decision_data.get('type', 'other'),
                'active': decision_data.get('active', True),
                'comment': decision_data.get('comment', ''),
                'synced': False  # Mark as unsynced so it gets processed by memory sync
            }
            
            # Insert new decision
            response = requests.post(
                f"{self.supabase_url}/rest/v1/decision_vault",
                headers=self.supabase_headers,
                json=insert_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                self.logger.info(f"   ✅ Restored: {decision_text[:50]}...")
                self.restore_stats['decisions_restored'] += 1
                return True
            else:
                self.logger.error(f"   ❌ Failed to restore decision: HTTP {response.status_code}")
                self.logger.error(f"      Response: {response.text}")
                self.restore_stats['decisions_failed'] += 1
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error upserting decision: {e}")
            self.restore_stats['decisions_failed'] += 1
            return False
    
    def restore_decisions_from_files(self) -> bool:
        """Restore decisions from exported JSON files"""
        self.logger.info("📋 Restoring decisions from exported files...")
        
        if not self.safe_export_dir.exists():
            self.logger.warning("⚠️ No safe export directory found")
            return True
        
        json_files = list(self.safe_export_dir.glob('*.json'))
        
        if not json_files:
            self.logger.info("ℹ️ No JSON files found to restore")
            return True
        
        self.logger.info(f"📁 Found {len(json_files)} JSON files to process")
        
        for json_file in json_files:
            self.logger.info(f"📄 Processing {json_file.name}...")
            
            decisions = self.load_decision_file(json_file)
            
            if decisions is None:
                continue
            
            if not decisions:
                self.logger.info(f"   ℹ️ No decisions found in {json_file.name}")
                continue
            
            self.logger.info(f"   📝 Found {len(decisions)} decisions in {json_file.name}")
            
            for i, decision in enumerate(decisions, 1):
                self.restore_stats['decisions_processed'] += 1
                
                # Skip if not a valid decision
                if not isinstance(decision, dict) or 'decision' not in decision:
                    self.logger.warning(f"   ⚠️ Invalid decision format at index {i}")
                    continue
                
                self.logger.info(f"   📝 Processing {i}/{len(decisions)}: {decision['decision'][:50]}...")
                self.upsert_decision(decision)
            
            self.restore_stats['files_pulled'] += 1
        
        return True
    
    def run_restore(self, restore_decisions: bool = False) -> bool:
        """Run complete restore process"""
        self.logger.info("🚀 Starting Angles AI Universe™ Restore")
        self.logger.info(f"📍 Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        self.logger.info("=" * 60)
        
        success = True
        
        # Step 1: Pull latest from GitHub
        if not self.pull_latest_from_github():
            success = False
        
        # Step 2: Restore decisions if requested
        if restore_decisions and success:
            if not self.restore_decisions_from_files():
                success = False
        elif restore_decisions:
            self.logger.warning("⚠️ Skipping decision restore due to previous failures")
        
        # Print summary
        self.logger.info("=" * 60)
        self.logger.info("📊 RESTORE SUMMARY")
        self.logger.info("=" * 60)
        
        if restore_decisions:
            self.logger.info(f"📁 Files processed: {self.restore_stats['files_pulled']}")
            self.logger.info(f"📝 Decisions processed: {self.restore_stats['decisions_processed']}")
            self.logger.info(f"✅ Decisions restored: {self.restore_stats['decisions_restored']}")
            self.logger.info(f"⏭️ Decisions skipped (existing): {self.restore_stats['decisions_skipped']}")
            self.logger.info(f"❌ Decisions failed: {self.restore_stats['decisions_failed']}")
        
        if success:
            self.logger.info("✅ RESTORE COMPLETED SUCCESSFULLY")
        else:
            self.logger.error("❌ RESTORE COMPLETED WITH ERRORS")
        
        return success

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Restore from GitHub')
    parser.add_argument('--restore-decisions', action='store_true', help='Restore decisions to Supabase')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    try:
        restore_runner = RestoreRunner(dry_run=args.dry_run)
        success = restore_runner.run_restore(restore_decisions=args.restore_decisions)
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"💥 Restore runner failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()