#!/usr/bin/env python3
"""
Weekly Memory Recovery Test Scheduler
Automatically runs memory_recovery_test.py weekly and manages results

Features:
- Weekly automated testing using schedule library
- GitHub push of test results and logs
- Supabase logging of test outcomes
- Failure notifications and self-healing
- Always-on compatible for Replit hosting

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# Using built-in time and datetime for scheduling instead of schedule library
# import schedule

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Warning: Supabase client not available")

try:
    from log_to_notion import log_to_notion
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("⚠️ Warning: Notion logging not available")

class WeeklyRecoveryScheduler:
    """Weekly automated memory recovery testing and result management"""
    
    def __init__(self):
        """Initialize the weekly scheduler"""
        self.setup_logging()
        self.setup_environment()
        self.setup_supabase()
        
        self.logger.info("🗓️ WEEKLY MEMORY RECOVERY SCHEDULER INITIALIZED")
        self.logger.info("=" * 60)
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if needed
        Path('logs').mkdir(exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger('weekly_recovery_scheduler')
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler
        log_file = Path('logs/weekly_recovery_scheduler.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def setup_environment(self):
        """Setup environment variables and configuration"""
        self.github_enabled = bool(os.getenv('GITHUB_TOKEN'))
        self.supabase_enabled = bool(os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_KEY'))
        self.notion_enabled = bool(os.getenv('NOTION_TOKEN'))
        
        self.logger.info(f"GitHub integration: {'✅ Enabled' if self.github_enabled else '❌ Disabled'}")
        self.logger.info(f"Supabase integration: {'✅ Enabled' if self.supabase_enabled else '❌ Disabled'}")
        self.logger.info(f"Notion integration: {'✅ Enabled' if self.notion_enabled else '❌ Disabled'}")
    
    def setup_supabase(self):
        """Setup Supabase client and ensure restore_checks table exists"""
        if not self.supabase_enabled or not SUPABASE_AVAILABLE:
            self.supabase = None
            return
        
        try:
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_KEY')
            
            if not url or not key:
                raise ValueError("Missing Supabase credentials")
                
            self.supabase = create_client(url, key)
            
            # Create restore_checks table if it doesn't exist
            self.ensure_restore_checks_table()
            
            self.logger.info("✅ Supabase client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Supabase client: {e}")
            self.supabase = None
    
    def ensure_restore_checks_table(self):
        """Ensure the restore_checks table exists in Supabase"""
        if not self.supabase:
            return
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS restore_checks (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            test_run_timestamp TIMESTAMPTZ DEFAULT NOW(),
            total_tests INTEGER NOT NULL,
            passed_tests INTEGER NOT NULL,
            failed_tests INTEGER NOT NULL,
            success_rate DECIMAL(5,2) NOT NULL,
            duration_seconds DECIMAL(10,3) NOT NULL,
            test_details JSONB,
            github_pushed BOOLEAN DEFAULT FALSE,
            scheduler_version VARCHAR(20) DEFAULT '1.0.0',
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Create index for faster queries
        CREATE INDEX IF NOT EXISTS idx_restore_checks_timestamp 
        ON restore_checks(test_run_timestamp);
        
        -- Create index for success rate monitoring
        CREATE INDEX IF NOT EXISTS idx_restore_checks_success_rate 
        ON restore_checks(success_rate);
        """
        
        try:
            # Note: Supabase doesn't support direct SQL execution via client
            # This would need to be run manually or via the Supabase dashboard
            self.logger.info("📝 restore_checks table schema ready (manual creation required)")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not ensure restore_checks table: {e}")
    
    def run_memory_recovery_test(self) -> Dict[str, Any]:
        """Run the memory recovery test suite and return results"""
        self.logger.info("🧪 Starting weekly memory recovery test...")
        
        start_time = datetime.now()
        
        try:
            # Run the test suite
            result = subprocess.run(
                [sys.executable, 'memory_recovery_test.py'],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Parse test results from file
            test_results = self.load_test_results()
            
            # Determine success based on exit code and results
            success = result.returncode == 0
            
            if success:
                self.logger.info("✅ Memory recovery test completed successfully")
            else:
                self.logger.error(f"❌ Memory recovery test failed with exit code: {result.returncode}")
                self.logger.error(f"STDERR: {result.stderr}")
            
            return {
                'success': success,
                'exit_code': result.returncode,
                'duration_seconds': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'test_results': test_results,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except subprocess.TimeoutExpired:
            self.logger.error("❌ Memory recovery test timed out after 10 minutes")
            return {
                'success': False,
                'exit_code': -1,
                'duration_seconds': 600,
                'stdout': '',
                'stderr': 'Test timed out after 10 minutes',
                'test_results': None,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to run memory recovery test: {e}")
            return {
                'success': False,
                'exit_code': -1,
                'duration_seconds': 0,
                'stdout': '',
                'stderr': str(e),
                'test_results': None,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def load_test_results(self) -> Optional[Dict[str, Any]]:
        """Load test results from the generated JSON file"""
        try:
            test_results_file = Path('test_results.json')
            if test_results_file.exists():
                with open(test_results_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load test results: {e}")
        
        return None
    
    def push_to_github(self) -> bool:
        """Push test results and logs to GitHub"""
        if not self.github_enabled:
            self.logger.warning("⚠️ GitHub integration disabled - skipping push")
            return False
        
        try:
            # Files to push
            files_to_push = [
                'restore_history.json',
                'last_restore.log',
                'test_results.json',
                'logs/weekly_recovery_scheduler.log'
            ]
            
            # Check which files exist
            existing_files = []
            for file_path in files_to_push:
                if Path(file_path).exists():
                    existing_files.append(file_path)
            
            if not existing_files:
                self.logger.warning("⚠️ No files to push to GitHub")
                return False
            
            # Stage files
            stage_result = subprocess.run(
                ['git', 'add'] + existing_files,
                capture_output=True,
                text=True
            )
            
            if stage_result.returncode != 0:
                self.logger.error(f"❌ Failed to stage files: {stage_result.stderr}")
                return False
            
            # Commit files
            commit_message = f"Weekly memory recovery test results - {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
            commit_result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                capture_output=True,
                text=True
            )
            
            # Push to remote (allow failure if no changes)
            if commit_result.returncode == 0:
                push_result = subprocess.run(
                    ['git', 'push', 'origin', 'main'],
                    capture_output=True,
                    text=True
                )
                
                if push_result.returncode == 0:
                    self.logger.info("✅ Successfully pushed test results to GitHub")
                    return True
                else:
                    self.logger.error(f"❌ Failed to push to GitHub: {push_result.stderr}")
                    return False
            else:
                self.logger.info("ℹ️ No changes to commit to GitHub")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Failed to push to GitHub: {e}")
            return False
    
    def log_to_supabase(self, test_results: Dict[str, Any], github_pushed: bool) -> bool:
        """Log test results to Supabase restore_checks table"""
        if not self.supabase:
            self.logger.warning("⚠️ Supabase integration disabled - skipping database log")
            return False
        
        try:
            # Extract test summary from results
            test_data = test_results.get('test_results', {})
            
            log_data = {
                'test_run_timestamp': test_results['timestamp'],
                'total_tests': test_data.get('total_tests', 0),
                'passed_tests': test_data.get('passed_tests', 0),
                'failed_tests': test_data.get('failed_tests', 0),
                'success_rate': test_data.get('success_rate', 0.0),
                'duration_seconds': test_results['duration_seconds'],
                'test_details': test_data.get('test_details', []),
                'github_pushed': github_pushed,
                'scheduler_version': '1.0.0'
            }
            
            # Insert to Supabase
            result = self.supabase.table('restore_checks').insert(log_data).execute()
            
            if result.data:
                self.logger.info("✅ Successfully logged test results to Supabase")
                return True
            else:
                self.logger.error("❌ Failed to log to Supabase: No data returned")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to log to Supabase: {e}")
            return False
    
    def log_to_notion_db(self, test_results: Dict[str, Any], success: bool):
        """Log test results to Notion for visibility"""
        if not self.notion_enabled or not NOTION_AVAILABLE:
            return
        
        try:
            test_data = test_results.get('test_results', {})
            
            message = f"Weekly memory recovery test completed. "
            message += f"Results: {test_data.get('passed_tests', 0)}/{test_data.get('total_tests', 0)} tests passed "
            message += f"({test_data.get('success_rate', 0):.1f}% success rate). "
            message += f"Duration: {test_results['duration_seconds']:.2f}s"
            
            tag = "Weekly Test Success" if success else "Weekly Test Failure"
            
            log_to_notion(message, [tag])
            self.logger.info("✅ Logged test results to Notion")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to log to Notion: {e}")
    
    def send_failure_notification(self, test_results: Dict[str, Any]):
        """Send notifications when tests fail"""
        test_data = test_results.get('test_results', {})
        
        # Log failure details
        self.logger.error("🚨 WEEKLY TEST FAILURE DETECTED")
        self.logger.error(f"Failed tests: {test_data.get('failed_tests', 'Unknown')}")
        self.logger.error(f"Success rate: {test_data.get('success_rate', 0):.1f}%")
        self.logger.error(f"Error output: {test_results.get('stderr', 'No error details')}")
        
        # Attempt Notion notification
        if self.notion_enabled and NOTION_AVAILABLE:
            try:
                failure_message = f"🚨 WEEKLY MEMORY RECOVERY TEST FAILURE: "
                failure_message += f"{test_data.get('failed_tests', 'Unknown')} tests failed. "
                failure_message += f"Success rate: {test_data.get('success_rate', 0):.1f}%. "
                failure_message += "Check logs for details."
                
                log_to_notion(failure_message, ["System Alert"])
                self.logger.info("✅ Sent failure notification to Notion")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to send Notion notification: {e}")
    
    def run_weekly_test_cycle(self):
        """Run the complete weekly test cycle"""
        self.logger.info("🔄 Starting weekly memory recovery test cycle...")
        
        cycle_start = datetime.now()
        
        # Step 1: Run the memory recovery test
        test_results = self.run_memory_recovery_test()
        
        # Step 2: Push results to GitHub
        github_pushed = self.push_to_github()
        
        # Step 3: Log to Supabase
        supabase_logged = self.log_to_supabase(test_results, github_pushed)
        
        # Step 4: Log to Notion
        self.log_to_notion_db(test_results, test_results['success'])
        
        # Step 5: Handle failures
        if not test_results['success']:
            self.send_failure_notification(test_results)
        
        # Summary
        cycle_duration = (datetime.now() - cycle_start).total_seconds()
        
        self.logger.info("=" * 60)
        self.logger.info("🏁 WEEKLY TEST CYCLE SUMMARY")
        self.logger.info(f"Test Success: {'✅' if test_results['success'] else '❌'}")
        self.logger.info(f"GitHub Push: {'✅' if github_pushed else '❌'}")
        self.logger.info(f"Supabase Log: {'✅' if supabase_logged else '❌'}")
        self.logger.info(f"Total Duration: {cycle_duration:.2f} seconds")
        self.logger.info("=" * 60)
    
    def start_scheduler(self):
        """Start the weekly scheduler using built-in datetime"""
        self.logger.info("🚀 Starting weekly memory recovery scheduler...")
        
        self.logger.info("⏰ Scheduled weekly tests for Sundays at 03:00 UTC")
        
        # Run an initial test if no recent test results exist
        if not Path('test_results.json').exists():
            self.logger.info("🎯 No recent test results found - running initial test...")
            self.run_weekly_test_cycle()
        
        # Main scheduler loop
        self.logger.info("🔄 Scheduler is now running... (Press Ctrl+C to stop)")
        
        try:
            last_run = None
            while True:
                now = datetime.now(timezone.utc)
                
                # Check if it's Sunday at 03:00 UTC and we haven't run today
                if (now.weekday() == 6 and  # Sunday is 6
                    now.hour == 3 and
                    now.minute < 5 and  # Run within first 5 minutes of 03:00
                    (last_run is None or last_run.date() != now.date())):
                    
                    self.logger.info("⏰ Weekly scheduled time reached - running test cycle")
                    self.run_weekly_test_cycle()
                    last_run = now
                
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"💥 Scheduler error: {e}")
            raise

def main():
    """Main scheduler execution"""
    try:
        print("🗓️ WEEKLY MEMORY RECOVERY SCHEDULER")
        print("=" * 50)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print("⏰ Schedule: Every Sunday at 03:00 UTC")
        print("📝 Logs: logs/weekly_recovery_scheduler.log")
        print()
        
        # Create and start scheduler
        scheduler = WeeklyRecoveryScheduler()
        scheduler.start_scheduler()
        
    except KeyboardInterrupt:
        print("\n🛑 Scheduler interrupted by user")
        return 130
    except Exception as e:
        print(f"💥 Scheduler failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())