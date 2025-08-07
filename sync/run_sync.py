#!/usr/bin/env python3
"""
Main bidirectional sync runner for Supabase-Notion sync
Orchestrates the complete sync process for Angles AI Universe™

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List

from .config import get_config
from .logging_util import get_logger, save_health_status, load_health_status
from .supabase_client import SupabaseClient
from .notion_client import NotionClient
from .diff import DiffEngine, SyncDelta


class BidirectionalSync:
    """Main bidirectional sync orchestrator"""
    
    def __init__(self, dry_run: bool = False):
        """Initialize sync service"""
        self.config = get_config()
        self.logger = get_logger()
        self.dry_run = dry_run
        
        # Initialize clients
        self.supabase = SupabaseClient()
        self.notion = NotionClient()
        self.diff_engine = DiffEngine()
        
        self.logger.info(f"🔄 Bidirectional sync initialized {'(DRY RUN)' if dry_run else ''}")
    
    def run_sync(self) -> Dict[str, Any]:
        """Run complete bidirectional sync process"""
        
        start_time = datetime.now()
        stats = {
            'start_time': start_time.isoformat(),
            'supabase_count': 0,
            'notion_count': 0,
            'created': 0,
            'updated': 0,
            'deleted': 0,
            'errors': 0,
            'error_details': []
        }
        
        try:
            self.logger.sync_start("bidirectional")
            
            # 1. Test connections
            if not self._test_connections():
                raise Exception("Connection tests failed")
            
            # 2. Fetch all records
            supabase_records = self._fetch_supabase_records()
            notion_records = self._fetch_notion_records()
            
            stats['supabase_count'] = len(supabase_records)
            stats['notion_count'] = len(notion_records)
            
            # 3. Compute sync differences
            delta = self._compute_differences(supabase_records, notion_records)
            
            # 4. Apply changes
            applied_stats = self._apply_changes(delta)
            stats.update(applied_stats)
            
            # 5. Calculate duration
            end_time = datetime.now()
            stats['duration'] = (end_time - start_time).total_seconds()
            stats['end_time'] = end_time.isoformat()
            
            # 6. Save health status
            self._save_health_status(stats)
            
            self.logger.sync_complete(stats)
            return stats
            
        except Exception as e:
            stats['errors'] = 1
            stats['error_details'].append(str(e))
            stats['duration'] = (datetime.now() - start_time).total_seconds()
            
            self.logger.sync_error(e, "bidirectional sync")
            self._save_health_status(stats)
            raise
    
    def _test_connections(self) -> bool:
        """Test connections to both services"""
        
        self.logger.info("🔍 Testing service connections...")
        
        try:
            supabase_ok = self.supabase.test_connection()
            notion_ok = self.notion.test_connection()
            
            if not supabase_ok:
                self.logger.error("❌ Supabase connection failed")
                return False
            
            if not notion_ok:
                self.logger.error("❌ Notion connection failed")
                return False
            
            self.logger.info("✅ All service connections successful")
            return True
            
        except Exception as e:
            self.logger.error("❌ Connection test failed", error=e)
            return False
    
    def _fetch_supabase_records(self) -> List[Dict[str, Any]]:
        """Fetch all records from Supabase"""
        
        self.logger.info("📥 Fetching Supabase records...")
        
        try:
            records = self.supabase.fetch_all_records()
            
            # Compute checksums for records missing them
            updated_records = []
            for record in records:
                if not record.get('checksum'):
                    record['checksum'] = self.diff_engine.compute_checksum(record)
                    # Update in database if not dry run
                    if not self.dry_run:
                        self.supabase.upsert_record(record)
                
                updated_records.append(record)
            
            self.logger.info(f"✅ Fetched {len(updated_records)} Supabase records")
            return updated_records
            
        except Exception as e:
            self.logger.error("❌ Failed to fetch Supabase records", error=e)
            raise
    
    def _fetch_notion_records(self) -> List[Dict[str, Any]]:
        """Fetch all records from Notion"""
        
        self.logger.info("📥 Fetching Notion records...")
        
        try:
            pages = self.notion.fetch_all_pages()
            
            # Parse pages to record format
            records = []
            for page in pages:
                try:
                    record = self.notion.parse_page_to_record(page)
                    
                    # Compute checksum if missing
                    if not record.get('checksum'):
                        record['checksum'] = self.diff_engine.compute_checksum(record)
                    
                    # Validate record
                    if self.diff_engine.validate_record(record):
                        records.append(record)
                    else:
                        self.logger.warning(f"⚠️ Skipping invalid Notion record: {page.get('id')}")
                        
                except Exception as e:
                    self.logger.error(f"❌ Failed to parse Notion page: {page.get('id')}", error=e)
                    continue
            
            self.logger.info(f"✅ Fetched {len(records)} valid Notion records")
            return records
            
        except Exception as e:
            self.logger.error("❌ Failed to fetch Notion records", error=e)
            raise
    
    def _compute_differences(self, supabase_records: List[Dict[str, Any]], notion_records: List[Dict[str, Any]]) -> SyncDelta:
        """Compute sync differences"""
        
        self.logger.info("🔍 Computing sync differences...")
        
        try:
            delta = self.diff_engine.compute_sync_delta(supabase_records, notion_records)
            
            if self.dry_run:
                self._print_dry_run_plan(delta)
            
            return delta
            
        except Exception as e:
            self.logger.error("❌ Failed to compute differences", error=e)
            raise
    
    def _apply_changes(self, delta: SyncDelta) -> Dict[str, int]:
        """Apply sync changes"""
        
        if delta.total_changes == 0:
            self.logger.info("ℹ️ No changes to apply")
            return {'created': 0, 'updated': 0, 'deleted': 0}
        
        self.logger.info(f"📝 Applying {delta.total_changes} changes...")
        
        stats = {'created': 0, 'updated': 0, 'deleted': 0}
        
        try:
            # 1. Create records in Supabase
            for notion_record in delta.create_in_supabase:
                try:
                    created = self.supabase.upsert_record(notion_record, self.dry_run)
                    if created:
                        stats['created'] += 1
                except Exception as e:
                    self.logger.error("❌ Failed to create in Supabase", error=e, record=notion_record.get('notion_page_id'))
            
            # 2. Create records in Notion
            for sb_record in delta.create_in_notion:
                try:
                    created_page = self.notion.create_page(sb_record, self.dry_run)
                    if created_page and not self.dry_run:
                        # Update Supabase with notion_page_id
                        self.supabase.mark_synced(sb_record['id'], created_page['id'])
                    stats['created'] += 1
                except Exception as e:
                    self.logger.error("❌ Failed to create in Notion", error=e, record=sb_record.get('id'))
            
            # 3. Update records in Supabase
            for current, new in delta.update_in_supabase:
                try:
                    updated = self.supabase.upsert_record(new, self.dry_run)
                    if updated:
                        stats['updated'] += 1
                except Exception as e:
                    self.logger.error("❌ Failed to update in Supabase", error=e, record=current.get('id'))
            
            # 4. Update records in Notion
            for current, new in delta.update_in_notion:
                try:
                    updated_page = self.notion.update_page(current['notion_page_id'], new, self.dry_run)
                    if updated_page:
                        stats['updated'] += 1
                except Exception as e:
                    self.logger.error("❌ Failed to update in Notion", error=e, record=current.get('notion_page_id'))
            
            self.logger.info(f"✅ Applied changes", **stats)
            return stats
            
        except Exception as e:
            self.logger.error("❌ Failed to apply changes", error=e)
            raise
    
    def _print_dry_run_plan(self, delta: SyncDelta):
        """Print dry run execution plan"""
        
        print("\n" + "="*60)
        print("🔍 DRY RUN - SYNC EXECUTION PLAN")
        print("="*60)
        
        if delta.total_changes == 0:
            print("ℹ️ No changes needed - databases are in sync")
            print("="*60)
            return
        
        print(f"📊 Total changes: {delta.total_changes}")
        print()
        
        if delta.create_in_supabase:
            print(f"📥 CREATE IN SUPABASE ({len(delta.create_in_supabase)} records):")
            for record in delta.create_in_supabase[:5]:  # Show first 5
                print(f"  • {record.get('decision', 'Unknown')[:50]}...")
            if len(delta.create_in_supabase) > 5:
                print(f"  ... and {len(delta.create_in_supabase) - 5} more")
            print()
        
        if delta.create_in_notion:
            print(f"📤 CREATE IN NOTION ({len(delta.create_in_notion)} records):")
            for record in delta.create_in_notion[:5]:  # Show first 5
                print(f"  • {record.get('decision', 'Unknown')[:50]}...")
            if len(delta.create_in_notion) > 5:
                print(f"  ... and {len(delta.create_in_notion) - 5} more")
            print()
        
        if delta.update_in_supabase:
            print(f"🔄 UPDATE IN SUPABASE ({len(delta.update_in_supabase)} records):")
            for current, new in delta.update_in_supabase[:5]:
                print(f"  • {current.get('decision', 'Unknown')[:50]}...")
            if len(delta.update_in_supabase) > 5:
                print(f"  ... and {len(delta.update_in_supabase) - 5} more")
            print()
        
        if delta.update_in_notion:
            print(f"🔄 UPDATE IN NOTION ({len(delta.update_in_notion)} records):")
            for current, new in delta.update_in_notion[:5]:
                print(f"  • {current.get('decision', 'Unknown')[:50]}...")
            if len(delta.update_in_notion) > 5:
                print(f"  ... and {len(delta.update_in_notion) - 5} more")
            print()
        
        print("="*60)
        print("✅ This is what would happen in a real sync")
        print("="*60)
    
    def _save_health_status(self, stats: Dict[str, Any]):
        """Save health status to file"""
        save_health_status(self.config.health_file, stats)
    
    def get_last_run_stats(self) -> Dict[str, Any]:
        """Get statistics from last sync run"""
        return load_health_status(self.config.health_file) or {}


def main():
    """CLI entry point for sync runner"""
    
    parser = argparse.ArgumentParser(description="Bidirectional Supabase-Notion Sync")
    parser.add_argument('--dry-run', action='store_true', help='Show what would be synced without making changes')
    parser.add_argument('--report', action='store_true', help='Show last sync run statistics')
    
    args = parser.parse_args()
    
    try:
        if args.report:
            # Show last run report
            sync_runner = BidirectionalSync()
            stats = sync_runner.get_last_run_stats()
            
            if not stats:
                print("📊 No previous sync runs found")
                return 0
            
            print("\n" + "="*50)
            print("📊 LAST SYNC RUN REPORT")
            print("="*50)
            print(f"🕐 Last Run: {stats.get('last_run', 'Unknown')}")
            print(f"📊 Status: {stats.get('status', 'Unknown').upper()}")
            print(f"⏱️ Duration: {stats.get('duration_seconds', 0):.2f} seconds")
            print()
            print("📈 STATISTICS:")
            statistics = stats.get('statistics', {})
            print(f"  Supabase Records: {statistics.get('supabase_records', 0)}")
            print(f"  Notion Records: {statistics.get('notion_records', 0)}")
            print(f"  Created: {statistics.get('created', 0)}")
            print(f"  Updated: {statistics.get('updated', 0)}")
            print(f"  Errors: {statistics.get('errors', 0)}")
            
            if statistics.get('errors', 0) > 0:
                print("\n❌ ERROR DETAILS:")
                for error in stats.get('error_details', []):
                    print(f"  • {error}")
            
            print("="*50)
            return 0
        
        # Run sync
        sync_runner = BidirectionalSync(dry_run=args.dry_run)
        result = sync_runner.run_sync()
        
        if args.dry_run:
            print(f"\n✅ Dry run completed - {result.get('duration', 0):.2f}s")
        else:
            print(f"\n✅ Sync completed - {result.get('duration', 0):.2f}s")
            print(f"📊 Created: {result.get('created', 0)}, Updated: {result.get('updated', 0)}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Sync interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Sync failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())