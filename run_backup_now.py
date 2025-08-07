#!/usr/bin/env python3
"""
Manual Backup Runner for Angles AI Universe™ Memory System
Runs GitHub backup operations with comprehensive logging

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

def setup_logging() -> logging.Logger:
    """Setup backup-specific logging"""
    # Ensure logs directory exists
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger('backup_runner')
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Rotating file handler for backup logs
    file_handler = RotatingFileHandler(
        'logs/backup.log',
        maxBytes=1024*1024,  # 1MB
        backupCount=10,
        encoding='utf-8'
    )
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

def run_backup():
    """Run GitHub backup operation"""
    logger = setup_logging()
    start_time = datetime.now()
    
    print()
    print("🔄 ANGLES AI UNIVERSE™ BACKUP RUNNER")
    print("=" * 50)
    print(f"Timestamp: {start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print()
    
    logger.info("Starting manual backup operation")
    
    try:
        # Import backup agent class directly for better control
        from backup.git_backup import GitBackupAgent
        
        logger.info("Initializing GitHub backup agent")
        backup_agent = GitBackupAgent()
        
        # Look for export files only (not logs)
        export_files = list(Path('export').glob('*.json'))
        
        if not export_files:
            logger.info("No export files found to backup")
            print("✅ BACKUP COMPLETED (No files to backup)")
            print(f"   • No export files found in export/ directory")
            print(f"   • This is normal if no recent exports were created")
            print("=" * 50)
            return True
        
        logger.info(f"Found {len(export_files)} export files to backup")
        
        # Run backup with export files only (no log files)
        result = backup_agent.backup_files([str(f) for f in export_files], log_files=None)
        
        if result['success']:
            logger.info(f"Backup successful: {result['message']}")
        else:
            logger.error(f"Backup failed: {result.get('error', 'Unknown error')}")
            return False
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Backup completed successfully in {duration:.2f} seconds")
        
        print("✅ BACKUP SUCCESSFUL")
        print(f"   • Duration: {duration:.2f} seconds")
        print(f"   • Files backed up: {result.get('files_backed_up', len(export_files))}")
        print(f"   • Destination: GitHub repository")
        print(f"   • Local logs: logs/backup.log")
        print("=" * 50)
        
        return True
            
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ Backup error: {e} after {duration:.2f} seconds")
        
        print("❌ BACKUP ERROR")
        print(f"   • Error: {e}")
        print(f"   • Duration: {duration:.2f} seconds")
        print(f"   • Check logs/backup.log for details")
        print("=" * 50)
        
        return False

def main():
    """Main entry point"""
    try:
        success = run_backup()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n❌ Backup interrupted by user")
        logging.getLogger('backup_runner').info("Backup interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        print(f"💥 FATAL ERROR: {e}")
        logging.getLogger('backup_runner').error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()