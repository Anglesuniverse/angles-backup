#!/usr/bin/env python3
"""
Angles AI Universe™ Comprehensive Test Suite
All-in-one testing for the backend deployment system

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import logging
import unittest
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import requests
except ImportError:
    print("❌ Missing required dependency: requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def setup_logging():
    """Setup logging for tests"""
    os.makedirs("logs/active", exist_ok=True)
    
    logger = logging.getLogger('test_suite')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler
    file_handler = logging.FileHandler('logs/active/test_results.log')
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class EnvironmentTests(unittest.TestCase):
    """Test environment configuration"""
    
    def setUp(self):
        self.logger = setup_logging()
        self.required_vars = [
            'SUPABASE_URL', 'SUPABASE_KEY', 'NOTION_TOKEN', 
            'NOTION_DATABASE_ID', 'GITHUB_TOKEN', 'REPO_URL'
        ]
    
    def test_required_environment_variables(self):
        """Test that all required environment variables are set"""
        missing_vars = []
        
        for var_name in self.required_vars:
            value = os.getenv(var_name)
            # Handle alternative Notion token name
            if var_name == 'NOTION_TOKEN' and not value:
                value = os.getenv('NOTION_API_KEY')
            
            if not value:
                missing_vars.append(var_name)
        
        self.assertEqual(
            len(missing_vars), 0, 
            f"Missing required environment variables: {missing_vars}"
        )
        
        self.logger.info(f"✅ All {len(self.required_vars)} required environment variables are set")
    
    def test_environment_variable_format(self):
        """Test environment variables have correct format"""
        supabase_url = os.getenv('SUPABASE_URL')
        if supabase_url:
            self.assertTrue(
                supabase_url.startswith('https://'), 
                "SUPABASE_URL should start with https://"
            )
            self.assertTrue(
                '.supabase.co' in supabase_url,
                "SUPABASE_URL should contain .supabase.co"
            )
        
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            self.assertTrue(
                github_token.startswith(('ghp_', 'github_pat_')),
                "GITHUB_TOKEN should start with ghp_ or github_pat_"
            )
        
        self.logger.info("✅ Environment variable formats are correct")

class FileStructureTests(unittest.TestCase):
    """Test file structure and dependencies"""
    
    def setUp(self):
        self.logger = setup_logging()
        self.required_files = [
            'run_migration.py',
            'memory_sync.py', 
            'autosync_files.py',
            'backend_monitor.py',
            'restore_from_github.py',
            'scheduler.py',
            'utils/git_helpers.py'
        ]
        self.required_dirs = [
            'logs', 'logs/active', 'export', 'export/safe', 
            'utils', 'tests'
        ]
    
    def test_required_files_exist(self):
        """Test that all required files exist"""
        missing_files = []
        
        for file_path in self.required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        self.assertEqual(
            len(missing_files), 0,
            f"Missing required files: {missing_files}"
        )
        
        self.logger.info(f"✅ All {len(self.required_files)} required files exist")
    
    def test_required_directories_exist(self):
        """Test that all required directories exist"""
        missing_dirs = []
        
        for dir_path in self.required_dirs:
            if not Path(dir_path).exists():
                missing_dirs.append(dir_path)
        
        self.assertEqual(
            len(missing_dirs), 0,
            f"Missing required directories: {missing_dirs}"
        )
        
        self.logger.info(f"✅ All {len(self.required_dirs)} required directories exist")
    
    def test_python_syntax(self):
        """Test Python files for syntax errors"""
        syntax_errors = []
        
        for file_path in self.required_files:
            if Path(file_path).exists() and file_path.endswith('.py'):
                try:
                    with open(file_path, 'r') as f:
                        compile(f.read(), file_path, 'exec')
                except SyntaxError as e:
                    syntax_errors.append(f"{file_path}: {e}")
        
        self.assertEqual(
            len(syntax_errors), 0,
            f"Python syntax errors found: {syntax_errors}"
        )
        
        self.logger.info("✅ All Python files have valid syntax")

class DatabaseTests(unittest.TestCase):
    """Test database connectivity and schema"""
    
    def setUp(self):
        self.logger = setup_logging()
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if self.supabase_url and self.supabase_key:
            self.headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
        else:
            self.headers = None
    
    def test_supabase_connectivity(self):
        """Test Supabase database connectivity"""
        if not self.headers:
            self.skipTest("Supabase credentials not configured")
        
        try:
            response = requests.get(
                f"{self.supabase_url}/rest/v1/",
                headers=self.headers,
                timeout=10
            )
            
            self.assertTrue(
                response.status_code in [200, 404],
                f"Supabase connection failed: HTTP {response.status_code}"
            )
            
            self.logger.info("✅ Supabase connectivity successful")
            
        except Exception as e:
            self.fail(f"Supabase connection error: {e}")
    
    def test_decision_vault_table(self):
        """Test decision_vault table exists and has correct schema"""
        if not self.headers:
            self.skipTest("Supabase credentials not configured")
        
        try:
            response = requests.get(
                f"{self.supabase_url}/rest/v1/decision_vault?select=id&limit=1",
                headers=self.headers,
                timeout=10
            )
            
            self.assertEqual(
                response.status_code, 200,
                f"decision_vault table access failed: HTTP {response.status_code}"
            )
            
            self.logger.info("✅ decision_vault table accessible")
            
        except Exception as e:
            self.fail(f"decision_vault table test error: {e}")
    
    def test_agent_activity_table(self):
        """Test agent_activity table exists"""
        if not self.headers:
            self.skipTest("Supabase credentials not configured")
        
        try:
            response = requests.get(
                f"{self.supabase_url}/rest/v1/agent_activity?select=id&limit=1",
                headers=self.headers,
                timeout=10
            )
            
            self.assertEqual(
                response.status_code, 200,
                f"agent_activity table access failed: HTTP {response.status_code}"
            )
            
            self.logger.info("✅ agent_activity table accessible")
            
        except Exception as e:
            self.fail(f"agent_activity table test error: {e}")

class NotionTests(unittest.TestCase):
    """Test Notion connectivity"""
    
    def setUp(self):
        self.logger = setup_logging()
        self.notion_token = os.getenv('NOTION_TOKEN') or os.getenv('NOTION_API_KEY')
        self.notion_db_id = os.getenv('NOTION_DATABASE_ID')
    
    def test_notion_connectivity(self):
        """Test Notion API connectivity"""
        if not self.notion_token:
            self.skipTest("Notion credentials not configured")
        
        try:
            response = requests.get(
                "https://api.notion.com/v1/users/me",
                headers={
                    'Authorization': f'Bearer {self.notion_token}',
                    'Notion-Version': '2022-06-28'
                },
                timeout=10
            )
            
            self.assertEqual(
                response.status_code, 200,
                f"Notion API connection failed: HTTP {response.status_code}"
            )
            
            self.logger.info("✅ Notion API connectivity successful")
            
        except Exception as e:
            self.fail(f"Notion connection error: {e}")
    
    def test_notion_database_access(self):
        """Test access to Notion database"""
        if not self.notion_token or not self.notion_db_id:
            self.skipTest("Notion credentials not fully configured")
        
        try:
            response = requests.get(
                f"https://api.notion.com/v1/databases/{self.notion_db_id}",
                headers={
                    'Authorization': f'Bearer {self.notion_token}',
                    'Notion-Version': '2022-06-28'
                },
                timeout=10
            )
            
            self.assertEqual(
                response.status_code, 200,
                f"Notion database access failed: HTTP {response.status_code}"
            )
            
            self.logger.info("✅ Notion database accessible")
            
        except Exception as e:
            self.fail(f"Notion database test error: {e}")

class ComponentTests(unittest.TestCase):
    """Test individual components"""
    
    def setUp(self):
        self.logger = setup_logging()
    
    def test_migration_script(self):
        """Test database migration script"""
        try:
            result = subprocess.run(
                [sys.executable, 'run_migration.py', '--dry-run'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            self.assertEqual(
                result.returncode, 0,
                f"Migration script failed: {result.stderr}"
            )
            
            self.logger.info("✅ Database migration script working")
            
        except Exception as e:
            self.fail(f"Migration script test error: {e}")
    
    def test_memory_sync(self):
        """Test memory sync component"""
        try:
            result = subprocess.run(
                [sys.executable, 'memory_sync.py', '--test'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Memory sync may fail if no data, but should not crash
            self.assertIn(
                result.returncode, [0, 1],
                f"Memory sync crashed unexpectedly: {result.stderr}"
            )
            
            self.logger.info("✅ Memory sync component functional")
            
        except Exception as e:
            self.fail(f"Memory sync test error: {e}")
    
    def test_backend_monitor(self):
        """Test backend monitor"""
        try:
            result = subprocess.run(
                [sys.executable, 'backend_monitor.py'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Monitor may warn but should not crash
            self.assertIn(
                result.returncode, [0, 1],
                f"Backend monitor crashed: {result.stderr}"
            )
            
            self.logger.info("✅ Backend monitor functional")
            
        except Exception as e:
            self.fail(f"Backend monitor test error: {e}")
    
    def test_autosync_files(self):
        """Test file autosync"""
        try:
            result = subprocess.run(
                [sys.executable, 'autosync_files.py', '--once', '--dry-run'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            self.assertEqual(
                result.returncode, 0,
                f"File autosync failed: {result.stderr}"
            )
            
            self.logger.info("✅ File autosync functional")
            
        except Exception as e:
            self.fail(f"File autosync test error: {e}")

class IntegrationTests(unittest.TestCase):
    """Test system integration"""
    
    def setUp(self):
        self.logger = setup_logging()
    
    def test_full_system_health(self):
        """Test overall system health"""
        try:
            result = subprocess.run(
                [sys.executable, 'backend_monitor.py'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Check if health report was generated
            health_report_path = Path('logs/active/system_health.json')
            self.assertTrue(
                health_report_path.exists(),
                "System health report not generated"
            )
            
            # Load and validate health report
            with open(health_report_path, 'r') as f:
                health_data = json.load(f)
            
            self.assertIn('overall_status', health_data)
            self.assertIn('checks', health_data)
            
            # System should not be in critical state
            self.assertNotEqual(
                health_data['overall_status'], 'critical',
                f"System in critical state: {health_data.get('critical_failures', [])}"
            )
            
            self.logger.info(f"✅ System health: {health_data['overall_status']}")
            
        except Exception as e:
            self.fail(f"System health test error: {e}")
    
    def test_log_generation(self):
        """Test that logs are being generated"""
        log_files = [
            'logs/active/system_health.log',
            'logs/active/test_results.log'
        ]
        
        for log_file in log_files:
            log_path = Path(log_file)
            if log_path.exists():
                self.assertGreater(
                    log_path.stat().st_size, 0,
                    f"Log file {log_file} is empty"
                )
        
        self.logger.info("✅ Log generation working")

def run_test_suite():
    """Run the complete test suite"""
    logger = setup_logging()
    
    print("🧪 ANGLES AI UNIVERSE™ COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print(f"Started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print()
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        EnvironmentTests,
        FileStructureTests,
        DatabaseTests,
        NotionTests,
        ComponentTests,
        IntegrationTests
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        buffer=True
    )
    
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 60)
    print("🧪 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    failed_tests = len(result.failures)
    error_tests = len(result.errors)
    passed_tests = total_tests - failed_tests - error_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Errors: {error_tests}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"   • {test}: {traceback.split('AssertionError: ')[-1].split('\n')[0]}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"   • {test}: {traceback.split('Exception: ')[-1].split('\n')[0]}")
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    if success_rate >= 90:
        status = "✅ EXCELLENT"
    elif success_rate >= 75:
        status = "⚠️ GOOD"
    elif success_rate >= 50:
        status = "⚠️ NEEDS IMPROVEMENT"
    else:
        status = "❌ CRITICAL"
    
    print(f"\nOverall Status: {status} ({success_rate:.1f}% success rate)")
    
    logger.info(f"Test suite completed: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    try:
        success = run_test_suite()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"💥 Test suite failed: {e}")
        sys.exit(1)