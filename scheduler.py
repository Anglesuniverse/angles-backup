#!/usr/bin/env python3
"""
Angles AI Universe™ Unified Scheduler
Automation without external cron dependencies

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import time
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    print("⚠️ Schedule library not available - using built-in time-based scheduling")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def setup_logging():
    """Setup logging for scheduler"""
    os.makedirs("logs/active", exist_ok=True)
    
    logger = logging.getLogger('scheduler')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler
    file_handler = logging.FileHandler('logs/active/scheduler.log')
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

class UnifiedScheduler:
    """Unified scheduler for all automation tasks"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.start_time = datetime.now(timezone.utc)
        
        # Task execution stats
        self.task_stats = {
            'backend_monitor': {'runs': 0, 'failures': 0, 'last_run': None},
            'memory_sync': {'runs': 0, 'failures': 0, 'last_run': None},
            'daily_backup': {'runs': 0, 'failures': 0, 'last_run': None},
            'weekly_restore': {'runs': 0, 'failures': 0, 'last_run': None},
            'autosync': {'runs': 0, 'failures': 0, 'last_run': None}
        }
        
        # Enable/disable flags
        self.enable_backend_monitor = True
        self.enable_memory_sync = True
        self.enable_daily_backup = True
        self.enable_weekly_restore = True
        self.enable_autosync = True
        
        # Built-in scheduler tracking
        self.last_runs = {
            'backend_monitor': 0,
            'memory_sync': 0,
            'daily_backup': 0,
            'weekly_restore': 0,
            'autosync': 0,
            'status_report': 0
        }
        
    def run_command(self, command: List[str], task_name: str, timeout: int = 300) -> bool:
        """Run command with error handling and logging"""
        self.logger.info(f"🚀 Running {task_name}...")
        
        try:
            start_time = datetime.now(timezone.utc)
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path.cwd()
            )
            
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            if result.returncode == 0:
                self.logger.info(f"✅ {task_name} completed successfully in {duration:.2f}s")
                
                # Log output if not empty
                if result.stdout.strip():
                    self.logger.info(f"📄 {task_name} output: {result.stdout.strip()[:200]}...")
                
                self.task_stats[task_name]['runs'] += 1
                self.task_stats[task_name]['last_run'] = start_time.isoformat()
                return True
            else:
                self.logger.error(f"❌ {task_name} failed (exit {result.returncode}) after {duration:.2f}s")
                self.logger.error(f"📄 Error output: {result.stderr.strip()[:200]}...")
                
                self.task_stats[task_name]['runs'] += 1
                self.task_stats[task_name]['failures'] += 1
                self.task_stats[task_name]['last_run'] = start_time.isoformat()
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"⏱️ {task_name} timed out after {timeout}s")
            self.task_stats[task_name]['runs'] += 1
            self.task_stats[task_name]['failures'] += 1
            return False
            
        except Exception as e:
            self.logger.error(f"💥 {task_name} error: {e}")
            self.task_stats[task_name]['runs'] += 1
            self.task_stats[task_name]['failures'] += 1
            return False
    
    def job_backend_monitor(self):
        """Hourly backend health monitoring"""
        if not self.enable_backend_monitor:
            return
        
        self.run_command(
            [sys.executable, 'backend_monitor.py'],
            'backend_monitor',
            timeout=180
        )
    
    def job_memory_sync(self):
        """6-hourly memory sync to Notion"""
        if not self.enable_memory_sync:
            return
        
        self.run_command(
            [sys.executable, 'memory_sync.py', '--sync-decisions'],
            'memory_sync',
            timeout=300
        )
    
    def job_daily_backup(self):
        """Daily backup at 02:00 UTC"""
        if not self.enable_daily_backup:
            return
        
        self.run_command(
            [sys.executable, 'run_backup_now.py'],
            'daily_backup',
            timeout=600
        )
    
    def job_weekly_restore_test(self):
        """Weekly restore verification test"""
        if not self.enable_weekly_restore:
            return
        
        self.run_command(
            [sys.executable, 'restore_from_github.py', '--dry-run'],
            'weekly_restore',
            timeout=300
        )
    
    def job_autosync_files(self):
        """Hourly file change detection"""
        if not self.enable_autosync:
            return
        
        self.run_command(
            [sys.executable, 'autosync_files.py', '--once'],
            'autosync',
            timeout=120
        )
    
    def print_scheduler_status(self):
        """Print current scheduler status"""
        uptime = datetime.now(timezone.utc) - self.start_time
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        
        self.logger.info("=" * 60)
        self.logger.info("📊 SCHEDULER STATUS")
        self.logger.info("=" * 60)
        self.logger.info(f"⏰ Uptime: {uptime_str}")
        self.logger.info(f"🕐 Current time (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Print next scheduled runs
        if SCHEDULE_AVAILABLE:
            self.logger.info("📅 Next scheduled runs:")
            for job in schedule.jobs:
                self.logger.info(f"   • {job.job_func.__name__}: {job.next_run}")
        else:
            self.logger.info("📅 Built-in scheduler running (check logs for task execution)")
        
        # Print task statistics
        self.logger.info("📈 Task Statistics:")
        for task_name, stats in self.task_stats.items():
            if stats['runs'] > 0:
                success_rate = ((stats['runs'] - stats['failures']) / stats['runs']) * 100
                last_run = stats['last_run'][:19] if stats['last_run'] else 'Never'
                self.logger.info(f"   • {task_name}: {stats['runs']} runs, {success_rate:.1f}% success, last: {last_run}")
        
        self.logger.info("=" * 60)
    
    def setup_schedule(self):
        """Setup all scheduled jobs"""
        self.logger.info("⚙️ Setting up scheduled jobs...")
        
        if SCHEDULE_AVAILABLE:
            # Hourly backend monitoring
            if self.enable_backend_monitor:
                schedule.every().hour.do(self.job_backend_monitor)
                self.logger.info("   ✅ Backend monitoring: Every hour")
            
            # 6-hourly memory sync
            if self.enable_memory_sync:
                schedule.every(6).hours.do(self.job_memory_sync)
                self.logger.info("   ✅ Memory sync: Every 6 hours")
            
            # Daily backup at 02:00 UTC
            if self.enable_daily_backup:
                schedule.every().day.at("02:00").do(self.job_daily_backup)
                self.logger.info("   ✅ Daily backup: 02:00 UTC")
            
            # Weekly restore test on Sundays at 03:00 UTC
            if self.enable_weekly_restore:
                schedule.every().sunday.at("03:00").do(self.job_weekly_restore_test)
                self.logger.info("   ✅ Weekly restore test: Sundays 03:00 UTC")
            
            # Hourly file autosync
            if self.enable_autosync:
                schedule.every().hour.do(self.job_autosync_files)
                self.logger.info("   ✅ File autosync: Every hour")
            
            # Status report every 6 hours
            schedule.every(6).hours.do(self.print_scheduler_status)
            self.logger.info("   ✅ Status report: Every 6 hours")
            
            self.logger.info(f"📋 Total scheduled jobs: {len(schedule.jobs)}")
        else:
            self.logger.info("📅 Using built-in time-based scheduling:")
            self.logger.info("   ✅ Backend monitoring: Every hour")
            self.logger.info("   ✅ Memory sync: Every 6 hours")
            self.logger.info("   ✅ Daily backup: 02:00 UTC")
            self.logger.info("   ✅ Weekly restore test: Sundays 03:00 UTC")
            self.logger.info("   ✅ File autosync: Every hour")
            self.logger.info("   ✅ Status report: Every 6 hours")
    
    def run_initial_health_check(self):
        """Run initial health check on startup"""
        self.logger.info("🏥 Running initial health check...")
        
        # Run backend monitor once
        success = self.run_command(
            [sys.executable, 'backend_monitor.py'],
            'backend_monitor',
            timeout=180
        )
        
        if success:
            self.logger.info("✅ Initial health check passed")
        else:
            self.logger.warning("⚠️ Initial health check failed - continuing anyway")
        
        return success
    
    def run_scheduler(self):
        """Run the scheduler main loop"""
        self.logger.info("🚀 Starting Angles AI Universe™ Unified Scheduler")
        self.logger.info(f"📍 Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        self.logger.info("=" * 60)
        
        # Run initial health check
        self.run_initial_health_check()
        
        # Setup scheduled jobs
        self.setup_schedule()
        
        # Print initial status
        self.print_scheduler_status()
        
        # Main scheduler loop
        self.logger.info("🔄 Entering scheduler loop...")
        self.logger.info("🛑 Press Ctrl+C to stop scheduler")
        
        try:
            if SCHEDULE_AVAILABLE:
                while True:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
            else:
                self._run_builtin_scheduler()
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Scheduler stopped by user")
            
        except Exception as e:
            self.logger.error(f"💥 Scheduler error: {e}")
            self.logger.info("🔄 Attempting to restart in 60 seconds...")
            time.sleep(60)
            return self.run_scheduler()  # Restart scheduler
        
        finally:
            # Print final statistics
            self.logger.info("📊 Final scheduler statistics:")
            self.print_scheduler_status()
    
    def _run_builtin_scheduler(self):
        """Built-in scheduler when schedule library is not available"""
        self.logger.info("🔄 Running built-in scheduler...")
        
        while True:
            now = datetime.now(timezone.utc)
            current_hour = now.hour
            current_minute = now.minute
            current_weekday = now.weekday()  # 0=Monday, 6=Sunday
            
            # Every hour tasks (at minute 0)
            if current_minute == 0:
                # Backend monitoring
                if (now.timestamp() - self.last_runs['backend_monitor']) >= 3600:
                    self.job_backend_monitor()
                    self.last_runs['backend_monitor'] = now.timestamp()
                
                # File autosync
                if (now.timestamp() - self.last_runs['autosync']) >= 3600:
                    self.job_autosync_files()
                    self.last_runs['autosync'] = now.timestamp()
            
            # Every 6 hours tasks (at 00:00, 06:00, 12:00, 18:00)
            if current_hour % 6 == 0 and current_minute == 0:
                # Memory sync
                if (now.timestamp() - self.last_runs['memory_sync']) >= 21600:
                    self.job_memory_sync()
                    self.last_runs['memory_sync'] = now.timestamp()
                
                # Status report
                if (now.timestamp() - self.last_runs['status_report']) >= 21600:
                    self.print_scheduler_status()
                    self.last_runs['status_report'] = now.timestamp()
            
            # Daily backup at 02:00 UTC
            if current_hour == 2 and current_minute == 0:
                if (now.timestamp() - self.last_runs['daily_backup']) >= 86400:
                    self.job_daily_backup()
                    self.last_runs['daily_backup'] = now.timestamp()
            
            # Weekly restore test on Sundays at 03:00 UTC
            if current_weekday == 6 and current_hour == 3 and current_minute == 0:
                if (now.timestamp() - self.last_runs['weekly_restore']) >= 604800:
                    self.job_weekly_restore_test()
                    self.last_runs['weekly_restore'] = now.timestamp()
            
            time.sleep(60)  # Check every minute

def main():
    """Main entry point"""
    try:
        scheduler = UnifiedScheduler()
        scheduler.run_scheduler()
        
    except Exception as e:
        print(f"💥 Scheduler startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()