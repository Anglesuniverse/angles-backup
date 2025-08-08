#!/usr/bin/env python3
"""
Daily Backup Scheduler for Angles AI Universe™ Memory System
Runs backup at 02:00 UTC daily with cron-like functionality

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import time
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

def setup_logging():
    """Setup scheduler logging"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger('backup_scheduler')
    logger.setLevel(logging.INFO)
    
    # File handler
    file_handler = logging.FileHandler('logs/backup_scheduler.log')
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

def is_backup_time():
    """Check if current time is 02:00 UTC"""
    now = datetime.now(timezone.utc)
    return now.hour == 2 and now.minute == 0

def run_backup_job(logger):
    """Execute the backup job"""
    logger.info("🔄 Executing daily backup job")
    
    try:
        result = subprocess.run([
            sys.executable, 'run_backup_now.py'
        ], capture_output=True, text=True, timeout=600)  # 10 minute timeout
        
        if result.returncode == 0:
            logger.info("✅ Daily backup completed successfully")
            return True
        else:
            logger.error(f"❌ Daily backup failed with exit code: {result.returncode}")
            if result.stderr:
                logger.error(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Daily backup timed out after 10 minutes")
        return False
    except Exception as e:
        logger.error(f"❌ Daily backup error: {e}")
        return False

def main():
    """Main scheduler loop"""
    logger = setup_logging()
    
    logger.info("🕐 Daily Backup Scheduler started")
    logger.info("⏰ Scheduled time: 02:00 UTC daily")
    
    print("🕐 ANGLES AI UNIVERSE™ DAILY BACKUP SCHEDULER")
    print("=" * 55)
    print("⏰ Scheduled time: 02:00 UTC daily")
    print("📝 Logs: logs/backup_scheduler.log")
    print("🔄 Status: Running...")
    print()
    
    last_backup_date = None
    
    try:
        while True:
            now = datetime.now(timezone.utc)
            current_date = now.date()
            
            # Check if it's backup time and we haven't run today
            if is_backup_time() and last_backup_date != current_date:
                logger.info(f"⏰ Backup time reached: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                
                success = run_backup_job(logger)
                last_backup_date = current_date
                
                if success:
                    logger.info("✅ Daily backup cycle completed")
                else:
                    logger.error("❌ Daily backup cycle failed")
            
            # Sleep for 60 seconds before checking again
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("🛑 Daily backup scheduler stopped by user")
        print("🛑 Scheduler stopped by user")
    except Exception as e:
        logger.error(f"💥 Scheduler error: {e}")
        print(f"💥 Scheduler error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()