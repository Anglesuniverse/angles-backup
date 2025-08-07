#!/usr/bin/env python3
"""
Angles AI Universe™ Sync Scheduler
Lightweight scheduler that runs sync every 2 minutes

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import time
from datetime import datetime
from memory_bridge import sync_all


def run_scheduler():
    """Run sync every 2 minutes continuously"""
    
    print("⏰ ANGLES AI UNIVERSE™ SYNC SCHEDULER")
    print("=" * 45)
    print("🔄 Running sync every 2 minutes...")
    print("📝 Press Ctrl+C to stop")
    print()
    
    try:
        while True:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"🕐 [{current_time}] Starting scheduled sync...")
            
            try:
                sync_all()
                print(f"✅ [{current_time}] Sync completed successfully")
            except Exception as e:
                print(f"❌ [{current_time}] Sync failed: {e}")
            
            print(f"💤 Waiting 2 minutes until next sync...\n")
            time.sleep(120)  # 2 minutes
            
    except KeyboardInterrupt:
        print("\n🛑 Scheduler stopped by user")
    except Exception as e:
        print(f"\n💥 Scheduler error: {e}")


if __name__ == "__main__":
    run_scheduler()