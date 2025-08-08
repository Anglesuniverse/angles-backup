#!/usr/bin/env python3
"""
Angles AI Universe™ Memory Sync
Unified Supabase ⇄ Notion synchronization with CLI flags

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ Missing required dependency: requests")
    sys.exit(1)

try:
    import httpx
except ImportError:
    print("⚠️ httpx not available, falling back to requests")
    httpx = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def setup_logging():
    """Setup logging for memory sync"""
    os.makedirs("logs/active", exist_ok=True)
    
    logger = logging.getLogger('memory_sync')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler
    file_handler = logging.FileHandler('logs/active/memory_sync.log')
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

class NotionClient:
    """Simple Notion client using requests/httpx"""
    
    def __init__(self, token: str, database_id: str):
        self.token = token
        self.database_id = database_id
        self.base_url = "https://api.notion.com/v1"
        
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
        
        # Use httpx if available, otherwise requests
        self.client = httpx if httpx else requests
    
    def test_connection(self) -> bool:
        """Test Notion API connection"""
        try:
            response = self.client.get(
                f"{self.base_url}/databases/{self.database_id}",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def create_page(self, decision_data: Dict[str, Any]) -> Optional[str]:
        """Create a new page in Notion database"""
        try:
            # Format decision type for multi-select
            decision_type = decision_data.get('type', 'other')
            
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": {
                    "Name": {
                        "title": [{"text": {"content": decision_data['decision'][:100]}}]
                    },
                    "Date": {
                        "date": {"start": decision_data.get('date', datetime.now().date().isoformat())}
                    },
                    "Tag": {
                        "multi_select": [{"name": decision_type.title()}]
                    }
                }
            }
            
            # Add comment if present
            comment = decision_data.get('comment')
            if comment:
                page_data["properties"]["Comment"] = {
                    "rich_text": [{"text": {"content": comment[:2000]}}]
                }
            
            response = self.client.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=page_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('id')
            else:
                return None
                
        except Exception as e:
            return None

class MemorySync:
    """Main memory synchronization class"""
    
    def __init__(self, dry_run: bool = False):
        self.logger = setup_logging()
        self.dry_run = dry_run
        
        # Load environment variables
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.notion_token = os.getenv('NOTION_TOKEN') or os.getenv('NOTION_API_KEY')
        self.notion_db_id = os.getenv('NOTION_DATABASE_ID')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY")
        
        self.supabase_headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json'
        }
        
        # Initialize Notion client if credentials available
        self.notion_client = None
        if self.notion_token and self.notion_db_id:
            self.notion_client = NotionClient(self.notion_token, self.notion_db_id)
        
        self.sync_stats = {
            'processed': 0,
            'synced': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def test_connections(self) -> bool:
        """Test all service connections"""
        self.logger.info("🔗 Testing service connections...")
        
        # Test Supabase
        try:
            response = requests.get(
                f"{self.supabase_url}/rest/v1/decision_vault?select=id&limit=1",
                headers=self.supabase_headers,
                timeout=10
            )
            supabase_ok = response.status_code == 200
            self.logger.info(f"{'✅' if supabase_ok else '❌'} Supabase: {'Connected' if supabase_ok else 'Failed'}")
        except Exception as e:
            supabase_ok = False
            self.logger.error(f"❌ Supabase connection error: {e}")
        
        # Test Notion
        notion_ok = False
        if self.notion_client:
            notion_ok = self.notion_client.test_connection()
            self.logger.info(f"{'✅' if notion_ok else '❌'} Notion: {'Connected' if notion_ok else 'Failed'}")
        else:
            self.logger.warning("⚠️ Notion: Not configured (missing NOTION_TOKEN or NOTION_DATABASE_ID)")
        
        return supabase_ok and (notion_ok if self.notion_client else True)
    
    def get_unsynced_decisions(self, sync_all: bool = False, recent_only: bool = False) -> List[Dict[str, Any]]:
        """Get unsynced decisions from Supabase"""
        try:
            # Build query
            query_params = ["select=*"]
            
            if not sync_all:
                query_params.append("synced=eq.false")
            
            if recent_only:
                yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
                query_params.append(f"date=gte.{yesterday}")
            
            query_params.append("order=created_at.desc")
            query_params.append("limit=1000")
            
            query_string = "&".join(query_params)
            
            response = requests.get(
                f"{self.supabase_url}/rest/v1/decision_vault?{query_string}",
                headers=self.supabase_headers,
                timeout=30
            )
            
            if response.status_code == 200:
                decisions = response.json()
                self.logger.info(f"📋 Found {len(decisions)} decisions to process")
                return decisions
            else:
                self.logger.error(f"❌ Failed to fetch decisions: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Error fetching decisions: {e}")
            return []
    
    def mark_decision_synced(self, decision_id: str) -> bool:
        """Mark decision as synced in Supabase"""
        if self.dry_run:
            return True
        
        try:
            data = {
                'synced': True,
                'synced_at': datetime.now(timezone.utc).isoformat()
            }
            
            response = requests.patch(
                f"{self.supabase_url}/rest/v1/decision_vault?id=eq.{decision_id}",
                headers=self.supabase_headers,
                json=data,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"❌ Error marking decision {decision_id} as synced: {e}")
            return False
    
    def sync_decision_to_notion(self, decision: Dict[str, Any]) -> bool:
        """Sync single decision to Notion"""
        if not self.notion_client:
            self.logger.warning("⚠️ Notion not configured, skipping sync")
            return False
        
        if self.dry_run:
            self.logger.info(f"🔍 [DRY RUN] Would sync to Notion: {decision['decision'][:50]}...")
            return True
        
        try:
            page_id = self.notion_client.create_page(decision)
            
            if page_id:
                self.logger.info(f"✅ Synced to Notion: {decision['decision'][:50]}...")
                return True
            else:
                self.logger.error(f"❌ Failed to sync to Notion: {decision['decision'][:50]}...")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error syncing to Notion: {e}")
            return False
    
    def sync_decisions(self, sync_all: bool = False, recent_only: bool = False) -> bool:
        """Sync unsynced decisions"""
        self.logger.info("🔄 Starting decision synchronization...")
        
        decisions = self.get_unsynced_decisions(sync_all, recent_only)
        
        if not decisions:
            self.logger.info("✅ No decisions to sync")
            return True
        
        for i, decision in enumerate(decisions, 1):
            self.logger.info(f"📝 Processing {i}/{len(decisions)}: {decision['decision'][:50]}...")
            self.sync_stats['processed'] += 1
            
            # Skip if already synced (for sync_all mode)
            if decision.get('synced') and not sync_all:
                self.logger.info("   ⏭️ Already synced, skipping")
                self.sync_stats['skipped'] += 1
                continue
            
            # Sync to Notion
            notion_success = True
            if self.notion_client:
                notion_success = self.sync_decision_to_notion(decision)
            
            if notion_success:
                # Mark as synced
                if self.mark_decision_synced(decision['id']):
                    self.sync_stats['synced'] += 1
                else:
                    self.sync_stats['failed'] += 1
            else:
                self.sync_stats['failed'] += 1
        
        return self.sync_stats['failed'] == 0
    
    def generate_export_summary(self) -> bool:
        """Generate JSON export summary"""
        try:
            os.makedirs("export", exist_ok=True)
            
            export_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'sync_stats': self.sync_stats,
                'dry_run': self.dry_run,
                'notion_configured': self.notion_client is not None
            }
            
            # Add recent decisions for export
            if not self.dry_run:
                recent_decisions = self.get_unsynced_decisions(sync_all=False, recent_only=True)
                export_data['recent_decisions_count'] = len(recent_decisions)
            
            date_str = datetime.now().strftime('%Y%m%d')
            export_file = f"export/decisions_{date_str}.json"
            
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"📊 Export summary saved: {export_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error generating export summary: {e}")
            return False
    
    def run_sync(self, sync_all: bool = False, recent_only: bool = False) -> bool:
        """Run complete sync process"""
        self.logger.info("🚀 Starting Angles AI Universe™ Memory Sync")
        self.logger.info(f"📍 Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        
        # Test connections first
        if not self.test_connections():
            self.logger.error("❌ Connection tests failed")
            return False
        
        # Run sync
        success = self.sync_decisions(sync_all, recent_only)
        
        # Generate export
        self.generate_export_summary()
        
        # Print summary
        self.logger.info("📊 Sync Summary:")
        self.logger.info(f"   📝 Processed: {self.sync_stats['processed']}")
        self.logger.info(f"   ✅ Synced: {self.sync_stats['synced']}")
        self.logger.info(f"   ❌ Failed: {self.sync_stats['failed']}")
        self.logger.info(f"   ⏭️ Skipped: {self.sync_stats['skipped']}")
        
        return success

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Memory Sync - Supabase ⇄ Notion')
    parser.add_argument('--test', action='store_true', help='Test connections only')
    parser.add_argument('--all', action='store_true', help='Sync all decisions (ignore synced flag)')
    parser.add_argument('--recent', action='store_true', help='Sync recent decisions only (last 24h)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    try:
        sync_engine = MemorySync(dry_run=args.dry_run)
        
        if args.test:
            success = sync_engine.test_connections()
            print(f"🔗 Connection test: {'✅ PASSED' if success else '❌ FAILED'}")
            sys.exit(0 if success else 1)
        
        success = sync_engine.run_sync(sync_all=args.all, recent_only=args.recent)
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"💥 Memory sync failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()