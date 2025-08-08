#!/usr/bin/env python3
"""
Angles AI Universe™ Comprehensive Operations Scheduler
Cron-like scheduler for health checks, backups, summaries, and maintenance

Author: Angles AI Universe™ Backend Team
Version: 2.0.0
"""

import os
import sys
import time
import logging
import subprocess
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from concurrent.futures import ThreadPoolExecutor

# Import our automation components
try:
    from alerts.notify import AlertManager
except ImportError:
    AlertManager = None

try:
    from git_helpers import GitHelper
except ImportError:
    GitHelper = None

class OpsScheduler:
    """Comprehensive operations scheduler with parallel task execution"""
    
    def __init__(self):
        """Initialize operations scheduler"""
        self.setup_logging()
        self.alert_manager = AlertManager() if AlertManager else None
        self.git_helper = GitHelper() if GitHelper else None
        
        # Track task execution
        self.last_runs = {
            'daily_health': None,
            'daily_backup': None,
            'weekly_summary': None,
            'hourly_maintenance': None
        }
        
        # Task execution stats
        self.execution_stats = {
            'health_checks': {'total': 0, 'passed': 0, 'failed': 0},
            'backups': {'total': 0, 'successful': 0, 'failed': 0},
            'summaries': {'total': 0, 'successful': 0, 'failed': 0},
            'maintenance': {'total': 0, 'successful': 0, 'failed': 0}
        }
        
        self.logger.info("🎆 Angles AI Universe™ Operations Scheduler Initialized")
        self.log_schedule_info()
    
    def setup_logging(self):
        """Setup comprehensive logging for scheduler"""
        os.makedirs("logs/active", exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger('ops_scheduler')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/active/ops_scheduler.log"
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
    
    def log_schedule_info(self):
        """Log scheduling information"""
        self.logger.info("="*70)
        self.logger.info("📅 AUTOMATED OPERATIONS SCHEDULE")
        self.logger.info("   🌅 Daily 03:00 UTC: Health Check + Conditional Restore")
        self.logger.info("   💾 Daily 02:10 UTC: Backup Operations")
        self.logger.info("   📄 Weekly Sun 02:30 UTC: Weekly Summary Generation")
        self.logger.info("   🔍 Every 60 min: Config Monitor + Schema Guard")
        self.logger.info("="*70)
    
    def run_command_safe(self, command: List[str], timeout: int = 300, 
                        task_name: str = "Unknown") -> Dict[str, Any]:
        """Run command safely with comprehensive error handling"""
        self.logger.info(f"🛠️ Executing {task_name}...")
        
        result = {
            'success': False,
            'returncode': None,
            'stdout': '',
            'stderr': '',
            'duration': 0,
            'task_name': task_name
        }
        
        start_time = datetime.now(timezone.utc)
        
        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            result['returncode'] = process.returncode
            result['stdout'] = process.stdout
            result['stderr'] = process.stderr
            result['success'] = process.returncode == 0
            
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            result['duration'] = duration
            
            status_icon = "✅" if result['success'] else "❌"
            self.logger.info(f"{status_icon} {task_name} completed in {duration:.2f}s (exit: {process.returncode})")
            
            if result['stdout']:
                self.logger.info(f"Output: {result['stdout'][:500]}..." if len(result['stdout']) > 500 else f"Output: {result['stdout']}")
            
            if result['stderr'] and not result['success']:
                self.logger.error(f"Error: {result['stderr'][:500]}..." if len(result['stderr']) > 500 else f"Error: {result['stderr']}")
            
        except subprocess.TimeoutExpired:
            result['stderr'] = f"Command timed out after {timeout} seconds"
            self.logger.error(f"❌ {task_name} timed out after {timeout}s")
        
        except Exception as e:
            result['stderr'] = f"Command execution failed: {str(e)}"
            self.logger.error(f"❌ {task_name} failed: {str(e)}")
        
        return result
    
    def daily_health_and_restore(self) -> bool:
        """Daily health check and conditional restore at 03:00 UTC"""
        self.logger.info("🌅 Starting Daily Health Check and Conditional Restore")
        
        success = True
        self.execution_stats['health_checks']['total'] += 1
        
        # Run health check
        health_result = self.run_command_safe(
            [sys.executable, 'health_check.py'],
            timeout=300,
            task_name="Health Check"
        )
        
        if health_result['success']:
            self.execution_stats['health_checks']['passed'] += 1
            self.logger.info("✅ Health check passed - system healthy")
        else:
            self.execution_stats['health_checks']['failed'] += 1
            self.logger.warning("⚠️ Health check failed - running conditional restore")
            success = False
            
            # Run conditional restore
            restore_result = self.run_command_safe(
                [sys.executable, 'restore_from_github.py'],
                timeout=600,
                task_name="Conditional Restore"
            )
            
            if restore_result['success']:
                self.logger.info("✅ Conditional restore completed")
                # Send alert about health issue but successful restore
                if self.alert_manager:
                    self.alert_manager.send_health_alert(
                        "system", "degraded", 
                        {"health_check_failed": True, "restore_successful": True}
                    )
            else:
                self.logger.error("❌ Conditional restore failed")
                # Send critical alert
                if self.alert_manager:
                    self.alert_manager.send_health_alert(
                        "system", "critical",
                        {"health_check_failed": True, "restore_failed": True, "error": restore_result['stderr']}
                    )
        
        return success
    
    def daily_backup_operations(self) -> bool:
        """Daily backup operations at 02:10 UTC"""
        self.logger.info("💾 Starting Daily Backup Operations")
        
        success = True
        self.execution_stats['backups']['total'] += 1
        
        # Run manual backup with automated tag
        backup_tag = f"auto-daily-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        
        backup_result = self.run_command_safe(
            [sys.executable, 'run_backup_manual.py', '--tag', backup_tag, '--no-encryption'],
            timeout=600,
            task_name="Daily Backup"
        )
        
        if backup_result['success']:
            self.execution_stats['backups']['successful'] += 1
            self.logger.info(f"✅ Daily backup completed with tag: {backup_tag}")
        else:
            self.execution_stats['backups']['failed'] += 1
            success = False
            self.logger.error("❌ Daily backup failed")
            
            # Send backup failure alert
            if self.alert_manager:
                self.alert_manager.send_backup_alert(
                    "daily_backup", "failed",
                    {"tag": backup_tag, "error": backup_result['stderr']}
                )
        
        return success
    
    def weekly_summary_generation(self) -> bool:
        """Weekly summary generation on Sunday at 02:30 UTC"""
        self.logger.info("📄 Starting Weekly Summary Generation")
        
        success = True
        self.execution_stats['summaries']['total'] += 1
        
        summary_result = self.run_command_safe(
            [sys.executable, 'generate_weekly_summary.py', '--generate'],
            timeout=900,
            task_name="Weekly Summary"
        )
        
        if summary_result['success']:
            self.execution_stats['summaries']['successful'] += 1
            self.logger.info("✅ Weekly summary generated and published")
        else:
            self.execution_stats['summaries']['failed'] += 1
            success = False
            self.logger.error("❌ Weekly summary generation failed")
            
            # Send summary failure alert
            if self.alert_manager:
                self.alert_manager.send_alert(
                    title="Weekly Summary Generation Failed",
                    message=f"Weekly summary generation failed: {summary_result['stderr']}",
                    severity="warning",
                    tags=['weekly-summary', 'failed']
                )
        
        return success
    
    def hourly_maintenance_tasks(self) -> bool:
        """Hourly maintenance: config monitoring and schema guard"""
        self.logger.info("🔍 Starting Hourly Maintenance Tasks")
        
        success = True
        self.execution_stats['maintenance']['total'] += 1
        
        tasks = []
        
        # Config monitoring
        config_result = self.run_command_safe(
            [sys.executable, 'config_versioning.py'],
            timeout=120,
            task_name="Config Monitoring"
        )
        tasks.append(('config', config_result['success']))
        
        # Schema guard
        schema_result = self.run_command_safe(
            [sys.executable, 'schema_guard.py', '--verify'],
            timeout=180,
            task_name="Schema Guard"
        )
        tasks.append(('schema', schema_result['success']))
        
        # Check if all tasks succeeded
        all_success = all(task[1] for task in tasks)
        
        if all_success:
            self.execution_stats['maintenance']['successful'] += 1
            self.logger.info("✅ All maintenance tasks completed successfully")
        else:
            self.execution_stats['maintenance']['failed'] += 1
            success = False
            
            failed_tasks = [task[0] for task in tasks if not task[1]]
            self.logger.warning(f"⚠️ Some maintenance tasks failed: {', '.join(failed_tasks)}")
            
            # Send maintenance alert for failures
            if self.alert_manager:
                self.alert_manager.send_alert(
                    title="Maintenance Tasks Failed",
                    message=f"The following maintenance tasks failed: {', '.join(failed_tasks)}",
                    severity="warning",
                    tags=['maintenance', 'failed']
                )
        
        return success
    
    def should_run_daily_health(self) -> bool:
        """Check if daily health check should run (03:00 UTC)"""
        now = datetime.now(timezone.utc)
        current_date = now.date()
        
        # Run at 03:00 UTC
        if now.hour == 3 and now.minute == 0:
            if self.last_runs['daily_health'] != current_date:
                return True
        return False
    
    def should_run_daily_backup(self) -> bool:
        """Check if daily backup should run (02:10 UTC)"""
        now = datetime.now(timezone.utc)
        current_date = now.date()
        
        # Run at 02:10 UTC
        if now.hour == 2 and now.minute == 10:
            if self.last_runs['daily_backup'] != current_date:
                return True
        return False
    
    def should_run_weekly_summary(self) -> bool:
        """Check if weekly summary should run (Sunday 02:30 UTC)"""
        now = datetime.now(timezone.utc)
        current_date = now.date()
        
        # Run on Sunday (weekday 6) at 02:30 UTC
        if now.weekday() == 6 and now.hour == 2 and now.minute == 30:
            if self.last_runs['weekly_summary'] != current_date:
                return True
        return False
    
    def should_run_hourly_maintenance(self) -> bool:
        """Check if hourly maintenance should run (every hour at minute 0)"""
        now = datetime.now(timezone.utc)
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        
        # Run every hour at minute 0
        if now.minute == 0:
            if self.last_runs['hourly_maintenance'] != current_hour:
                return True
        return False
    
    def log_execution_stats(self):
        """Log execution statistics every 4 hours"""
        now = datetime.now(timezone.utc)
        
        # Log stats every 4 hours
        if now.hour % 4 == 0 and now.minute == 0:
            self.logger.info("📊 EXECUTION STATISTICS:")
            
            for category, stats in self.execution_stats.items():
                total = stats['total']
                if total > 0:
                    success_rate = (stats.get('successful', stats.get('passed', 0)) / total) * 100
                    self.logger.info(f"   {category}: {total} total, {success_rate:.1f}% success rate")
    
    def commit_logs_to_git(self):
        """Commit log files to Git daily at 04:00 UTC"""
        now = datetime.now(timezone.utc)
        
        if now.hour == 4 and now.minute == 0 and self.git_helper:
            try:
                # Commit log files
                log_files = [
                    'logs/active/ops_scheduler.log',
                    'logs/active/system_health.log',
                    'logs/active/backup.log',
                    'logs/active/schema_guard.log'
                ]
                
                # Filter to existing files
                existing_files = [f for f in log_files if os.path.exists(f)]
                
                if existing_files:
                    result = self.git_helper.safe_commit_and_push(
                        existing_files,
                        f"Daily log update {now.strftime('%Y-%m-%d')}"
                    )
                    
                    if result['success']:
                        self.logger.info("✅ Log files committed to Git")
                    else:
                        self.logger.warning(f"⚠️ Log commit failed: {result['errors']}")
            
            except Exception as e:
                self.logger.error(f"❌ Log commit failed: {str(e)}")
    
    def cleanup_old_logs(self):
        """Cleanup old logs weekly on Monday at 01:00 UTC"""
        now = datetime.now(timezone.utc)
        
        if now.weekday() == 0 and now.hour == 1 and now.minute == 0:  # Monday
            try:
                log_result = self.run_command_safe(
                    [sys.executable, 'log_manager.py'],
                    timeout=300,
                    task_name="Log Cleanup"
                )
                
                if log_result['success']:
                    self.logger.info("✅ Log cleanup completed")
                else:
                    self.logger.warning("⚠️ Log cleanup failed")
            
            except Exception as e:
                self.logger.error(f"❌ Log cleanup failed: {str(e)}")
    
    def run_scheduler(self):
        """Run the comprehensive operations scheduler"""
        self.logger.info("🚀 Starting Comprehensive Operations Scheduler")
        self.logger.info("⏰ Scheduler running... (Press Ctrl+C to stop)")
        
        try:
            while True:
                now = datetime.now(timezone.utc)
                
                # Daily health check and restore (03:00 UTC)
                if self.should_run_daily_health():
                    self.logger.info("⏰ Time for daily health check and restore")
                    success = self.daily_health_and_restore()
                    self.last_runs['daily_health'] = now.date()
                
                # Daily backup operations (02:10 UTC)
                elif self.should_run_daily_backup():
                    self.logger.info("⏰ Time for daily backup operations")
                    success = self.daily_backup_operations()
                    self.last_runs['daily_backup'] = now.date()
                
                # Weekly summary generation (Sunday 02:30 UTC)
                elif self.should_run_weekly_summary():
                    self.logger.info("⏰ Time for weekly summary generation")
                    success = self.weekly_summary_generation()
                    self.last_runs['weekly_summary'] = now.date()
                
                # Hourly maintenance tasks (every hour)
                elif self.should_run_hourly_maintenance():
                    self.logger.info("⏰ Time for hourly maintenance tasks")
                    success = self.hourly_maintenance_tasks()
                    self.last_runs['hourly_maintenance'] = now.replace(minute=0, second=0, microsecond=0)
                
                # Log execution statistics
                self.log_execution_stats()
                
                # Commit logs to Git
                self.commit_logs_to_git()
                
                # Cleanup old logs
                self.cleanup_old_logs()
                
                # Sleep for 60 seconds
                time.sleep(60)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Operations scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"💥 Scheduler error: {str(e)}")
            
            # Send critical alert
            if self.alert_manager:
                self.alert_manager.send_alert(
                    title="Operations Scheduler Critical Failure",
                    message=f"The operations scheduler encountered a critical error: {str(e)}",
                    severity="critical",
                    tags=['scheduler', 'critical', 'failure']
                )
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get comprehensive status summary"""
        now = datetime.now(timezone.utc)
        
        summary = {
            'timestamp': now.isoformat(),
            'uptime_hours': 0,  # Could track actual uptime
            'last_runs': self.last_runs.copy(),
            'execution_stats': self.execution_stats.copy(),
            'next_scheduled': {
                'daily_health': '03:00 UTC',
                'daily_backup': '02:10 UTC', 
                'weekly_summary': 'Sunday 02:30 UTC',
                'hourly_maintenance': 'Every hour at :00'
            },
            'overall_health': 'healthy'  # Could be calculated based on recent failures
        }
        
        # Calculate overall health
        total_tasks = sum(stats['total'] for stats in self.execution_stats.values())
        if total_tasks > 0:
            total_failures = sum(stats.get('failed', 0) for stats in self.execution_stats.values())
            failure_rate = total_failures / total_tasks
            
            if failure_rate > 0.2:
                summary['overall_health'] = 'critical'
            elif failure_rate > 0.1:
                summary['overall_health'] = 'degraded'
        
        return summary

def main():
    """Main entry point for operations scheduler"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive operations scheduler')
    parser.add_argument('--status', action='store_true', help='Show scheduler status')
    parser.add_argument('--test-health', action='store_true', help='Test daily health check')
    parser.add_argument('--test-backup', action='store_true', help='Test daily backup')
    parser.add_argument('--test-summary', action='store_true', help='Test weekly summary')
    parser.add_argument('--test-maintenance', action='store_true', help='Test hourly maintenance')
    
    args = parser.parse_args()
    
    try:
        scheduler = OpsScheduler()
        
        if args.status:
            status = scheduler.get_status_summary()
            print("\n📊 Operations Scheduler Status:")
            print(f"  Overall Health: {status['overall_health']}")
            print(f"  Timestamp: {status['timestamp']}")
            
            print("\n🔄 Last Runs:")
            for task, last_run in status['last_runs'].items():
                print(f"  {task}: {last_run or 'Never'}")
            
            print("\n📊 Execution Stats:")
            for category, stats in status['execution_stats'].items():
                total = stats['total']
                if total > 0:
                    success_key = 'successful' if 'successful' in stats else 'passed'
                    success_rate = (stats.get(success_key, 0) / total) * 100
                    print(f"  {category}: {total} total, {success_rate:.1f}% success")
        
        elif args.test_health:
            success = scheduler.daily_health_and_restore()
            print(f"\n🌅 Daily Health Check: {'Passed' if success else 'Failed'}")
        
        elif args.test_backup:
            success = scheduler.daily_backup_operations()
            print(f"\n💾 Daily Backup: {'Successful' if success else 'Failed'}")
        
        elif args.test_summary:
            success = scheduler.weekly_summary_generation()
            print(f"\n📄 Weekly Summary: {'Generated' if success else 'Failed'}")
        
        elif args.test_maintenance:
            success = scheduler.hourly_maintenance_tasks()
            print(f"\n🔍 Hourly Maintenance: {'Completed' if success else 'Failed'}")
        
        else:
            # Run the scheduler
            scheduler.run_scheduler()
    
    except KeyboardInterrupt:
        print("\n🛑 Operations scheduler interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Operations scheduler failed: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()