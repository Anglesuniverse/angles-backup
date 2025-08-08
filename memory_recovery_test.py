#!/usr/bin/env python3
"""
Memory Recovery System Test Suite
Comprehensive testing for 4-level fallback restore system

Test Scenarios:
- Individual source testing
- Auto-restore with various failure combinations
- Mock testing to avoid hitting live APIs

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import json
import logging
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List
import shutil

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from memory_recovery import (
    MemoryRecoverySystem,
    restore_from_github,
    restore_from_supabase,
    restore_from_local,
    restore_from_notion,
    auto_restore
)

class MemoryRecoveryTestSuite:
    """Comprehensive test suite for memory recovery system"""
    
    def __init__(self):
        """Initialize test suite"""
        self.test_results = []
        self.setup_test_logging()
        self.setup_test_environment()
        
        self.logger.info("🧪 MEMORY RECOVERY TEST SUITE INITIALIZED")
        self.logger.info("=" * 60)
    
    def setup_test_logging(self):
        """Setup test-specific logging"""
        # Create test logger
        self.logger = logging.getLogger('memory_recovery_test')
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler for test log
        test_log_file = Path('last_restore.log')
        file_handler = logging.FileHandler(test_log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - TEST - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def setup_test_environment(self):
        """Setup test environment and dummy files"""
        # Ensure all dummy backup files exist
        dummy_files = [
            'backup_github.json',
            'backup_supabase.json', 
            'backup_local.json',
            'backup_notion.json'
        ]
        
        for dummy_file in dummy_files:
            if not Path(dummy_file).exists():
                self.logger.warning(f"Creating missing dummy file: {dummy_file}")
                self.create_dummy_backup(dummy_file)
    
    def create_dummy_backup(self, filename: str):
        """Create a dummy backup file for testing"""
        source_name = filename.replace('backup_', '').replace('.json', '').title()
        
        dummy_data = {
            "source": source_name,
            "data": f"This is {source_name} backup",
            "version": datetime.now().strftime('%Y-%m-%d'),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_data": True
        }
        
        with open(filename, 'w') as f:
            json.dump(dummy_data, f, indent=2)
        
        self.logger.info(f"✅ Created dummy backup: {filename}")
    
    def log_test_result(self, test_name: str, success: bool, details: str = "", data: Dict[str, Any] = None):
        """Log test result"""
        result = {
            "test_name": test_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": success,
            "details": details,
            "data_source": data.get('source') if data else None,
            "data_size": len(str(data)) if data else 0
        }
        
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        self.logger.info(f"{status} - {test_name}: {details}")
        
        # Log to restore history as well
        self.append_to_restore_history(result)
    
    def append_to_restore_history(self, test_result: Dict[str, Any]):
        """Append test result to restore history"""
        history_file = Path('restore_history.json')
        
        # Load existing history
        history = []
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        
        # Append test result
        history.append(test_result)
        
        # Keep only last 1000 entries
        if len(history) > 1000:
            history = history[-1000:]
        
        # Save updated history
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def test_individual_sources(self):
        """Test each restore source individually"""
        self.logger.info("🔬 Testing individual restore sources...")
        
        # Test GitHub restore
        try:
            data = restore_from_github(mock=True)
            if data and data.get('source') == 'GitHub':
                self.log_test_result("GitHub Individual", True, "GitHub restore successful", data)
            else:
                self.log_test_result("GitHub Individual", False, "GitHub restore failed or invalid data")
        except Exception as e:
            self.log_test_result("GitHub Individual", False, f"GitHub restore exception: {e}")
        
        # Test Supabase restore
        try:
            data = restore_from_supabase(mock=True)
            if data and data.get('source') == 'Supabase':
                self.log_test_result("Supabase Individual", True, "Supabase restore successful", data)
            else:
                self.log_test_result("Supabase Individual", False, "Supabase restore failed or invalid data")
        except Exception as e:
            self.log_test_result("Supabase Individual", False, f"Supabase restore exception: {e}")
        
        # Test Local restore
        try:
            data = restore_from_local(mock=True)
            if data and data.get('source') == 'Local':
                self.log_test_result("Local Individual", True, "Local restore successful", data)
            else:
                self.log_test_result("Local Individual", False, "Local restore failed or invalid data")
        except Exception as e:
            self.log_test_result("Local Individual", False, f"Local restore exception: {e}")
        
        # Test Notion restore
        try:
            data = restore_from_notion(mock=True)
            if data and data.get('source') == 'Notion':
                self.log_test_result("Notion Individual", True, "Notion restore successful", data)
            else:
                self.log_test_result("Notion Individual", False, "Notion restore failed or invalid data")
        except Exception as e:
            self.log_test_result("Notion Individual", False, f"Notion restore exception: {e}")
    
    def test_auto_restore_scenarios(self):
        """Test auto_restore in various failure scenarios"""
        self.logger.info("🔄 Testing auto_restore scenarios...")
        
        # Scenario 1: Only GitHub available
        self.test_scenario_github_only()
        
        # Scenario 2: GitHub down, Supabase up
        self.test_scenario_github_down_supabase_up()
        
        # Scenario 3: All but Local down
        self.test_scenario_only_local_available()
        
        # Scenario 4: Only Notion up
        self.test_scenario_only_notion_available()
        
        # Scenario 5: All sources available (should use GitHub first)
        self.test_scenario_all_available()
        
        # Scenario 6: All sources down
        self.test_scenario_all_down()
    
    def test_scenario_github_only(self):
        """Test scenario: Only GitHub available"""
        self.logger.info("📝 Scenario 1: Only GitHub available")
        
        # Temporarily hide other backup files
        backup_files = ['backup_supabase.json', 'backup_local.json', 'backup_notion.json']
        temp_files = []
        
        try:
            # Move other backup files temporarily
            for backup_file in backup_files:
                if Path(backup_file).exists():
                    temp_name = f"{backup_file}.temp"
                    shutil.move(backup_file, temp_name)
                    temp_files.append((backup_file, temp_name))
            
            # Test auto_restore
            data = auto_restore(mock=True)
            if data and data.get('source') == 'GitHub':
                self.log_test_result("Auto-Restore GitHub Only", True, "Auto-restore successful with GitHub only", data)
            else:
                self.log_test_result("Auto-Restore GitHub Only", False, "Auto-restore failed with GitHub only")
            
        except Exception as e:
            self.log_test_result("Auto-Restore GitHub Only", False, f"Exception: {e}")
        
        finally:
            # Restore backup files
            for original, temp in temp_files:
                if Path(temp).exists():
                    shutil.move(temp, original)
    
    def test_scenario_github_down_supabase_up(self):
        """Test scenario: GitHub down, Supabase up"""
        self.logger.info("📝 Scenario 2: GitHub down, Supabase up")
        
        # Temporarily hide GitHub and other backup files
        backup_files = ['backup_github.json', 'backup_local.json', 'backup_notion.json']
        temp_files = []
        
        try:
            # Move backup files temporarily
            for backup_file in backup_files:
                if Path(backup_file).exists():
                    temp_name = f"{backup_file}.temp"
                    shutil.move(backup_file, temp_name)
                    temp_files.append((backup_file, temp_name))
            
            # Test auto_restore
            data = auto_restore(mock=True)
            if data and data.get('source') == 'Supabase':
                self.log_test_result("Auto-Restore Supabase Fallback", True, "Auto-restore fallback to Supabase successful", data)
            else:
                self.log_test_result("Auto-Restore Supabase Fallback", False, "Auto-restore failed to fallback to Supabase")
            
        except Exception as e:
            self.log_test_result("Auto-Restore Supabase Fallback", False, f"Exception: {e}")
        
        finally:
            # Restore backup files
            for original, temp in temp_files:
                if Path(temp).exists():
                    shutil.move(temp, original)
    
    def test_scenario_only_local_available(self):
        """Test scenario: All but Local down"""
        self.logger.info("📝 Scenario 3: All but Local down")
        
        # Temporarily hide all backup files except local
        backup_files = ['backup_github.json', 'backup_supabase.json', 'backup_notion.json']
        temp_files = []
        
        try:
            # Move backup files temporarily
            for backup_file in backup_files:
                if Path(backup_file).exists():
                    temp_name = f"{backup_file}.temp"
                    shutil.move(backup_file, temp_name)
                    temp_files.append((backup_file, temp_name))
            
            # Test auto_restore
            data = auto_restore(mock=True)
            if data and data.get('source') == 'Local':
                self.log_test_result("Auto-Restore Local Fallback", True, "Auto-restore fallback to Local successful", data)
            else:
                self.log_test_result("Auto-Restore Local Fallback", False, "Auto-restore failed to fallback to Local")
            
        except Exception as e:
            self.log_test_result("Auto-Restore Local Fallback", False, f"Exception: {e}")
        
        finally:
            # Restore backup files
            for original, temp in temp_files:
                if Path(temp).exists():
                    shutil.move(temp, original)
    
    def test_scenario_only_notion_available(self):
        """Test scenario: Only Notion up"""
        self.logger.info("📝 Scenario 4: Only Notion up")
        
        # Temporarily hide all backup files except notion
        backup_files = ['backup_github.json', 'backup_supabase.json', 'backup_local.json']
        temp_files = []
        
        try:
            # Move backup files temporarily
            for backup_file in backup_files:
                if Path(backup_file).exists():
                    temp_name = f"{backup_file}.temp"
                    shutil.move(backup_file, temp_name)
                    temp_files.append((backup_file, temp_name))
            
            # Test auto_restore
            data = auto_restore(mock=True)
            if data and data.get('source') == 'Notion':
                self.log_test_result("Auto-Restore Notion Fallback", True, "Auto-restore fallback to Notion successful", data)
            else:
                self.log_test_result("Auto-Restore Notion Fallback", False, "Auto-restore failed to fallback to Notion")
            
        except Exception as e:
            self.log_test_result("Auto-Restore Notion Fallback", False, f"Exception: {e}")
        
        finally:
            # Restore backup files
            for original, temp in temp_files:
                if Path(temp).exists():
                    shutil.move(temp, original)
    
    def test_scenario_all_available(self):
        """Test scenario: All sources available (should prioritize GitHub)"""
        self.logger.info("📝 Scenario 5: All sources available")
        
        try:
            # Test auto_restore with all sources available
            data = auto_restore(mock=True)
            if data and data.get('source') == 'GitHub':
                self.log_test_result("Auto-Restore Priority", True, "Auto-restore correctly prioritized GitHub", data)
            else:
                self.log_test_result("Auto-Restore Priority", False, f"Auto-restore used wrong source: {data.get('source') if data else 'None'}")
            
        except Exception as e:
            self.log_test_result("Auto-Restore Priority", False, f"Exception: {e}")
    
    def test_scenario_all_down(self):
        """Test scenario: All sources down"""
        self.logger.info("📝 Scenario 6: All sources down")
        
        # Temporarily hide all backup files
        backup_files = ['backup_github.json', 'backup_supabase.json', 'backup_local.json', 'backup_notion.json']
        temp_files = []
        
        try:
            # Move all backup files temporarily
            for backup_file in backup_files:
                if Path(backup_file).exists():
                    temp_name = f"{backup_file}.temp"
                    shutil.move(backup_file, temp_name)
                    temp_files.append((backup_file, temp_name))
            
            # Test auto_restore
            data = auto_restore(mock=True)
            if data is None:
                self.log_test_result("Auto-Restore All Down", True, "Auto-restore correctly returned None when all sources down")
            else:
                self.log_test_result("Auto-Restore All Down", False, f"Auto-restore should have failed but returned: {data.get('source')}")
            
        except Exception as e:
            self.log_test_result("Auto-Restore All Down", False, f"Exception: {e}")
        
        finally:
            # Restore backup files
            for original, temp in temp_files:
                if Path(temp).exists():
                    shutil.move(temp, original)
    
    def test_integrity_validation(self):
        """Test backup integrity validation"""
        self.logger.info("🔍 Testing integrity validation...")
        
        # Create invalid backup file
        invalid_backup = {
            "invalid": "data",
            "missing": "required_keys"
        }
        
        with open('backup_invalid.json', 'w') as f:
            json.dump(invalid_backup, f)
        
        try:
            recovery = MemoryRecoverySystem()
            valid = recovery._validate_backup_integrity(invalid_backup)
            
            if not valid:
                self.log_test_result("Integrity Validation", True, "Correctly rejected invalid backup structure")
            else:
                self.log_test_result("Integrity Validation", False, "Failed to reject invalid backup structure")
        
        except Exception as e:
            self.log_test_result("Integrity Validation", False, f"Exception during validation: {e}")
        
        finally:
            # Cleanup
            Path('backup_invalid.json').unlink(missing_ok=True)
    
    def run_all_tests(self):
        """Run all tests in the test suite"""
        self.logger.info("🚀 Starting comprehensive memory recovery test suite...")
        
        start_time = datetime.now()
        
        # Run all test categories
        self.test_individual_sources()
        self.test_auto_restore_scenarios()
        self.test_integrity_validation()
        
        # Calculate test duration
        duration = (datetime.now() - start_time).total_seconds()
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        self.logger.info("=" * 60)
        self.logger.info("🏁 TEST SUITE SUMMARY")
        self.logger.info(f"Total Tests: {total_tests}")
        self.logger.info(f"Passed: {passed_tests}")
        self.logger.info(f"Failed: {failed_tests}")
        self.logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        self.logger.info(f"Duration: {duration:.2f} seconds")
        self.logger.info("=" * 60)
        
        # Save test results
        self.save_test_results(duration, passed_tests, failed_tests)
        
        return passed_tests == total_tests
    
    def save_test_results(self, duration: float, passed: int, failed: int):
        """Save test results to file"""
        test_summary = {
            "test_run_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_tests": len(self.test_results),
            "passed_tests": passed,
            "failed_tests": failed,
            "success_rate": (passed / len(self.test_results)) * 100 if self.test_results else 0,
            "duration_seconds": duration,
            "test_details": self.test_results
        }
        
        # Save detailed results
        with open('test_results.json', 'w') as f:
            json.dump(test_summary, f, indent=2)
        
        self.logger.info("💾 Test results saved to test_results.json")

def main():
    """Main test execution"""
    try:
        print("🧪 MEMORY RECOVERY SYSTEM TEST SUITE")
        print("=" * 50)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print()
        
        # Run test suite
        test_suite = MemoryRecoveryTestSuite()
        success = test_suite.run_all_tests()
        
        print()
        if success:
            print("✅ All tests passed!")
            return 0
        else:
            print("❌ Some tests failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Test suite interrupted by user")
        return 130
    except Exception as e:
        print(f"💥 Test suite failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())