#!/usr/bin/env python3
"""
Angles AI Universe™ Automated Scheduler
Cron-like scheduler for health checks, restores, and log management

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import time
import logging
import subprocess
from datetime import datetime, timezone, timedelta
from typing import Optional

class AutomatedScheduler:
    """Automated scheduler for system maintenance tasks"""
    
    def __init__(self):
        """Initialize automated scheduler"""
        self.setup_logging()
        self.logger.info("⏰ Angles AI Universe™ Automated Scheduler Initialized")
        
        # Track last health check status
        self.last_health_check_passed = True
    
    def setup_logging(self):
        """Setup logging for scheduler"""
        os.makedirs("logs/active", exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger('automated_scheduler')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/active/scheduler.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def run_health_check(self) -> bool:
        """Run health check and return success status"""
        self.logger.info("🔍 Running scheduled health check...")
        
        try:
            result = subprocess.run([
                sys.executable, 'health_check.py'
            ], capture_output=True, text=True, timeout=300)
            
            success = result.returncode == 0
            
            self.logger.info(f"📊 Health check result: {'PASSED' if success else 'FAILED'}")
            if result.stdout:
                self.logger.info(f"Output: {result.stdout.strip()}")
            if result.stderr:
                self.logger.error(f"Errors: {result.stderr.strip()}")
            
            self.last_health_check_passed = success
            return success
            
        except subprocess.TimeoutExpired:
            self.logger.error("❌ Health check timed out")
            self.last_health_check_passed = False
            return False
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {str(e)}")
            self.last_health_check_passed = False
            return False
    
    def run_restore_if_needed(self):
        """Run restore only if health check failed"""
        if self.last_health_check_passed:
            self.logger.info("✅ Health check passed - no restore needed")
            return
        
        self.logger.info("🔄 Health check failed - running restore...")
        
        try:
            result = subprocess.run([
                sys.executable, 'restore_from_github.py'
            ], capture_output=True, text=True, timeout=600)
            
            success = result.returncode == 0
            
            self.logger.info(f"📊 Restore result: {'COMPLETED' if success else 'FAILED'}")
            if result.stdout:
                self.logger.info(f"Output: {result.stdout.strip()}")
            if result.stderr:
                self.logger.error(f"Errors: {result.stderr.strip()}")
            
        except subprocess.TimeoutExpired:
            self.logger.error("❌ Restore timed out")
        except Exception as e:
            self.logger.error(f"❌ Restore failed: {str(e)}")
    
    def run_log_management(self):
        """Run log management"""
        self.logger.info("📦 Running scheduled log management...")
        
        try:
            result = subprocess.run([
                sys.executable, 'log_manager.py'
            ], capture_output=True, text=True, timeout=300)
            
            success = result.returncode == 0
            
            self.logger.info(f"📊 Log management result: {'COMPLETED' if success else 'FAILED'}")
            if result.stdout:
                self.logger.info(f"Output: {result.stdout.strip()}")
            if result.stderr:
                self.logger.error(f"Errors: {result.stderr.strip()}")
            
        except subprocess.TimeoutExpired:
            self.logger.error("❌ Log management timed out")
        except Exception as e:
            self.logger.error(f"❌ Log management failed: {str(e)}")
    
    def daily_health_and_restore(self):
        """Daily task: health check and conditional restore"""
        self.logger.info("🌅 Starting daily health check and restore cycle")
        
        # Run health check
        health_passed = self.run_health_check()
        
        # Run restore if needed
        self.run_restore_if_needed()
        
        self.logger.info("🌙 Daily cycle completed")
    
    def should_run_daily_task(self) -> bool:
        """Check if daily task should run (at 03:00 UTC)"""
        now = datetime.now(timezone.utc)
        return now.hour == 3 and now.minute == 0
    
    def should_run_weekly_task(self) -> bool:
        """Check if weekly task should run (Sunday 02:00 UTC)"""
        now = datetime.now(timezone.utc)
        return now.weekday() == 6 and now.hour == 2 and now.minute == 0  # Sunday = 6
    
    def run_scheduler(self):
        """Run the scheduler continuously"""
        self.logger.info("🚀 Starting Automated Scheduler")
        self.logger.info("=" * 60)
        
        self.logger.info("✅ Schedule configured:")
        self.logger.info("   📊 Daily health check + restore: 03:00 UTC")
        self.logger.info("   📦 Weekly log management: Sunday 02:00 UTC")
        
        self.logger.info("⏰ Scheduler running... (Press Ctrl+C to stop)")
        
        last_daily_run = None
        last_weekly_run = None
        
        try:
            while True:
                now = datetime.now(timezone.utc)
                current_date = now.date()
                
                # Check for daily task (03:00 UTC)
                if self.should_run_daily_task():
                    if last_daily_run != current_date:
                        self.logger.info("⏰ Time for daily health check and restore")
                        self.daily_health_and_restore()
                        last_daily_run = current_date
                
                # Check for weekly task (Sunday 02:00 UTC)
                if self.should_run_weekly_task():
                    if last_weekly_run != current_date:
                        self.logger.info("⏰ Time for weekly log management")
                        self.run_log_management()
                        last_weekly_run = current_date
                
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"💥 Scheduler error: {str(e)}")

def main():
    """Main entry point"""
    try:
        scheduler = AutomatedScheduler()
        scheduler.run_scheduler()
        
    except Exception as e:
        print(f"💥 Scheduler initialization failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()