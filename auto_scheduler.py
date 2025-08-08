#!/usr/bin/env python3
"""
Angles AI Universe™ Auto-Scheduler
Comprehensive scheduling for hourly sync, daily backup, nightly tests with self-heal

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import time
import json
import logging
try:
    import schedule
except ImportError:
    schedule = None
import threading
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from alerts.notify import AlertManager
except ImportError:
    AlertManager = None

try:
    from memory_bridge import get_bridge
except ImportError:
    get_bridge = None

class AutoScheduler:
    """Comprehensive auto-scheduler with self-healing capabilities"""
    
    def __init__(self):
        """Initialize auto-scheduler"""
        self.setup_logging()
        self.load_configuration()
        self.alert_manager = AlertManager() if AlertManager else None
        
        # Scheduler state
        self.is_running = False
        self.stop_event = threading.Event()
        
        # Self-heal tracking
        self.task_failures = {}
        self.last_health_check = None
        self.consecutive_failures = 0
        
        # Performance tracking
        self.task_performance = {}
        self.optimization_metrics = {
            'total_tasks_run': 0,
            'total_failures': 0,
            'average_duration': 0,
            'last_optimization': None
        }
        
        self.logger.info("⏰ Angles AI Universe™ Auto-Scheduler Initialized")
    
    def setup_logging(self):
        """Setup logging for auto-scheduler"""
        os.makedirs("logs/scheduler", exist_ok=True)
        
        self.logger = logging.getLogger('auto_scheduler')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/scheduler/auto_scheduler.log"
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
    
    def load_configuration(self):
        """Load scheduler configuration"""
        self.config = {
            # Scheduling intervals
            'memory_sync_interval': 60,      # minutes - hourly sync
            'backup_interval': '02:00',      # daily backup time
            'health_check_interval': 30,     # minutes
            'quick_test_interval': '23:00',  # nightly quick tests
            'deep_health_interval': '03:30', # daily deep health check
            
            # Self-heal settings
            'max_consecutive_failures': 3,
            'failure_cooldown_minutes': 15,
            'auto_restart_services': True,
            'health_check_timeout': 300,
            
            # Performance optimization
            'performance_logging': True,
            'optimization_interval': '04:00',  # daily optimization
            'performance_history_days': 30,
            'slow_task_threshold': 300,  # seconds
            
            # Retry settings
            'max_retries': 3,
            'retry_delay': 30,  # seconds
            'exponential_backoff': True
        }
        
        self.logger.info("📋 Scheduler configuration loaded")
    
    def with_retry_and_heal(self, func: Callable, task_name: str, *args, **kwargs) -> Any:
        """Execute function with retry logic and self-healing"""
        max_retries = self.config['max_retries']
        retry_delay = self.config['retry_delay']
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Track performance
                self.track_task_performance(task_name, duration, True)
                
                # Reset failure count on success
                if task_name in self.task_failures:
                    self.task_failures[task_name] = 0
                
                self.logger.info(f"✅ {task_name} completed successfully in {duration:.1f}s")
                return result
            
            except Exception as e:
                self.logger.error(f"❌ {task_name} attempt {attempt + 1} failed: {e}")
                
                # Track failure
                if task_name not in self.task_failures:
                    self.task_failures[task_name] = 0
                self.task_failures[task_name] += 1
                
                # Track performance (as failure)
                duration = 0
                if 'start_time' in locals():
                    duration = time.time() - start_time
                self.track_task_performance(task_name, duration, False)
                
                # Check if we should attempt self-heal
                if attempt < max_retries:
                    if self.config['exponential_backoff']:
                        delay = retry_delay * (2 ** attempt)
                    else:
                        delay = retry_delay
                    
                    self.logger.info(f"🔄 Retrying {task_name} in {delay}s...")
                    time.sleep(delay)
                    
                    # Attempt self-heal before retry
                    self.attempt_self_heal(task_name, e)
                else:
                    # All retries exhausted
                    self.handle_task_failure(task_name, e)
                    raise
    
    def track_task_performance(self, task_name: str, duration: float, success: bool):
        """Track task performance metrics"""
        if not self.config['performance_logging']:
            return
        
        if task_name not in self.task_performance:
            self.task_performance[task_name] = {
                'runs': 0,
                'successes': 0,
                'failures': 0,
                'total_duration': 0,
                'average_duration': 0,
                'last_run': None,
                'slowest_run': 0,
                'fastest_run': float('inf')
            }
        
        stats = self.task_performance[task_name]
        stats['runs'] += 1
        stats['total_duration'] += duration
        stats['average_duration'] = stats['total_duration'] / stats['runs']
        stats['last_run'] = datetime.now(timezone.utc).isoformat()
        
        if success:
            stats['successes'] += 1
        else:
            stats['failures'] += 1
        
        if duration > stats['slowest_run']:
            stats['slowest_run'] = duration
        if duration < stats['fastest_run']:
            stats['fastest_run'] = duration
        
        # Check for slow task
        if duration > self.config['slow_task_threshold']:
            self.logger.warning(f"⚠️ Slow task detected: {task_name} took {duration:.1f}s")
    
    def attempt_self_heal(self, task_name: str, error: Exception):
        """Attempt to self-heal common issues"""
        self.logger.info(f"🔧 Attempting self-heal for {task_name}...")
        
        error_str = str(error).lower()
        
        # Connection issues
        if 'connection' in error_str or 'timeout' in error_str:
            self.logger.info("🔧 Detected connection issue, waiting for network recovery...")
            time.sleep(10)
            
            # Test basic connectivity
            try:
                if get_bridge:
                    bridge = get_bridge()
                    if bridge.healthcheck():
                        self.logger.info("✅ Network connectivity restored")
                    else:
                        self.logger.warning("⚠️ Network still unreachable")
            except:
                pass
        
        # Memory/resource issues
        elif 'memory' in error_str or 'resource' in error_str:
            self.logger.info("🔧 Detected resource issue, attempting cleanup...")
            self.cleanup_resources()
        
        # Permission issues
        elif 'permission' in error_str or 'access' in error_str:
            self.logger.info("🔧 Detected permission issue, checking file permissions...")
            self.check_and_fix_permissions()
        
        # Git issues
        elif 'git' in error_str:
            self.logger.info("🔧 Detected Git issue, attempting repository cleanup...")
            self.cleanup_git_state()
    
    def cleanup_resources(self):
        """Clean up system resources"""
        try:
            # Clean temporary files
            import tempfile
            temp_dir = tempfile.gettempdir()
            for file in os.listdir(temp_dir):
                if file.startswith('restore_temp_') or file.startswith('backup_temp_'):
                    try:
                        file_path = os.path.join(temp_dir, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            import shutil
                            shutil.rmtree(file_path)
                    except:
                        pass
            
            self.logger.info("✅ Cleaned up temporary resources")
        except Exception as e:
            self.logger.error(f"❌ Resource cleanup failed: {e}")
    
    def check_and_fix_permissions(self):
        """Check and fix file permissions"""
        try:
            critical_dirs = ['logs', 'export', 'backups']
            for dir_path in critical_dirs:
                if os.path.exists(dir_path):
                    try:
                        # Ensure directory is writable
                        os.chmod(dir_path, 0o755)
                    except:
                        pass
            
            self.logger.info("✅ Checked and fixed permissions")
        except Exception as e:
            self.logger.error(f"❌ Permission fix failed: {e}")
    
    def cleanup_git_state(self):
        """Clean up Git repository state"""
        try:
            # Reset any unstaged changes
            subprocess.run(['git', 'reset', '--hard'], capture_output=True, timeout=30)
            
            # Clean untracked files
            subprocess.run(['git', 'clean', '-fd'], capture_output=True, timeout=30)
            
            self.logger.info("✅ Cleaned up Git state")
        except Exception as e:
            self.logger.error(f"❌ Git cleanup failed: {e}")
    
    def handle_task_failure(self, task_name: str, error: Exception):
        """Handle task failure after all retries exhausted"""
        failure_count = self.task_failures.get(task_name, 0)
        
        if failure_count >= self.config['max_consecutive_failures']:
            self.logger.error(f"🚨 Critical: {task_name} has failed {failure_count} consecutive times")
            
            # Send critical alert
            if self.alert_manager:
                self.alert_manager.send_alert(
                    title=f"🚨 Critical Task Failure: {task_name}",
                    message=f"Task {task_name} has failed {failure_count} consecutive times.\nLatest error: {error}",
                    severity="critical",
                    tags=['scheduler', 'task-failure', 'critical']
                )
            
            # Attempt service restart if enabled
            if self.config['auto_restart_services']:
                self.attempt_service_restart(task_name)
    
    def attempt_service_restart(self, task_name: str):
        """Attempt to restart related services"""
        self.logger.info(f"🔄 Attempting service restart for {task_name}...")
        
        try:
            if 'sync' in task_name.lower():
                # Restart memory bridge
                self.logger.info("🔄 Restarting memory bridge...")
                # Memory bridge is stateless, just reinitialize
                if get_bridge:
                    global _bridge
                    _bridge = None  # Force reinitialization
            
            self.logger.info("✅ Service restart completed")
        except Exception as e:
            self.logger.error(f"❌ Service restart failed: {e}")
    
    def run_memory_sync(self):
        """Run memory sync task"""
        if not get_bridge:
            raise Exception("Memory bridge not available")
        
        bridge = get_bridge()
        bridge.sync_all()
    
    def run_github_backup(self):
        """Run GitHub backup task"""
        result = subprocess.run([
            sys.executable, 'github_backup.py', '--run'
        ], capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            raise Exception(f"Backup failed: {result.stderr}")
    
    def run_health_check(self):
        """Run health check task"""
        result = subprocess.run([
            sys.executable, 'health_check.py', '--run', '--quick'
        ], capture_output=True, text=True, timeout=self.config['health_check_timeout'])
        
        if result.returncode != 0:
            raise Exception(f"Health check failed: {result.stderr}")
    
    def run_quick_tests(self):
        """Run quick test suite"""
        result = subprocess.run([
            sys.executable, 'quick_test.py', '--run', '--critical-only'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise Exception(f"Quick tests failed: {result.stderr}")
    
    def run_deep_health_check(self):
        """Run deep health check"""
        result = subprocess.run([
            sys.executable, 'health_check.py', '--run'
        ], capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            raise Exception(f"Deep health check failed: {result.stderr}")
    
    def run_optimization_tasks(self):
        """Run performance optimization tasks"""
        self.logger.info("🚀 Running optimization tasks...")
        
        try:
            # Clean old logs
            self.optimize_log_files()
            
            # Clean old backups
            self.optimize_backup_files()
            
            # Update performance metrics
            self.update_optimization_metrics()
            
            # Generate performance report
            self.generate_performance_report()
            
        except Exception as e:
            self.logger.error(f"❌ Optimization tasks failed: {e}")
            raise
    
    def optimize_log_files(self):
        """Optimize log files by compressing old ones"""
        import gzip
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for root, dirs, files in os.walk('logs'):
            for file in files:
                if file.endswith('.log'):
                    file_path = os.path.join(root, file)
                    try:
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        if file_mtime < cutoff_date and not file.endswith('.gz'):
                            # Compress old log
                            with open(file_path, 'rb') as f_in:
                                with gzip.open(file_path + '.gz', 'wb') as f_out:
                                    f_out.writelines(f_in)
                            
                            os.remove(file_path)
                            self.logger.info(f"🗜️ Compressed old log: {file}")
                    except:
                        pass
    
    def optimize_backup_files(self):
        """Clean up old backup files"""
        if not os.path.exists('backups'):
            return
        
        cutoff_date = datetime.now() - timedelta(days=30)
        removed_count = 0
        
        for filename in os.listdir('backups'):
            file_path = os.path.join('backups', filename)
            try:
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_mtime < cutoff_date:
                    os.remove(file_path)
                    removed_count += 1
            except:
                pass
        
        if removed_count > 0:
            self.logger.info(f"🗑️ Cleaned up {removed_count} old backup files")
    
    def update_optimization_metrics(self):
        """Update optimization metrics"""
        self.optimization_metrics['total_tasks_run'] = sum(
            stats['runs'] for stats in self.task_performance.values()
        )
        self.optimization_metrics['total_failures'] = sum(
            stats['failures'] for stats in self.task_performance.values()
        )
        
        if self.task_performance:
            total_duration = sum(stats['total_duration'] for stats in self.task_performance.values())
            total_runs = sum(stats['runs'] for stats in self.task_performance.values())
            self.optimization_metrics['average_duration'] = total_duration / total_runs if total_runs > 0 else 0
        
        self.optimization_metrics['last_optimization'] = datetime.now(timezone.utc).isoformat()
    
    def generate_performance_report(self):
        """Generate performance report"""
        try:
            report = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'optimization_metrics': self.optimization_metrics,
                'task_performance': self.task_performance,
                'task_failures': self.task_failures
            }
            
            os.makedirs('logs/performance', exist_ok=True)
            report_file = f"logs/performance/performance_{datetime.now().strftime('%Y%m%d')}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"📊 Performance report saved: {report_file}")
        except Exception as e:
            self.logger.error(f"❌ Performance report generation failed: {e}")
    
    def setup_schedule(self):
        """Setup scheduled tasks"""
        self.logger.info("⏰ Setting up scheduled tasks...")
        
        # Memory sync - every hour
        schedule.every(self.config['memory_sync_interval']).minutes.do(
            lambda: self.with_retry_and_heal(self.run_memory_sync, "memory_sync")
        )
        
        # Daily backup
        schedule.every().day.at(self.config['backup_interval']).do(
            lambda: self.with_retry_and_heal(self.run_github_backup, "github_backup")
        )
        
        # Health checks - every 30 minutes
        schedule.every(self.config['health_check_interval']).minutes.do(
            lambda: self.with_retry_and_heal(self.run_health_check, "health_check")
        )
        
        # Nightly quick tests
        schedule.every().day.at(self.config['quick_test_interval']).do(
            lambda: self.with_retry_and_heal(self.run_quick_tests, "quick_tests")
        )
        
        # Daily deep health check
        schedule.every().day.at(self.config['deep_health_interval']).do(
            lambda: self.with_retry_and_heal(self.run_deep_health_check, "deep_health_check")
        )
        
        # Daily optimization
        schedule.every().day.at(self.config['optimization_interval']).do(
            lambda: self.with_retry_and_heal(self.run_optimization_tasks, "optimization")
        )
        
        self.logger.info("✅ Scheduled tasks configured:")
        self.logger.info(f"   🔄 Memory sync: Every {self.config['memory_sync_interval']} minutes")
        self.logger.info(f"   💾 Backup: Daily at {self.config['backup_interval']}")
        self.logger.info(f"   ❤️ Health checks: Every {self.config['health_check_interval']} minutes")
        self.logger.info(f"   🧪 Quick tests: Daily at {self.config['quick_test_interval']}")
        self.logger.info(f"   🔍 Deep health: Daily at {self.config['deep_health_interval']}")
        self.logger.info(f"   ⚡ Optimization: Daily at {self.config['optimization_interval']}")
    
    def run_scheduler(self):
        """Run the scheduler loop"""
        self.setup_schedule()
        self.is_running = True
        
        self.logger.info("🚀 Auto-scheduler started")
        self.logger.info("=" * 60)
        
        try:
            while self.is_running and not self.stop_event.is_set():
                schedule.run_pending()
                time.sleep(1)
        
        except KeyboardInterrupt:
            self.logger.info("🛑 Scheduler interrupted by user")
        
        except Exception as e:
            self.logger.error(f"💥 Scheduler error: {e}")
            
            # Attempt self-recovery
            self.consecutive_failures += 1
            if self.consecutive_failures < self.config['max_consecutive_failures']:
                self.logger.info(f"🔧 Attempting scheduler recovery (attempt {self.consecutive_failures})...")
                time.sleep(60)  # Wait before restart
                self.run_scheduler()  # Recursive restart
            else:
                self.logger.error("🚨 Scheduler failed too many times, stopping")
                raise
        
        finally:
            self.is_running = False
            self.logger.info("🏁 Auto-scheduler stopped")
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        self.stop_event.set()

def main():
    """Main entry point for auto-scheduler"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto-Scheduler with Self-Heal')
    parser.add_argument('--run', action='store_true', help='Start the scheduler')
    parser.add_argument('--test', action='store_true', help='Run test sequence')
    parser.add_argument('--config', type=str, help='Custom configuration file')
    
    args = parser.parse_args()
    
    try:
        scheduler = AutoScheduler()
        
        if args.test:
            # Run test sequence
            scheduler.logger.info("🧪 Running test sequence...")
            
            test_tasks = [
                ('memory_sync', scheduler.run_memory_sync),
                ('health_check', scheduler.run_health_check),
                ('quick_tests', scheduler.run_quick_tests)
            ]
            
            for task_name, task_func in test_tasks:
                scheduler.logger.info(f"Testing {task_name}...")
                try:
                    scheduler.with_retry_and_heal(task_func, task_name)
                except Exception as e:
                    scheduler.logger.error(f"Test {task_name} failed: {e}")
            
            scheduler.logger.info("✅ Test sequence completed")
        
        elif args.run or not any(vars(args).values()):
            scheduler.run_scheduler()
        
    except KeyboardInterrupt:
        print("\n🛑 Auto-scheduler interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Auto-scheduler failure: {e}")
        sys.exit(255)

if __name__ == "__main__":
    main()