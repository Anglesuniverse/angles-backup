#!/usr/bin/env python3
"""
Angles AI Universe™ Operational Smoke Tests
Comprehensive system validation and health verification

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import requests
import subprocess
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import glob

class OperationalSmokeTests:
    """Comprehensive operational smoke tests for all systems"""
    
    def __init__(self):
        """Initialize smoke tests"""
        self.setup_logging()
        self.load_environment()
        
        # Test results storage
        self.test_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'test_details': [],
            'overall_status': 'unknown',
            'duration_seconds': 0
        }
        
        self.logger.info("🧪 Angles AI Universe™ Operational Smoke Tests Initialized")
    
    def setup_logging(self):
        """Setup logging for smoke tests"""
        os.makedirs("logs/active", exist_ok=True)
        
        self.logger = logging.getLogger('smoke_tests')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/active/smoke_tests.log"
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
        """Load environment variables for testing"""
        self.env = {
            'supabase_url': os.getenv('SUPABASE_URL'),
            'supabase_key': os.getenv('SUPABASE_KEY'),
            'notion_token': os.getenv('NOTION_TOKEN') or os.getenv('NOTION_API_KEY'),
            'notion_database_id': os.getenv('NOTION_DATABASE_ID'),
            'github_token': os.getenv('GITHUB_TOKEN'),
            'repo_url': os.getenv('REPO_URL', '')
        }
        
        self.logger.info("📋 Environment variables loaded for testing")
    
    def run_test(self, test_name: str, test_function, *args, **kwargs) -> Dict[str, Any]:
        """Run individual test with error handling"""
        self.test_results['total_tests'] += 1
        
        test_result = {
            'name': test_name,
            'status': 'unknown',
            'duration': 0,
            'message': '',
            'details': {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self.logger.info(f"🧪 Running test: {test_name}")
        start_time = time.time()
        
        try:
            result = test_function(*args, **kwargs)
            
            if isinstance(result, dict):
                test_result.update(result)
            elif isinstance(result, bool):
                test_result['status'] = 'passed' if result else 'failed'
            else:
                test_result['status'] = 'passed'
                test_result['details'] = result
            
            if test_result['status'] == 'passed':
                self.test_results['passed_tests'] += 1
                self.logger.info(f"✅ {test_name}: PASSED")
            elif test_result['status'] == 'skipped':
                self.test_results['skipped_tests'] += 1
                self.logger.info(f"⏭️ {test_name}: SKIPPED - {test_result['message']}")
            else:
                self.test_results['failed_tests'] += 1
                self.logger.error(f"❌ {test_name}: FAILED - {test_result['message']}")
        
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['message'] = str(e)
            test_result['details'] = {'error': str(e)}
            self.test_results['failed_tests'] += 1
            self.logger.error(f"❌ {test_name}: FAILED - {str(e)}")
        
        test_result['duration'] = time.time() - start_time
        self.test_results['test_details'].append(test_result)
        
        return test_result
    
    def test_file_structure(self) -> Dict[str, Any]:
        """Test that all required files and directories exist"""
        required_files = [
            'ops_scheduler.py',
            'generate_weekly_summary.py',
            'alerts/notify.py',
            'schema_guard.py',
            'git_helpers.py',
            'log_manager.py',
            'tools/health_server.py',
            'operational_smoke_tests.py'
        ]
        
        required_directories = [
            'logs/active',
            'logs/archive',
            'logs/compressed',
            'logs/health',
            'logs/alerts',
            'logs/schema',
            'logs/maintenance',
            'alerts',
            'tools'
        ]
        
        missing_files = []
        missing_dirs = []
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        for dir_path in required_directories:
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_path)
        
        if missing_files or missing_dirs:
            return {
                'status': 'failed',
                'message': f"Missing files: {missing_files}, Missing dirs: {missing_dirs}",
                'details': {'missing_files': missing_files, 'missing_dirs': missing_dirs}
            }
        
        return {
            'status': 'passed',
            'message': 'All required files and directories exist',
            'details': {'files_checked': len(required_files), 'dirs_checked': len(required_directories)}
        }
    
    def test_environment_variables(self) -> Dict[str, Any]:
        """Test that required environment variables are set"""
        required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
        optional_vars = ['NOTION_TOKEN', 'NOTION_DATABASE_ID', 'GITHUB_TOKEN', 'REPO_URL']
        
        missing_required = []
        missing_optional = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
        
        for var in optional_vars:
            if not os.getenv(var):
                missing_optional.append(var)
        
        if missing_required:
            return {
                'status': 'failed',
                'message': f"Missing required environment variables: {missing_required}",
                'details': {'missing_required': missing_required, 'missing_optional': missing_optional}
            }
        
        if missing_optional:
            return {
                'status': 'passed',
                'message': f"All required vars set, optional missing: {missing_optional}",
                'details': {'missing_optional': missing_optional}
            }
        
        return {
            'status': 'passed',
            'message': 'All environment variables are set',
            'details': {'all_vars_set': True}
        }
    
    def test_supabase_connectivity(self) -> Dict[str, Any]:
        """Test Supabase database connectivity"""
        if not self.env['supabase_url'] or not self.env['supabase_key']:
            return {
                'status': 'skipped',
                'message': 'Supabase credentials not available'
            }
        
        try:
            headers = {
                'apikey': self.env['supabase_key'],
                'Authorization': f"Bearer {self.env['supabase_key']}",
                'Content-Type': 'application/json'
            }
            
            # Test connection with decision_vault table
            url = f"{self.env['supabase_url']}/rest/v1/decision_vault"
            params = {'select': 'id', 'limit': '1'}
            
            start_time = time.time()
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    'status': 'passed',
                    'message': f'Supabase connection successful ({response_time:.2f}s)',
                    'details': {'response_time': response_time, 'status_code': response.status_code}
                }
            else:
                return {
                    'status': 'failed',
                    'message': f'Supabase connection failed: HTTP {response.status_code}',
                    'details': {'status_code': response.status_code, 'response': response.text[:200]}
                }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Supabase connection error: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def test_notion_connectivity(self) -> Dict[str, Any]:
        """Test Notion API connectivity"""
        if not self.env['notion_token']:
            return {
                'status': 'skipped',
                'message': 'Notion credentials not available'
            }
        
        try:
            headers = {
                'Authorization': f"Bearer {self.env['notion_token']}",
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
            
            # Test API connectivity
            url = 'https://api.notion.com/v1/users/me'
            
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    'status': 'passed',
                    'message': f'Notion API connection successful ({response_time:.2f}s)',
                    'details': {'response_time': response_time, 'status_code': response.status_code}
                }
            else:
                return {
                    'status': 'failed',
                    'message': f'Notion API connection failed: HTTP {response.status_code}',
                    'details': {'status_code': response.status_code, 'response': response.text[:200]}
                }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Notion API connection error: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def test_github_connectivity(self) -> Dict[str, Any]:
        """Test GitHub API connectivity"""
        if not self.env['github_token']:
            return {
                'status': 'skipped',
                'message': 'GitHub credentials not available'
            }
        
        try:
            headers = {
                'Authorization': f"token {self.env['github_token']}",
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Test API connectivity
            url = 'https://api.github.com/user'
            
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    'status': 'passed',
                    'message': f'GitHub API connection successful ({response_time:.2f}s)',
                    'details': {'response_time': response_time, 'status_code': response.status_code}
                }
            else:
                return {
                    'status': 'failed',
                    'message': f'GitHub API connection failed: HTTP {response.status_code}',
                    'details': {'status_code': response.status_code, 'response': response.text[:200]}
                }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'GitHub API connection error: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def test_health_dashboard(self) -> Dict[str, Any]:
        """Test health dashboard accessibility"""
        try:
            # Test main dashboard
            dashboard_url = 'http://localhost:5000'
            
            start_time = time.time()
            response = requests.get(dashboard_url, timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # Test API endpoint
                api_url = 'http://localhost:5000/health'
                api_response = requests.get(api_url, timeout=5)
                
                if api_response.status_code == 200:
                    return {
                        'status': 'passed',
                        'message': f'Health dashboard accessible ({response_time:.2f}s)',
                        'details': {'response_time': response_time, 'api_working': True}
                    }
                else:
                    return {
                        'status': 'failed',
                        'message': 'Dashboard accessible but API endpoint failed',
                        'details': {'dashboard_ok': True, 'api_status': api_response.status_code}
                    }
            else:
                return {
                    'status': 'failed',
                    'message': f'Health dashboard not accessible: HTTP {response.status_code}',
                    'details': {'status_code': response.status_code}
                }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Health dashboard test error: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def test_script_syntax(self) -> Dict[str, Any]:
        """Test Python syntax for all main scripts"""
        scripts_to_test = [
            'ops_scheduler.py',
            'generate_weekly_summary.py',
            'schema_guard.py',
            'git_helpers.py',
            'log_manager.py',
            'tools/health_server.py',
            'alerts/notify.py'
        ]
        
        syntax_errors = []
        
        for script in scripts_to_test:
            if os.path.exists(script):
                try:
                    # Test syntax by compiling
                    with open(script, 'r') as f:
                        compile(f.read(), script, 'exec')
                except SyntaxError as e:
                    syntax_errors.append(f"{script}: {str(e)}")
                except Exception as e:
                    syntax_errors.append(f"{script}: {str(e)}")
        
        if syntax_errors:
            return {
                'status': 'failed',
                'message': f'Syntax errors found in {len(syntax_errors)} scripts',
                'details': {'syntax_errors': syntax_errors}
            }
        
        return {
            'status': 'passed',
            'message': f'All {len(scripts_to_test)} scripts have valid syntax',
            'details': {'scripts_tested': len(scripts_to_test)}
        }
    
    def test_log_directory_permissions(self) -> Dict[str, Any]:
        """Test log directory write permissions"""
        test_directories = [
            'logs/active',
            'logs/archive',
            'logs/compressed',
            'logs/health',
            'logs/alerts'
        ]
        
        permission_issues = []
        
        for directory in test_directories:
            try:
                # Test write permission
                test_file = os.path.join(directory, 'permission_test.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except Exception as e:
                permission_issues.append(f"{directory}: {str(e)}")
        
        if permission_issues:
            return {
                'status': 'failed',
                'message': f'Permission issues in {len(permission_issues)} directories',
                'details': {'permission_issues': permission_issues}
            }
        
        return {
            'status': 'passed',
            'message': f'All {len(test_directories)} directories are writable',
            'details': {'directories_tested': len(test_directories)}
        }
    
    def test_git_repository_status(self) -> Dict[str, Any]:
        """Test Git repository status"""
        try:
            # Check if this is a Git repository
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return {
                    'status': 'failed',
                    'message': 'Not a Git repository or Git not available',
                    'details': {'error': result.stderr}
                }
            
            # Check for uncommitted changes
            uncommitted_files = result.stdout.strip().split('\\n') if result.stdout.strip() else []
            
            # Check remote connectivity
            remote_result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                         capture_output=True, text=True, timeout=10)
            
            has_remote = remote_result.returncode == 0
            
            return {
                'status': 'passed',
                'message': f'Git repository status checked ({len(uncommitted_files)} uncommitted files)',
                'details': {
                    'uncommitted_files': len(uncommitted_files),
                    'has_remote': has_remote,
                    'remote_url': remote_result.stdout.strip() if has_remote else None
                }
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Git status check failed: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def test_alert_system_components(self) -> Dict[str, Any]:
        """Test alert system components"""
        try:
            # Import and test alert manager
            sys.path.append('.')
            from alerts.notify import AlertManager
            
            alert_manager = AlertManager()
            
            # Test basic functionality (without sending actual alerts)
            if hasattr(alert_manager, 'env') and hasattr(alert_manager, 'logger'):
                return {
                    'status': 'passed',
                    'message': 'Alert system components loaded successfully',
                    'details': {'alert_manager_loaded': True}
                }
            else:
                return {
                    'status': 'failed',
                    'message': 'Alert manager missing required attributes',
                    'details': {'alert_manager_loaded': False}
                }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Alert system test failed: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def test_schema_guard_functionality(self) -> Dict[str, Any]:
        """Test schema guard basic functionality"""
        try:
            # Import and test schema guard
            from schema_guard import SchemaGuard
            
            if self.env['supabase_url'] and self.env['supabase_key']:
                schema_guard = SchemaGuard()
                
                # Test basic functionality
                if hasattr(schema_guard, 'required_schema') and hasattr(schema_guard, 'logger'):
                    return {
                        'status': 'passed',
                        'message': 'Schema guard loaded successfully',
                        'details': {'schema_guard_loaded': True, 'has_supabase_creds': True}
                    }
                else:
                    return {
                        'status': 'failed',
                        'message': 'Schema guard missing required attributes',
                        'details': {'schema_guard_loaded': False}
                    }
            else:
                return {
                    'status': 'skipped',
                    'message': 'Schema guard test skipped - no Supabase credentials',
                    'details': {'supabase_creds_available': False}
                }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Schema guard test failed: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def test_log_manager_functionality(self) -> Dict[str, Any]:
        """Test log manager basic functionality"""
        try:
            # Import and test log manager
            from log_manager import LogManager
            
            log_manager = LogManager()
            
            # Test basic functionality
            if hasattr(log_manager, 'config') and hasattr(log_manager, 'logger'):
                # Test disk usage check
                usage = log_manager.check_disk_usage()
                
                if isinstance(usage, dict) and 'total_size_mb' in usage:
                    return {
                        'status': 'passed',
                        'message': f'Log manager working (total logs: {usage["total_size_mb"]:.1f}MB)',
                        'details': {'log_manager_loaded': True, 'disk_usage_mb': usage['total_size_mb']}
                    }
                else:
                    return {
                        'status': 'failed',
                        'message': 'Log manager disk usage check failed',
                        'details': {'disk_usage_result': usage}
                    }
            else:
                return {
                    'status': 'failed',
                    'message': 'Log manager missing required attributes',
                    'details': {'log_manager_loaded': False}
                }
        
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Log manager test failed: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all operational smoke tests"""
        self.logger.info("🚀 Starting Comprehensive Operational Smoke Tests")
        self.logger.info("=" * 70)
        
        start_time = time.time()
        
        # Define test suite
        test_suite = [
            ("File Structure Check", self.test_file_structure),
            ("Environment Variables", self.test_environment_variables),
            ("Supabase Connectivity", self.test_supabase_connectivity),
            ("Notion Connectivity", self.test_notion_connectivity),
            ("GitHub Connectivity", self.test_github_connectivity),
            ("Health Dashboard", self.test_health_dashboard),
            ("Python Syntax Check", self.test_script_syntax),
            ("Log Directory Permissions", self.test_log_directory_permissions),
            ("Git Repository Status", self.test_git_repository_status),
            ("Alert System Components", self.test_alert_system_components),
            ("Schema Guard Functionality", self.test_schema_guard_functionality),
            ("Log Manager Functionality", self.test_log_manager_functionality)
        ]
        
        # Run all tests
        for test_name, test_function in test_suite:
            self.run_test(test_name, test_function)
        
        # Calculate final results
        duration = time.time() - start_time
        self.test_results['duration_seconds'] = duration
        
        # Determine overall status
        if self.test_results['failed_tests'] == 0:
            if self.test_results['skipped_tests'] > 0:
                self.test_results['overall_status'] = 'passed_with_skips'
            else:
                self.test_results['overall_status'] = 'passed'
        else:
            self.test_results['overall_status'] = 'failed'
        
        # Log summary
        self.logger.info("=" * 70)
        self.logger.info("🎉 Operational Smoke Tests Complete")
        self.logger.info(f"   Duration: {duration:.2f} seconds")
        self.logger.info(f"   Total tests: {self.test_results['total_tests']}")
        self.logger.info(f"   Passed: {self.test_results['passed_tests']} ✅")
        self.logger.info(f"   Failed: {self.test_results['failed_tests']} ❌")
        self.logger.info(f"   Skipped: {self.test_results['skipped_tests']} ⏭️")
        self.logger.info(f"   Overall status: {self.test_results['overall_status'].upper()}")
        
        # Save test report
        self.save_test_report()
        
        return self.test_results
    
    def save_test_report(self):
        """Save test report to file"""
        try:
            os.makedirs("logs/tests", exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = f"logs/tests/smoke_test_report_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            
            # Also save as latest report
            with open("logs/tests/latest_smoke_test.json", 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            
            self.logger.info(f"📊 Smoke test report saved: {report_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save test report: {str(e)}")

def main():
    """Main entry point for operational smoke tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Operational smoke tests for Angles AI Universe™')
    parser.add_argument('--test', help='Run specific test only')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only (skip connectivity)')
    parser.add_argument('--connectivity', action='store_true', help='Run connectivity tests only')
    parser.add_argument('--report', action='store_true', help='Show latest test report')
    
    args = parser.parse_args()
    
    try:
        smoke_tests = OperationalSmokeTests()
        
        if args.report:
            # Show latest test report
            try:
                with open("logs/tests/latest_smoke_test.json", 'r') as f:
                    report = json.load(f)
                
                print(f"\\n📊 Latest Smoke Test Report ({report['timestamp']}):")
                print(f"  Overall Status: {report['overall_status']}")
                print(f"  Total Tests: {report['total_tests']}")
                print(f"  Passed: {report['passed_tests']} ✅")
                print(f"  Failed: {report['failed_tests']} ❌")
                print(f"  Skipped: {report['skipped_tests']} ⏭️")
                print(f"  Duration: {report['duration_seconds']:.2f}s")
                
                if report['failed_tests'] > 0:
                    print("\\n❌ Failed Tests:")
                    for test in report['test_details']:
                        if test['status'] == 'failed':
                            print(f"    - {test['name']}: {test['message']}")
                
            except FileNotFoundError:
                print("\\n📊 No previous test reports found. Run tests first.")
        
        elif args.test:
            # Run specific test
            test_method = f"test_{args.test.lower().replace(' ', '_').replace('-', '_')}"
            if hasattr(smoke_tests, test_method):
                result = smoke_tests.run_test(args.test, getattr(smoke_tests, test_method))
                print(f"\\n🧪 Test Result for '{args.test}':")
                print(f"  Status: {result['status']}")
                print(f"  Message: {result['message']}")
                print(f"  Duration: {result['duration']:.2f}s")
            else:
                print(f"\\n❌ Test '{args.test}' not found")
        
        elif args.quick:
            # Run quick tests (skip connectivity)
            quick_tests = [
                ("File Structure Check", smoke_tests.test_file_structure),
                ("Environment Variables", smoke_tests.test_environment_variables),
                ("Python Syntax Check", smoke_tests.test_script_syntax),
                ("Log Directory Permissions", smoke_tests.test_log_directory_permissions),
                ("Git Repository Status", smoke_tests.test_git_repository_status)
            ]
            
            for test_name, test_function in quick_tests:
                smoke_tests.run_test(test_name, test_function)
            
            print(f"\\n🧪 Quick Test Results:")
            print(f"  Passed: {smoke_tests.test_results['passed_tests']} ✅")
            print(f"  Failed: {smoke_tests.test_results['failed_tests']} ❌")
        
        elif args.connectivity:
            # Run connectivity tests only
            connectivity_tests = [
                ("Supabase Connectivity", smoke_tests.test_supabase_connectivity),
                ("Notion Connectivity", smoke_tests.test_notion_connectivity),
                ("GitHub Connectivity", smoke_tests.test_github_connectivity),
                ("Health Dashboard", smoke_tests.test_health_dashboard)
            ]
            
            for test_name, test_function in connectivity_tests:
                smoke_tests.run_test(test_name, test_function)
            
            print(f"\\n🧪 Connectivity Test Results:")
            print(f"  Passed: {smoke_tests.test_results['passed_tests']} ✅")
            print(f"  Failed: {smoke_tests.test_results['failed_tests']} ❌")
            print(f"  Skipped: {smoke_tests.test_results['skipped_tests']} ⏭️")
        
        else:
            # Run all tests
            results = smoke_tests.run_all_tests()
            
            # Exit with appropriate code
            if results['overall_status'] == 'passed':
                print("\\n✅ All operational smoke tests passed!")
                sys.exit(0)
            elif results['overall_status'] == 'passed_with_skips':
                print("\\n✅ All critical tests passed (some tests skipped)")
                sys.exit(0)
            else:
                print(f"\\n❌ {results['failed_tests']} tests failed")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\\n🛑 Smoke tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Smoke tests failed: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()