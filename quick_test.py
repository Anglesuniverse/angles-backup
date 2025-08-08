#!/usr/bin/env python3
"""
Angles AI Universe™ Quick Test System
Fast validation suite for core system functionality (<30 seconds)

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import time
import json
import logging
import requests
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from memory_bridge import get_bridge
except ImportError:
    get_bridge = None

try:
    from alerts.notify import AlertManager
except ImportError:
    AlertManager = None

class QuickTestSystem:
    """Fast validation system for core functionality"""
    
    def __init__(self):
        """Initialize quick test system"""
        self.setup_logging()
        self.load_environment()
        self.alert_manager = AlertManager() if AlertManager else None
        
        # Quick test configuration
        self.config = {
            'max_total_duration': 30,  # seconds
            'timeout_per_test': 5,     # seconds per individual test
            'test_record_prefix': 'quicktest_',
            'critical_tests_only': False,
            'parallel_execution': False  # Keep simple for reliability
        }
        
        # Test results tracking
        self.test_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'test_id': f"quicktest_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'overall_status': 'unknown',
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'tests_skipped': 0,
            'duration_seconds': 0,
            'test_details': {},
            'failures': [],
            'performance_metrics': {}
        }
        
        # Define quick tests (name, function, critical, timeout)
        self.quick_tests = [
            ('env_check', self.test_environment_variables, True, 1),
            ('supabase_ping', self.test_supabase_connection, True, 5),
            ('supabase_read', self.test_supabase_read, True, 5),
            ('supabase_write', self.test_supabase_write, True, 5),
            ('memory_bridge', self.test_memory_bridge, True, 5),
            ('notion_ping', self.test_notion_connection, False, 5),
            ('git_status', self.test_git_operations, False, 3),
            ('disk_space', self.test_disk_space, True, 1),
            ('log_system', self.test_log_system, False, 2),
            ('file_permissions', self.test_file_permissions, True, 2)
        ]
        
        self.logger.info("⚡ Angles AI Universe™ Quick Test System Initialized")
    
    def setup_logging(self):
        """Setup logging for quick test system"""
        os.makedirs("logs/tests", exist_ok=True)
        
        self.logger = logging.getLogger('quick_test')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/tests/quick_test.log"
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
    
    def load_environment(self):
        """Load environment variables"""
        self.env = {
            'supabase_url': os.getenv('SUPABASE_URL'),
            'supabase_key': os.getenv('SUPABASE_KEY'),
            'notion_token': os.getenv('NOTION_TOKEN'),
            'notion_database_id': os.getenv('NOTION_DATABASE_ID'),
            'github_token': os.getenv('GITHUB_TOKEN'),
            'repo_url': os.getenv('REPO_URL')
        }
        
        self.logger.info("📋 Environment loaded for quick tests")
    
    def test_environment_variables(self) -> Dict[str, Any]:
        """Test critical environment variables"""
        required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
        optional_vars = ['NOTION_TOKEN', 'NOTION_DATABASE_ID', 'GITHUB_TOKEN', 'REPO_URL']
        
        result = {
            'status': 'pass',
            'duration_ms': 0,
            'details': {
                'required_present': 0,
                'optional_present': 0,
                'missing_required': [],
                'missing_optional': []
            }
        }
        
        start_time = time.time()
        
        try:
            # Check required variables
            for var in required_vars:
                if os.getenv(var):
                    result['details']['required_present'] += 1
                else:
                    result['details']['missing_required'].append(var)
            
            # Check optional variables
            for var in optional_vars:
                if os.getenv(var):
                    result['details']['optional_present'] += 1
                else:
                    result['details']['missing_optional'].append(var)
            
            # Determine status
            if result['details']['missing_required']:
                result['status'] = 'fail'
                result['error'] = f"Missing required variables: {', '.join(result['details']['missing_required'])}"
            
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
        
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
    
    def test_supabase_connection(self) -> Dict[str, Any]:
        """Test basic Supabase connectivity"""
        result = {
            'status': 'pass',
            'duration_ms': 0,
            'details': {
                'url': self.env['supabase_url'],
                'response_code': None,
                'response_time_ms': None
            }
        }
        
        if not self.env['supabase_url'] or not self.env['supabase_key']:
            result['status'] = 'skip'
            result['error'] = 'Supabase credentials not configured'
            return result
        
        start_time = time.time()
        
        try:
            headers = {
                'apikey': self.env['supabase_key'],
                'Authorization': f"Bearer {self.env['supabase_key']}",
                'Content-Type': 'application/json'
            }
            
            # Simple ping to check connectivity
            url = f"{self.env['supabase_url']}/rest/v1/"
            
            response = requests.get(url, headers=headers, timeout=self.config['timeout_per_test'])
            
            result['details']['response_code'] = response.status_code
            result['details']['response_time_ms'] = (time.time() - start_time) * 1000
            
            if response.status_code in [200, 404]:  # 404 is OK for base path
                result['status'] = 'pass'
            else:
                result['status'] = 'fail'
                result['error'] = f"HTTP {response.status_code}"
            
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
        
        except Exception as e:
            result['status'] = 'fail'
            result['error'] = str(e)
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
    
    def test_supabase_read(self) -> Dict[str, Any]:
        """Test Supabase read operations"""
        result = {
            'status': 'pass',
            'duration_ms': 0,
            'details': {
                'table': 'decision_vault',
                'records_read': 0,
                'read_time_ms': None
            }
        }
        
        if not self.env['supabase_url'] or not self.env['supabase_key']:
            result['status'] = 'skip'
            result['error'] = 'Supabase credentials not configured'
            return result
        
        start_time = time.time()
        
        try:
            headers = {
                'apikey': self.env['supabase_key'],
                'Authorization': f"Bearer {self.env['supabase_key']}",
                'Content-Type': 'application/json'
            }
            
            url = f"{self.env['supabase_url']}/rest/v1/decision_vault"
            params = {'select': 'id', 'limit': '5'}
            
            read_start = time.time()
            response = requests.get(url, headers=headers, params=params, timeout=self.config['timeout_per_test'])
            result['details']['read_time_ms'] = (time.time() - read_start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                result['details']['records_read'] = len(data)
                result['status'] = 'pass'
            else:
                result['status'] = 'fail'
                result['error'] = f"Read failed: HTTP {response.status_code}"
            
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
        
        except Exception as e:
            result['status'] = 'fail'
            result['error'] = str(e)
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
    
    def test_supabase_write(self) -> Dict[str, Any]:
        """Test Supabase write operations"""
        result = {
            'status': 'pass',
            'duration_ms': 0,
            'details': {
                'table': 'decision_vault',
                'test_record_created': False,
                'test_record_deleted': False,
                'write_time_ms': None
            }
        }
        
        if not self.env['supabase_url'] or not self.env['supabase_key']:
            result['status'] = 'skip'
            result['error'] = 'Supabase credentials not configured'
            return result
        
        start_time = time.time()
        test_record_id = None
        
        try:
            headers = {
                'apikey': self.env['supabase_key'],
                'Authorization': f"Bearer {self.env['supabase_key']}",
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            }
            
            # Create test record
            test_data = {
                'decision': f'{self.config["test_record_prefix"]}{self.test_results["test_id"]}',
                'type': 'technical',
                'date': datetime.now().date().isoformat(),
                'notion_synced': False
            }
            
            url = f"{self.env['supabase_url']}/rest/v1/decision_vault"
            
            write_start = time.time()
            response = requests.post(url, headers=headers, json=test_data, timeout=self.config['timeout_per_test'])
            result['details']['write_time_ms'] = (time.time() - write_start) * 1000
            
            if response.status_code in [200, 201]:
                result['details']['test_record_created'] = True
                
                # Extract record ID for cleanup
                response_data = response.json()
                if response_data and isinstance(response_data, list) and len(response_data) > 0:
                    test_record_id = response_data[0].get('id')
                
                # Clean up test record
                if test_record_id:
                    delete_url = f"{url}?id=eq.{test_record_id}"
                    delete_response = requests.delete(delete_url, headers=headers, timeout=3)
                    result['details']['test_record_deleted'] = delete_response.status_code in [200, 204]
                
                result['status'] = 'pass'
            else:
                result['status'] = 'fail'
                result['error'] = f"Write failed: HTTP {response.status_code}"
            
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
        
        except Exception as e:
            # Attempt cleanup even if test failed
            if test_record_id and self.env['supabase_url'] and self.env['supabase_key']:
                try:
                    headers = {
                        'apikey': self.env['supabase_key'],
                        'Authorization': f"Bearer {self.env['supabase_key']}",
                        'Content-Type': 'application/json'
                    }
                    delete_url = f"{self.env['supabase_url']}/rest/v1/decision_vault?id=eq.{test_record_id}"
                    requests.delete(delete_url, headers=headers, timeout=2)
                except:
                    pass
            
            result['status'] = 'fail'
            result['error'] = str(e)
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
    
    def test_memory_bridge(self) -> Dict[str, Any]:
        """Test memory bridge functionality"""
        result = {
            'status': 'pass',
            'duration_ms': 0,
            'details': {
                'bridge_available': False,
                'health_check_passed': False,
                'notion_enabled': False
            }
        }
        
        start_time = time.time()
        
        try:
            if not get_bridge:
                result['status'] = 'skip'
                result['error'] = 'Memory bridge not available'
                result['duration_ms'] = (time.time() - start_time) * 1000
                return result
            
            bridge = get_bridge()
            result['details']['bridge_available'] = True
            result['details']['notion_enabled'] = bridge.notion_enabled
            
            # Test health check
            health_check_result = bridge.healthcheck()
            result['details']['health_check_passed'] = health_check_result
            
            if health_check_result:
                result['status'] = 'pass'
            else:
                result['status'] = 'fail'
                result['error'] = 'Memory bridge health check failed'
            
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
        
        except Exception as e:
            result['status'] = 'fail'
            result['error'] = str(e)
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
    
    def test_notion_connection(self) -> Dict[str, Any]:
        """Test Notion API connectivity"""
        result = {
            'status': 'pass',
            'duration_ms': 0,
            'details': {
                'credentials_available': False,
                'api_response_code': None,
                'response_time_ms': None
            }
        }
        
        if not self.env['notion_token']:
            result['status'] = 'skip'
            result['error'] = 'Notion credentials not configured'
            return result
        
        start_time = time.time()
        
        try:
            result['details']['credentials_available'] = True
            
            headers = {
                'Authorization': f"Bearer {self.env['notion_token']}",
                'Notion-Version': '2022-06-28'
            }
            
            url = 'https://api.notion.com/v1/users/me'
            
            api_start = time.time()
            response = requests.get(url, headers=headers, timeout=self.config['timeout_per_test'])
            result['details']['response_time_ms'] = (time.time() - api_start) * 1000
            result['details']['api_response_code'] = response.status_code
            
            if response.status_code == 200:
                result['status'] = 'pass'
            else:
                result['status'] = 'fail'
                result['error'] = f"Notion API returned HTTP {response.status_code}"
            
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
        
        except Exception as e:
            result['status'] = 'fail'
            result['error'] = str(e)
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
    
    def test_git_operations(self) -> Dict[str, Any]:
        """Test basic Git operations"""
        result = {
            'status': 'pass',
            'duration_ms': 0,
            'details': {
                'git_available': False,
                'repository_status': None,
                'uncommitted_changes': 0
            }
        }
        
        start_time = time.time()
        
        try:
            # Check if git is available
            git_version = subprocess.run(['git', '--version'], capture_output=True, text=True, timeout=2)
            if git_version.returncode != 0:
                result['status'] = 'fail'
                result['error'] = 'Git not available'
                result['duration_ms'] = (time.time() - start_time) * 1000
                return result
            
            result['details']['git_available'] = True
            
            # Check repository status
            git_status = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, timeout=3)
            
            if git_status.returncode == 0:
                result['details']['repository_status'] = 'clean' if not git_status.stdout.strip() else 'dirty'
                result['details']['uncommitted_changes'] = len(git_status.stdout.strip().split('\n')) if git_status.stdout.strip() else 0
                result['status'] = 'pass'
            else:
                result['status'] = 'fail'
                result['error'] = 'Git status check failed'
            
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
        
        except Exception as e:
            result['status'] = 'fail'
            result['error'] = str(e)
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
    
    def test_disk_space(self) -> Dict[str, Any]:
        """Test available disk space"""
        result = {
            'status': 'pass',
            'duration_ms': 0,
            'details': {
                'free_gb': 0,
                'total_gb': 0,
                'used_percent': 0
            }
        }
        
        start_time = time.time()
        
        try:
            import shutil
            
            total, used, free = shutil.disk_usage('.')
            
            result['details']['free_gb'] = free / (1024**3)
            result['details']['total_gb'] = total / (1024**3)
            result['details']['used_percent'] = (used / total) * 100
            
            # Check thresholds
            if result['details']['used_percent'] >= 95:
                result['status'] = 'fail'
                result['error'] = f"Critical disk usage: {result['details']['used_percent']:.1f}%"
            elif result['details']['used_percent'] >= 90:
                result['status'] = 'warn'
                result['error'] = f"High disk usage: {result['details']['used_percent']:.1f}%"
            
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
        
        except Exception as e:
            result['status'] = 'fail'
            result['error'] = str(e)
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
    
    def test_log_system(self) -> Dict[str, Any]:
        """Test log system functionality"""
        result = {
            'status': 'pass',
            'duration_ms': 0,
            'details': {
                'log_dirs_exist': 0,
                'writable': False,
                'total_log_files': 0
            }
        }
        
        start_time = time.time()
        
        try:
            log_dirs = ['logs', 'logs/health', 'logs/tests', 'logs/backup']
            existing_dirs = 0
            total_files = 0
            
            for log_dir in log_dirs:
                if os.path.exists(log_dir):
                    existing_dirs += 1
                    
                    # Count log files
                    try:
                        for root, dirs, files in os.walk(log_dir):
                            total_files += len([f for f in files if f.endswith('.log')])
                    except:
                        pass
            
            result['details']['log_dirs_exist'] = existing_dirs
            result['details']['total_log_files'] = total_files
            
            # Test write permissions
            test_log_file = 'logs/tests/quick_test_write.tmp'
            try:
                os.makedirs(os.path.dirname(test_log_file), exist_ok=True)
                with open(test_log_file, 'w') as f:
                    f.write('test')
                result['details']['writable'] = True
                os.remove(test_log_file)  # Clean up
            except:
                result['details']['writable'] = False
            
            if not result['details']['writable']:
                result['status'] = 'fail'
                result['error'] = 'Log directory not writable'
            elif existing_dirs < len(log_dirs) // 2:
                result['status'] = 'warn'
                result['error'] = 'Some log directories missing'
            
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
        
        except Exception as e:
            result['status'] = 'fail'
            result['error'] = str(e)
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
    
    def test_file_permissions(self) -> Dict[str, Any]:
        """Test critical file permissions"""
        result = {
            'status': 'pass',
            'duration_ms': 0,
            'details': {
                'executable_scripts': 0,
                'writable_dirs': 0,
                'permission_issues': []
            }
        }
        
        start_time = time.time()
        
        try:
            # Check script executability
            scripts_to_check = [
                'memory_bridge.py',
                'github_backup.py',
                'github_restore.py',
                'health_check.py',
                'quick_test.py'
            ]
            
            executable_count = 0
            for script in scripts_to_check:
                if os.path.exists(script) and os.access(script, os.X_OK):
                    executable_count += 1
                elif os.path.exists(script):
                    result['details']['permission_issues'].append(f"{script} not executable")
            
            result['details']['executable_scripts'] = executable_count
            
            # Check directory writability
            dirs_to_check = ['logs', 'export', 'backups']
            writable_count = 0
            
            for dir_path in dirs_to_check:
                if os.path.exists(dir_path) and os.access(dir_path, os.W_OK):
                    writable_count += 1
                elif os.path.exists(dir_path):
                    result['details']['permission_issues'].append(f"{dir_path} not writable")
            
            result['details']['writable_dirs'] = writable_count
            
            # Determine status
            if result['details']['permission_issues']:
                result['status'] = 'fail'
                result['error'] = f"Permission issues: {', '.join(result['details']['permission_issues'][:3])}"
            
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
        
        except Exception as e:
            result['status'] = 'fail'
            result['error'] = str(e)
            result['duration_ms'] = (time.time() - start_time) * 1000
            return result
    
    def run_quick_tests(self) -> Dict[str, Any]:
        """Run all quick tests"""
        self.logger.info("⚡ Starting quick test suite...")
        self.logger.info("=" * 50)
        
        suite_start_time = time.time()
        
        try:
            # Filter tests if needed
            tests_to_run = self.quick_tests
            if self.config['critical_tests_only']:
                tests_to_run = [(name, func, critical, timeout) for name, func, critical, timeout in self.quick_tests if critical]
            
            self.logger.info(f"🔍 Running {len(tests_to_run)} tests (max {self.config['max_total_duration']}s)...")
            
            # Run tests
            for test_name, test_function, is_critical, timeout in tests_to_run:
                # Check if we're running out of time
                elapsed = time.time() - suite_start_time
                if elapsed >= self.config['max_total_duration']:
                    self.logger.warning(f"⏰ Time limit reached, skipping remaining tests")
                    break
                
                self.logger.info(f"   🧪 {test_name}...")
                
                try:
                    test_result = test_function()
                    self.test_results['test_details'][test_name] = test_result
                    self.test_results['tests_run'] += 1
                    
                    # Update counters
                    if test_result['status'] == 'pass':
                        self.test_results['tests_passed'] += 1
                        status_icon = '✅'
                    elif test_result['status'] == 'skip':
                        self.test_results['tests_skipped'] += 1
                        status_icon = '⏭️'
                    elif test_result['status'] == 'warn':
                        self.test_results['tests_passed'] += 1  # Count as pass but note warning
                        status_icon = '⚠️'
                    else:
                        self.test_results['tests_failed'] += 1
                        self.test_results['failures'].append(f"{test_name}: {test_result.get('error', 'Unknown error')}")
                        status_icon = '❌'
                    
                    # Log result
                    duration = test_result.get('duration_ms', 0)
                    self.logger.info(f"      {status_icon} {test_name}: {test_result['status']} ({duration:.0f}ms)")
                    
                    if test_result.get('error'):
                        self.logger.info(f"         • {test_result['error']}")
                    
                    # Store performance metrics
                    self.test_results['performance_metrics'][test_name] = {
                        'duration_ms': duration,
                        'status': test_result['status']
                    }
                
                except Exception as e:
                    self.logger.error(f"❌ Test {test_name} failed with exception: {e}")
                    self.test_results['tests_run'] += 1
                    self.test_results['tests_failed'] += 1
                    self.test_results['failures'].append(f"{test_name}: Test execution failed - {e}")
                    self.test_results['test_details'][test_name] = {
                        'status': 'error',
                        'error': f"Test execution failed: {e}",
                        'duration_ms': 0
                    }
            
            # Calculate final results
            total_duration = time.time() - suite_start_time
            self.test_results['duration_seconds'] = total_duration
            
            # Determine overall status
            if self.test_results['tests_failed'] > 0:
                # Check if any critical tests failed
                critical_failures = []
                for test_name, _, is_critical, _ in tests_to_run:
                    if test_name in self.test_results['test_details']:
                        test_result = self.test_results['test_details'][test_name]
                        if is_critical and test_result['status'] in ['fail', 'error']:
                            critical_failures.append(test_name)
                
                if critical_failures:
                    self.test_results['overall_status'] = 'critical'
                else:
                    self.test_results['overall_status'] = 'partial'
            else:
                self.test_results['overall_status'] = 'success'
            
            # Send alerts if needed
            self.send_test_alert()
            
            # Final summary
            self.logger.info("\n" + "=" * 50)
            self.logger.info("🏁 QUICK TEST SUITE COMPLETE")
            self.logger.info("=" * 50)
            self.logger.info(f"📊 SUMMARY:")
            self.logger.info(f"   Overall Status: {self.test_results['overall_status'].upper()}")
            self.logger.info(f"   Tests Run: {self.test_results['tests_run']}")
            self.logger.info(f"   Passed: {self.test_results['tests_passed']}")
            self.logger.info(f"   Failed: {self.test_results['tests_failed']}")
            self.logger.info(f"   Skipped: {self.test_results['tests_skipped']}")
            self.logger.info(f"   Duration: {self.test_results['duration_seconds']:.1f} seconds")
            
            if self.test_results['failures']:
                self.logger.error("❌ FAILURES:")
                for failure in self.test_results['failures']:
                    self.logger.error(f"   • {failure}")
            
            # Performance summary
            avg_duration = sum(m['duration_ms'] for m in self.test_results['performance_metrics'].values()) / len(self.test_results['performance_metrics']) if self.test_results['performance_metrics'] else 0
            self.logger.info(f"   Average test duration: {avg_duration:.0f}ms")
            
            self.logger.info("=" * 50)
            
            return self.test_results
        
        except Exception as e:
            self.test_results['overall_status'] = 'error'
            self.test_results['failures'].append(f"Test suite execution failed: {e}")
            self.logger.error(f"💥 Quick test suite failed: {e}")
            return self.test_results
    
    def send_test_alert(self):
        """Send test results alert"""
        if not self.alert_manager:
            return
        
        try:
            status = self.test_results['overall_status']
            passed = self.test_results['tests_passed']
            failed = self.test_results['tests_failed']
            duration = self.test_results['duration_seconds']
            
            if status == 'success':
                title = "✅ Quick Tests Passed"
                message = f"All quick tests passed successfully!\n"
                message += f"• Tests passed: {passed}\n"
                message += f"• Duration: {duration:.1f}s"
                severity = "info"
            elif status == 'partial':
                title = "⚠️ Quick Tests Partial"
                message = f"Some quick tests failed.\n"
                message += f"• Tests passed: {passed}\n"
                message += f"• Tests failed: {failed}\n"
                message += f"• Duration: {duration:.1f}s"
                severity = "warning"
            else:
                title = "❌ Quick Tests Failed"
                message = f"Critical quick tests failed!\n"
                message += f"• Tests failed: {failed}\n"
                message += f"• Duration: {duration:.1f}s"
                if self.test_results['failures']:
                    message += f"\n• Latest failure: {self.test_results['failures'][-1]}"
                severity = "critical"
            
            self.alert_manager.send_alert(
                title=title,
                message=message,
                severity=severity,
                tags=['quick-test', 'validation', 'automated']
            )
            
            self.logger.info("📢 Test alert sent")
        
        except Exception as e:
            self.logger.error(f"❌ Failed to send test alert: {e}")

def main():
    """Main entry point for quick test system"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Quick Test System')
    parser.add_argument('--run', action='store_true', help='Run quick test suite')
    parser.add_argument('--critical-only', action='store_true', help='Run only critical tests')
    parser.add_argument('--no-alerts', action='store_true', help='Disable alert notifications')
    parser.add_argument('--timeout', type=int, default=30, help='Max total duration in seconds')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    
    args = parser.parse_args()
    
    try:
        test_system = QuickTestSystem()
        
        # Override configuration based on args
        if args.critical_only:
            test_system.config['critical_tests_only'] = True
        if args.no_alerts:
            test_system.alert_manager = None
        if args.timeout:
            test_system.config['max_total_duration'] = args.timeout
        
        if args.run or not any(vars(args).values()):
            results = test_system.run_quick_tests()
            
            if args.json:
                print(json.dumps(results, indent=2, default=str))
            
            # Exit codes based on test results
            if results['overall_status'] == 'success':
                sys.exit(0)
            elif results['overall_status'] == 'partial':
                sys.exit(1)
            else:
                sys.exit(2)
        
    except KeyboardInterrupt:
        print("\n🛑 Quick tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Quick test system failure: {e}")
        sys.exit(255)

if __name__ == "__main__":
    main()