"""
Cron Runner for Angles AI Universe™
Scheduled task management and automation
"""

import time
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, Any

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    schedule = None

from .memory_sync_agent import MemorySyncAgent
from .historical_sweep import HistoricalSweep
from .restore import BackupRestore
from .backend_monitor import BackendMonitor
from .config import print_config_status


logger = logging.getLogger(__name__)


class CronRunner:
    """Scheduled task runner with job management"""
    
    def __init__(self):
        self.running = False
        self.jobs_run = 0
        self.last_error = None
        
        # Initialize components
        self.memory_sync = MemorySyncAgent()
        self.historical_sweep = HistoricalSweep()
        self.backup_restore = BackupRestore()
        self.backend_monitor = BackendMonitor()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"📶 Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def job_wrapper(self, job_name: str, job_func):
        """Wrapper for scheduled jobs with error handling"""
        def wrapper():
            start_time = datetime.now()
            logger.info(f"🔄 Starting job: {job_name}")
            
            try:
                success = job_func()
                duration = (datetime.now() - start_time).total_seconds()
                
                if success:
                    logger.info(f"✅ Job completed: {job_name} ({duration:.1f}s)")
                else:
                    logger.error(f"❌ Job failed: {job_name} ({duration:.1f}s)")
                    self.last_error = f"{job_name} failed"
                
                self.jobs_run += 1
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"💥 Job crashed: {job_name} ({duration:.1f}s) - {e}")
                self.last_error = f"{job_name} crashed: {e}"
        
        return wrapper
    
    def setup_schedule(self):
        """Setup scheduled jobs"""
        if not SCHEDULE_AVAILABLE:
            logger.error("❌ Schedule library not available")
            logger.error("   Please install with: pip install schedule")
            return False
        
        logger.info("⏰ Setting up scheduled jobs...")
        
        # Memory Sync Agent: every 6 hours
        schedule.every(6).hours.do(
            self.job_wrapper('MemorySyncAgent', self.memory_sync.run_sync)
        ).tag('memory_sync')
        
        # Historical Sweep: Sundays at 02:00 UTC  
        schedule.every().sunday.at("02:00").do(
            self.job_wrapper('HistoricalSweep', self.historical_sweep.run_historical_sweep)
        ).tag('historical_sweep')
        
        # Backup/Restore (export): daily at 03:00 UTC
        schedule.every().day.at("03:00").do(
            self.job_wrapper('BackupRestore', self.backup_restore.run_backup)
        ).tag('backup')
        
        # Backend Monitor: every hour
        schedule.every().hour.do(
            self.job_wrapper('BackendMonitor', self.backend_monitor.run_monitor)
        ).tag('monitor')
        
        # Print scheduled jobs
        jobs = schedule.get_jobs()
        logger.info(f"📅 Configured {len(jobs)} scheduled jobs:")
        
        for job in jobs:
            next_run = job.next_run.strftime('%Y-%m-%d %H:%M:%S UTC') if job.next_run else 'Never'
            logger.info(f"   🔹 {', '.join(job.tags)}: {next_run}")
        
        return True
    
    def run_scheduler(self):
        """Run the main scheduler loop"""
        logger.info("🚀 Starting Cron Runner")
        print_config_status()
        
        if not self.setup_schedule():
            return False
        
        # Run initial health check
        logger.info("🏥 Running initial health check...")
        try:
            self.backend_monitor.run_monitor()
        except Exception as e:
            logger.warning(f"Initial health check failed: {e}")
        
        self.running = True
        logger.info("⏰ Scheduler is now running... (Press Ctrl+C to stop)")
        
        try:
            while self.running:
                # Run pending jobs
                schedule.run_pending()
                
                # Sleep for a short interval
                time.sleep(60)  # Check every minute
                
                # Periodic status update (every hour)
                if self.jobs_run > 0 and self.jobs_run % 60 == 0:
                    self.print_status()
                    
        except KeyboardInterrupt:
            logger.info("📶 Interrupted by user")
        except Exception as e:
            logger.error(f"💥 Scheduler error: {e}")
        finally:
            logger.info("🛑 Cron Runner stopped")
            self.print_final_stats()
        
        return True
    
    def print_status(self):
        """Print current scheduler status"""
        logger.info("📊 Scheduler Status:")
        logger.info(f"   🔄 Jobs run: {self.jobs_run}")
        logger.info(f"   ⚠️ Last error: {self.last_error or 'None'}")
        logger.info(f"   ⏰ Next jobs:")
        
        jobs = schedule.get_jobs()
        for job in jobs[:3]:  # Show next 3 jobs
            next_run = job.next_run.strftime('%Y-%m-%d %H:%M:%S UTC') if job.next_run else 'Never'
            logger.info(f"      🔹 {', '.join(job.tags)}: {next_run}")
    
    def print_final_stats(self):
        """Print final statistics"""
        logger.info("📈 Final Statistics:")
        logger.info(f"   🔄 Total jobs run: {self.jobs_run}")
        logger.info(f"   ⚠️ Last error: {self.last_error or 'None'}")
        logger.info("   📋 Thanks for using Angles AI Universe™ Scheduler!")
    
    def run_job_now(self, job_name: str) -> bool:
        """Run a specific job immediately"""
        logger.info(f"🚀 Running job immediately: {job_name}")
        
        job_map = {
            'memory_sync': self.memory_sync.run_sync,
            'historical_sweep': self.historical_sweep.run_historical_sweep,
            'backup': self.backup_restore.run_backup,
            'monitor': self.backend_monitor.run_monitor
        }
        
        if job_name not in job_map:
            logger.error(f"❌ Unknown job: {job_name}")
            logger.info(f"   Available jobs: {', '.join(job_map.keys())}")
            return False
        
        try:
            success = job_map[job_name]()
            if success:
                logger.info(f"✅ Job completed successfully: {job_name}")
            else:
                logger.error(f"❌ Job failed: {job_name}")
            return success
            
        except Exception as e:
            logger.error(f"💥 Job crashed: {job_name} - {e}")
            return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cron Runner - Scheduled task management')
    parser.add_argument('--run-now', choices=['memory_sync', 'historical_sweep', 'backup', 'monitor'],
                       help='Run a specific job immediately')
    parser.add_argument('--list-jobs', action='store_true', help='List configured jobs and exit')
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/cron_runner.log') if Path('logs').exists() else logging.NullHandler()
        ]
    )
    
    try:
        runner = CronRunner()
        
        if args.list_jobs:
            if runner.setup_schedule():
                jobs = schedule.get_jobs() if SCHEDULE_AVAILABLE else []
                print(f"\n📅 Configured Jobs ({len(jobs)}):")
                for job in jobs:
                    next_run = job.next_run.strftime('%Y-%m-%d %H:%M:%S UTC') if job.next_run else 'Never'
                    print(f"   🔹 {', '.join(job.tags)}: {next_run}")
            return 0
        
        if args.run_now:
            success = runner.run_job_now(args.run_now)
            return 0 if success else 1
        
        # Run scheduler
        success = runner.run_scheduler()
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Cron Runner setup failed: {e}")
        return 1


if __name__ == "__main__":
    from pathlib import Path
    exit(main())