#!/usr/bin/env python3
"""
Manual Weekly Recovery Test Runner
Allows manual execution of the weekly memory recovery test cycle

This is a convenience script for running the weekly test cycle on-demand
without waiting for the scheduled time.

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from weekly_recovery_scheduler import WeeklyRecoveryScheduler

def main():
    """Run weekly recovery test cycle manually"""
    try:
        print("🧪 MANUAL WEEKLY RECOVERY TEST")
        print("=" * 40)
        print("Running weekly memory recovery test cycle...")
        print()
        
        # Create scheduler and run test cycle
        scheduler = WeeklyRecoveryScheduler()
        scheduler.run_weekly_test_cycle()
        
        print()
        print("✅ Weekly recovery test cycle completed!")
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Test cycle interrupted by user")
        return 130
    except Exception as e:
        print(f"💥 Test cycle failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())