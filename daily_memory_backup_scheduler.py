#!/usr/bin/env python3
"""
MemorySyncAgent™ Daily Backup Scheduler
Scheduled service that runs daily memory backups at 03:00 UTC

This service:
- Runs daily at 03:00 UTC
- Executes memory backup to Supabase
- Handles scheduling and error recovery
- Provides status monitoring

Author: Angles AI Universe™ Backend Team
Version: 2.0.0
"""

import os
import sys
import time
import signal
import logging
try:
    import schedule
except ImportError:
    schedule = None
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

class DailyBackupScheduler:
    """Scheduler for daily memory backups"""
    
    def __init__(self):
        """Initialize the scheduler"""
        self.logger = self._setup_logging()
        self.running = False
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("📅 MEMORYSYNCAGENT™ DAILY BACKUP SCHEDULER INITIALIZED")
        self.logger.info("=" * 60)
        self.logger.info("⏰ Scheduled time: 03:00 UTC daily")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup scheduler-specific logging"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('memory_backup_scheduler')
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler('logs/memory_backup_scheduler.log')
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def _run_backup(self):
        """Execute the daily backup"""
        try:
            self.logger.info("🚀 Executing scheduled daily memory backup...")
            
            # Run backup script
            result = subprocess.run(
                [sys.executable, 'backup_memory_to_supabase.py'],
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            if result.returncode == 0:
                self.logger.info("✅ Daily backup completed successfully")
                if result.stdout:
                    self.logger.info(f"Backup output: {result.stdout.strip()}")
            else:
                self.logger.error("❌ Daily backup failed")
                if result.stderr:
                    self.logger.error(f"Backup error: {result.stderr.strip()}")
                
        except subprocess.TimeoutExpired:
            self.logger.error("❌ Daily backup timed out after 30 minutes")
        except Exception as e:
            self.logger.error(f"❌ Error executing daily backup: {e}")
    
    def start(self):
        """Start the scheduler"""
        if not schedule:
            self.logger.error("Schedule library not available, please install with: pip install schedule")
            return
            
        self.running = True
        
        # Schedule daily backup at 03:00 UTC
        schedule.every().day.at("03:00").do(self._run_backup)
        
        self.logger.info("🚀 Daily backup scheduler started")
        self.logger.info("⏰ Next backup scheduled for 03:00 UTC")
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.logger.info("Scheduler interrupted by user")
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")
        finally:
            self._shutdown()
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
    
    def _shutdown(self):
        """Perform cleanup on shutdown"""
        self.logger.info("🛑 Daily backup scheduler shutting down...")
        self.logger.info("✅ Scheduler shutdown complete")

def main():
    """Main entry point for the scheduler"""
    try:
        print()
        print("📅 MEMORYSYNCAGENT™ DAILY BACKUP SCHEDULER")
        print("=" * 50)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print("⏰ Scheduled time: 03:00 UTC daily")
        print(f"📝 Logs: logs/memory_backup_scheduler.log")
        print("🔄 Status: Running...")
        print()
        
        scheduler = DailyBackupScheduler()
        scheduler.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Scheduler interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"💥 Scheduler failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()