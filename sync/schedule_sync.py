#!/usr/bin/env python3
"""
Scheduler for automated bidirectional sync
Runs sync every 15 minutes with built-in scheduling for Angles AI Universe™

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import argparse
import sys
import time
from datetime import datetime, timezone

from .config import get_config
from .logging_util import get_logger
from .run_sync import BidirectionalSync


class SyncScheduler:
    """Scheduler for automated sync operations"""
    
    def __init__(self):
        """Initialize sync scheduler"""
        self.config = get_config()
        self.logger = get_logger()
        self.sync_runner = BidirectionalSync()
        
        self.logger.info(f"⏰ Sync scheduler initialized (interval: {self.config.sync_interval} minutes)")
    
    def run_scheduled_sync(self):
        """Run a single scheduled sync"""
        
        self.logger.info("🔄 Starting scheduled sync...")
        
        try:
            result = self.sync_runner.run_sync()
            
            self.logger.info(
                f"✅ Scheduled sync completed successfully",
                duration=result.get('duration', 0),
                created=result.get('created', 0),
                updated=result.get('updated', 0),
                errors=result.get('errors', 0)
            )
            
        except Exception as e:
            self.logger.error("❌ Scheduled sync failed", error=e)
    
    def start_scheduler(self):
        """Start the continuous scheduler"""
        
        self.logger.info(f"🚀 Starting sync scheduler (every {self.config.sync_interval} minutes)")
        
        try:
            last_run = None
            interval_seconds = self.config.sync_interval * 60
            
            while True:
                now = datetime.now(timezone.utc)
                
                # Check if it's time to run
                if (last_run is None or 
                    (now - last_run).total_seconds() >= interval_seconds):
                    
                    self.run_scheduled_sync()
                    last_run = now
                
                # Sleep for 1 minute before checking again
                time.sleep(60)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Sync scheduler stopped by user")
        except Exception as e:
            self.logger.error("💥 Sync scheduler error", error=e)
            raise


def main():
    """CLI entry point for sync scheduler"""
    
    parser = argparse.ArgumentParser(description="Automated Supabase-Notion Sync Scheduler")
    parser.add_argument('--once', action='store_true', help='Run sync once and exit')
    
    args = parser.parse_args()
    
    try:
        scheduler = SyncScheduler()
        
        if args.once:
            print("🔄 Running sync once...")
            scheduler.run_scheduled_sync()
            print("✅ Sync completed")
            return 0
        else:
            print(f"⏰ Starting automated sync scheduler...")
            print(f"📅 Sync interval: {scheduler.config.sync_interval} minutes")
            print("🔄 Press Ctrl+C to stop")
            scheduler.start_scheduler()
            return 0
            
    except KeyboardInterrupt:
        print("\n🛑 Scheduler stopped by user")
        return 130
    except Exception as e:
        print(f"\n💥 Scheduler failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())