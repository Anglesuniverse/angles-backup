#!/usr/bin/env python3
"""
Manual control tools for Supabase-Notion sync
CLI interface for managing sync operations for Angles AI Universe™

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sync.run_sync import BidirectionalSync
from sync.logging_util import load_health_status


def sync_now():
    """Run sync immediately"""
    print("🔄 Running sync now...")
    
    try:
        sync_runner = BidirectionalSync()
        result = sync_runner.run_sync()
        
        print("\n✅ Sync completed successfully!")
        print(f"⏱️ Duration: {result.get('duration', 0):.2f} seconds")
        print(f"📊 Created: {result.get('created', 0)}")
        print(f"📊 Updated: {result.get('updated', 0)}")
        print(f"📊 Errors: {result.get('errors', 0)}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Sync failed: {e}")
        return 1


def dry_run():
    """Run sync in dry-run mode"""
    print("🔍 Running dry-run sync...")
    
    try:
        sync_runner = BidirectionalSync(dry_run=True)
        result = sync_runner.run_sync()
        
        print(f"\n✅ Dry-run completed in {result.get('duration', 0):.2f} seconds")
        print("ℹ️ No actual changes were made")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Dry-run failed: {e}")
        return 1


def show_report():
    """Show last sync run report"""
    print("📊 Last Sync Run Report")
    print("=" * 40)
    
    try:
        stats = load_health_status("logs/last_success.json")
        
        if not stats:
            print("ℹ️ No previous sync runs found")
            return 0
        
        print(f"🕐 Last Run: {stats.get('last_run', 'Unknown')}")
        print(f"📊 Status: {stats.get('status', 'Unknown').upper()}")
        print(f"⏱️ Duration: {stats.get('duration_seconds', 0):.2f} seconds")
        print()
        
        statistics = stats.get('statistics', {})
        print("📈 Statistics:")
        print(f"  Supabase Records: {statistics.get('supabase_records', 0)}")
        print(f"  Notion Records: {statistics.get('notion_records', 0)}")
        print(f"  Created: {statistics.get('created', 0)}")
        print(f"  Updated: {statistics.get('updated', 0)}")
        print(f"  Errors: {statistics.get('errors', 0)}")
        
        if statistics.get('errors', 0) > 0:
            print("\n❌ Error Details:")
            for error in stats.get('error_details', []):
                print(f"  • {error}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Failed to load report: {e}")
        return 1


def main():
    """Main CLI entry point"""
    
    parser = argparse.ArgumentParser(
        description="Sync Control Tools for Angles AI Universe™",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  sync-now    Run sync immediately
  dry-run     Show what would be synced without making changes
  report      Show last sync run statistics

Examples:
  python tools/controls.py sync-now
  python tools/controls.py dry-run
  python tools/controls.py report
        """
    )
    
    parser.add_argument(
        'command', 
        choices=['sync-now', 'dry-run', 'report'],
        help='Command to execute'
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == 'sync-now':
            return sync_now()
        elif args.command == 'dry-run':
            return dry_run()
        elif args.command == 'report':
            return show_report()
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Operation interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Command failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())