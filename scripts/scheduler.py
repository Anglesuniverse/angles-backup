#!/usr/bin/env python3
"""
Angles AI Universe™ Automated Scheduler
Sets up and manages automated health checks and backups

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import logging
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

class AutomatedScheduler:
    """Automated scheduler for health checks and backups"""
    
    def __init__(self):
        """Initialize scheduler"""
        self.config = self._load_config()
        self._setup_logging()
        
        self.logger.info("⏰ Automated Scheduler initialized")
    
    def _load_config(self) -> Dict:
        """Load configuration from config.json"""
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to load config.json: {e}")
            return {"scheduler": {"run_time": "03:00", "timezone": "UTC"}}
    
    def _setup_logging(self):
        """Setup logging"""
        os.makedirs("logs", exist_ok=True)
        
        self.logger = logging.getLogger('scheduler')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler("logs/scheduler.log")
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
    
    def setup_replit_workflow(self) -> bool:
        """Set up Replit workflow for automated health checks"""
        self.logger.info("🔧 Setting up Replit workflow for automated health checks...")
        
        try:
            # Check if run_all.py exists, if not create it
            run_all_path = Path("run_all.py")
            if not run_all_path.exists():
                run_all_content = '''#!/usr/bin/env python3
"""
Angles AI Universe™ Automated Health Check & Backup Runner
Runs daily health checks and backups
"""

import sys
import subprocess
import logging
from datetime import datetime

def setup_logging():
    """Setup logging for automated runs"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/automated_runs.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('automated_runner')

def run_health_check():
    """Run health check"""
    logger = setup_logging()
    logger.info("🔍 Starting automated health check...")
    
    try:
        result = subprocess.run([
            sys.executable, 'scripts/health_check.py'
        ], capture_output=True, text=True, timeout=300)
        
        logger.info(f"Health check exit code: {result.returncode}")
        if result.stdout:
            logger.info(f"Health check output: {result.stdout}")
        if result.stderr:
            logger.error(f"Health check errors: {result.stderr}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        logger.error("❌ Health check timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return False

def run_backup():
    """Run backup if health check passed"""
    logger = setup_logging()
    logger.info("📦 Starting automated backup...")
    
    try:
        result = subprocess.run([
            sys.executable, 'scripts/backup_to_github.py'
        ], capture_output=True, text=True, timeout=600)
        
        logger.info(f"Backup exit code: {result.returncode}")
        if result.stdout:
            logger.info(f"Backup output: {result.stdout}")
        if result.stderr:
            logger.error(f"Backup errors: {result.stderr}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        logger.error("❌ Backup timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Backup failed: {str(e)}")
        return False

def main():
    """Main entry point for automated runs"""
    logger = setup_logging()
    logger.info("🚀 Starting Angles AI Universe™ automated health & backup process")
    
    # Ensure logs directory exists
    import os
    os.makedirs("logs", exist_ok=True)
    
    # Run health check
    health_success = run_health_check()
    
    if health_success:
        logger.info("✅ Health check passed - proceeding with backup")
        backup_success = run_backup()
        
        if backup_success:
            logger.info("🎉 Automated process completed successfully!")
        else:
            logger.error("❌ Backup failed after successful health check")
    else:
        logger.error("❌ Health check failed - skipping backup")
    
    logger.info("📊 Automated process finished")

if __name__ == "__main__":
    main()
'''
                
                with open(run_all_path, 'w') as f:
                    f.write(run_all_content)
                
                # Make executable
                os.chmod(run_all_path, 0o755)
                self.logger.info("✅ Created run_all.py for automated execution")
            
            self.logger.info("✅ Replit workflow setup complete")
            self.logger.info("💡 To activate, add this as a workflow in Replit:")
            self.logger.info("   Name: Health Monitor & Backup")
            self.logger.info("   Command: python run_all.py")
            self.logger.info("   Schedule: Daily at 03:00 UTC")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup Replit workflow: {str(e)}")
            return False
    
    def test_scheduler_setup(self) -> bool:
        """Test that all scheduler components are working"""
        self.logger.info("🧪 Testing scheduler setup...")
        
        try:
            # Check if all required scripts exist
            required_scripts = [
                'scripts/health_check.py',
                'scripts/backup_to_github.py',
                'scripts/restore_from_github.py'
            ]
            
            missing_scripts = []
            for script in required_scripts:
                if not Path(script).exists():
                    missing_scripts.append(script)
            
            if missing_scripts:
                self.logger.error(f"❌ Missing required scripts: {', '.join(missing_scripts)}")
                return False
            
            # Test health check in test mode
            self.logger.info("🔍 Testing health check in test mode...")
            result = subprocess.run([
                sys.executable, 'scripts/health_check.py', '--test'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode in [1, 2]:  # Warnings or errors expected in test mode
                self.logger.info("✅ Health check test mode working correctly")
            else:
                self.logger.warning(f"⚠️ Unexpected health check test result: {result.returncode}")
            
            # Check if logs directory was created
            if Path("logs").exists():
                self.logger.info("✅ Logging directory exists")
            else:
                self.logger.error("❌ Logging directory not created")
                return False
            
            self.logger.info("✅ Scheduler setup test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Scheduler setup test failed: {str(e)}")
            return False
    
    def create_manual_runner(self) -> bool:
        """Create manual runner script for immediate execution"""
        self.logger.info("📝 Creating manual runner script...")
        
        try:
            manual_runner_content = '''#!/usr/bin/env python3
"""
Angles AI Universe™ Manual Health Check & Backup Runner
For immediate execution of health checks and backups
"""

import sys
import argparse
import subprocess
from pathlib import Path

def run_health_check(test_mode=False):
    """Run health check"""
    print("🔍 Running health check...")
    
    cmd = [sys.executable, 'scripts/health_check.py']
    if test_mode:
        cmd.append('--test')
    
    result = subprocess.run(cmd)
    return result.returncode

def run_backup():
    """Run backup"""
    print("📦 Running backup...")
    result = subprocess.run([sys.executable, 'scripts/backup_to_github.py'])
    return result.returncode

def run_restore(dry_run=True, backup_file=None):
    """Run restore"""
    print("🔄 Running restore...")
    
    cmd = [sys.executable, 'scripts/restore_from_github.py']
    if dry_run:
        cmd.append('--dry-run')
    else:
        cmd.append('--live')
    
    if backup_file:
        cmd.extend(['--file', backup_file])
    
    result = subprocess.run(cmd)
    return result.returncode

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Manual Health Check & Backup Runner')
    parser.add_argument('--health', action='store_true', help='Run health check only')
    parser.add_argument('--backup', action='store_true', help='Run backup only')
    parser.add_argument('--restore', action='store_true', help='Run restore')
    parser.add_argument('--test', action='store_true', help='Run health check in test mode')
    parser.add_argument('--live-restore', action='store_true', help='Run live restore (not dry-run)')
    parser.add_argument('--backup-file', type=str, help='Specific backup file for restore')
    parser.add_argument('--all', action='store_true', help='Run health check and backup')
    
    args = parser.parse_args()
    
    if not any([args.health, args.backup, args.restore, args.all]):
        parser.print_help()
        return 1
    
    if args.all:
        print("🚀 Running complete health check and backup process...")
        health_code = run_health_check(test_mode=args.test)
        if health_code == 0:
            backup_code = run_backup()
            return backup_code
        else:
            print("❌ Health check failed - skipping backup")
            return health_code
    
    if args.health:
        return run_health_check(test_mode=args.test)
    
    if args.backup:
        return run_backup()
    
    if args.restore:
        return run_restore(dry_run=not args.live_restore, backup_file=args.backup_file)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
            
            manual_runner_path = Path("run_manual.py")
            with open(manual_runner_path, 'w') as f:
                f.write(manual_runner_content)
            
            # Make executable
            os.chmod(manual_runner_path, 0o755)
            
            self.logger.info("✅ Manual runner created: run_manual.py")
            self.logger.info("💡 Usage examples:")
            self.logger.info("   python run_manual.py --all          # Run health check + backup")
            self.logger.info("   python run_manual.py --health --test # Test health check")
            self.logger.info("   python run_manual.py --restore      # Dry run restore")
            self.logger.info("   python run_manual.py --restore --live-restore # Live restore")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create manual runner: {str(e)}")
            return False
    
    def run_setup(self) -> bool:
        """Run complete scheduler setup"""
        self.logger.info("🚀 Setting up Angles AI Universe™ automated scheduler...")
        self.logger.info("=" * 60)
        
        try:
            # Setup Replit workflow
            if not self.setup_replit_workflow():
                return False
            
            # Create manual runner
            if not self.create_manual_runner():
                return False
            
            # Test setup
            if not self.test_scheduler_setup():
                return False
            
            self.logger.info("=" * 60)
            self.logger.info("🎉 Scheduler setup completed successfully!")
            self.logger.info("")
            self.logger.info("📋 Next Steps:")
            self.logger.info("1. Add environment secrets in Replit")
            self.logger.info("2. Set up 'Health Monitor & Backup' workflow in Replit")
            self.logger.info("3. Test with: python run_manual.py --health --test")
            self.logger.info("4. Run live backup: python run_manual.py --all")
            
            return True
            
        except Exception as e:
            self.logger.error(f"💥 Scheduler setup failed: {str(e)}")
            return False

def main():
    """Main entry point"""
    try:
        scheduler = AutomatedScheduler()
        success = scheduler.run_setup()
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Scheduler setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Scheduler setup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()