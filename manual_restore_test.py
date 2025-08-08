#!/usr/bin/env python3
"""
Manual Restore Test for Angles AI Universe™ Memory System
Comprehensive testing of GitHub backup & restore pipeline

This script:
1. Runs github_restore.py using latest backup from angles-backup repository
2. Verifies all files restore to correct local directories
3. Checks restored memory files match format required by memory_bridge.py
4. Detects data corruption or missing files
5. Verifies memory_bridge.py runs successfully after restore
6. Logs all output and marks test as PASSED or FAILED

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import logging
import subprocess
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from logging.handlers import RotatingFileHandler

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

def setup_logging() -> logging.Logger:
    """Setup test-specific logging"""
    # Ensure logs directory exists
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger('restore_test')
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Rotating file handler for restore test logs
    file_handler = RotatingFileHandler(
        'logs/restore_test.log',
        maxBytes=1024*1024,  # 1MB
        backupCount=5,
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

class RestoreTestSuite:
    """Comprehensive restore testing suite"""
    
    def __init__(self):
        """Initialize the test suite"""
        self.logger = setup_logging()
        self.start_time = datetime.now()
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "overall_status": "PENDING"
        }
        
        # Create backup of current state
        self.backup_dir = self._create_state_backup()
        
        self.logger.info("🧪 MANUAL RESTORE TEST SUITE INITIALIZED")
        self.logger.info("=" * 60)
    
    def _create_state_backup(self) -> Path:
        """Create backup of current system state"""
        backup_dir = Path(f"temp_backup_{int(self.start_time.timestamp())}")
        backup_dir.mkdir(exist_ok=True)
        
        # Backup critical directories
        for dir_name in ['export', 'logs', 'data']:
            src_dir = Path(dir_name)
            if src_dir.exists():
                dst_dir = backup_dir / dir_name
                try:
                    shutil.copytree(src_dir, dst_dir)
                except Exception:
                    pass  # Ignore copy errors
        
        self.logger.info(f"📁 Created state backup: {backup_dir}")
        return backup_dir
    
    def _restore_state_backup(self):
        """Restore system state from backup"""
        try:
            for dir_name in ['export', 'logs', 'data']:
                src_dir = self.backup_dir / dir_name
                dst_dir = Path(dir_name)
                if src_dir.exists():
                    if dst_dir.exists():
                        shutil.rmtree(dst_dir)
                    shutil.copytree(src_dir, dst_dir)
            
            # Clean up backup
            shutil.rmtree(self.backup_dir, ignore_errors=True)
            self.logger.info("🔄 Restored system state from backup")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to restore state backup: {e}")
    
    def _run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and track results"""
        self.test_results["total_tests"] += 1
        self.logger.info(f"🔬 Running test: {test_name}")
        
        try:
            result = test_func()
            if result:
                self.test_results["passed_tests"] += 1
                self.logger.info(f"✅ {test_name}: PASSED")
            else:
                self.test_results["failed_tests"] += 1
                self.logger.error(f"❌ {test_name}: FAILED")
            
            self.test_results["test_details"].append({
                "name": test_name,
                "status": "PASSED" if result else "FAILED",
                "timestamp": datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            self.test_results["failed_tests"] += 1
            self.logger.error(f"💥 {test_name}: ERROR - {e}")
            self.test_results["test_details"].append({
                "name": test_name,
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    def test_git_repository_access(self) -> bool:
        """Test 1: Verify git repository access and latest backup availability"""
        self.logger.info("📡 Testing git repository access...")
        
        try:
            # Check if git is available and repo is accessible
            result = subprocess.run([
                'git', 'remote', 'get-url', 'origin'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.logger.error("Git repository not accessible")
                return False
            
            repo_url = result.stdout.strip()
            self.logger.info(f"🔗 Repository URL: {repo_url}")
            
            # Pull latest changes
            pull_result = subprocess.run([
                'git', 'pull', 'origin', 'main'
            ], capture_output=True, text=True, timeout=60)
            
            self.logger.info("📥 Git pull completed")
            
            # Check for backup files
            export_dir = Path('export')
            if not export_dir.exists():
                self.logger.error("Export directory not found")
                return False
            
            backup_files = list(export_dir.glob('*.json'))
            if not backup_files:
                self.logger.error("No backup files found in export directory")
                return False
            
            self.logger.info(f"📄 Found {len(backup_files)} backup files")
            for backup_file in backup_files:
                self.logger.info(f"  - {backup_file.name}")
            
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.error("Git operations timed out")
            return False
        except Exception as e:
            self.logger.error(f"Git repository access failed: {e}")
            return False
    
    def test_restore_execution(self) -> bool:
        """Test 2: Execute github_restore.py with dry-run first, then live restore"""
        self.logger.info("🔄 Testing restore execution...")
        
        try:
            # First, run dry-run to verify restore plan
            self.logger.info("🧪 Running dry-run restore...")
            dry_run_result = subprocess.run([
                sys.executable, 'run_restore_now.py', '--dry-run'
            ], capture_output=True, text=True, timeout=300)
            
            if dry_run_result.returncode != 0:
                self.logger.error(f"Dry-run restore failed: {dry_run_result.stderr}")
                return False
            
            self.logger.info("✅ Dry-run completed successfully")
            
            # Parse dry-run output for expected restore counts
            dry_run_output = dry_run_result.stdout
            self.logger.info("📊 Dry-run results:")
            for line in dry_run_output.split('\n'):
                if 'records' in line.lower() or 'files' in line.lower():
                    self.logger.info(f"  {line.strip()}")
            
            # Run actual restore
            self.logger.info("🚀 Running live restore...")
            restore_result = subprocess.run([
                sys.executable, 'run_restore_now.py'
            ], capture_output=True, text=True, timeout=300, input='yes\n')
            
            if restore_result.returncode != 0:
                self.logger.error(f"Live restore failed: {restore_result.stderr}")
                self.logger.error(f"Restore stdout: {restore_result.stdout}")
                return False
            
            self.logger.info("✅ Live restore completed successfully")
            
            # Log restore results
            restore_output = restore_result.stdout
            self.logger.info("📊 Restore results:")
            for line in restore_output.split('\n'):
                if any(keyword in line.lower() for keyword in ['restored', 'inserted', 'updated', 'success', 'failed']):
                    self.logger.info(f"  {line.strip()}")
            
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.error("Restore execution timed out")
            return False
        except Exception as e:
            self.logger.error(f"Restore execution failed: {e}")
            return False
    
    def test_file_integrity(self) -> bool:
        """Test 3: Verify file integrity and correct directory structure"""
        self.logger.info("🔍 Testing file integrity...")
        
        try:
            # Check for expected files and directories
            expected_files = [
                'export/decisions_20250807.json',  # Current export format
                'memory_bridge.py',
                'memory_sync_agent.py',
                'github_restore.py'
            ]
            
            missing_files = []
            for file_path in expected_files:
                if not Path(file_path).exists():
                    missing_files.append(file_path)
            
            if missing_files:
                self.logger.error(f"Missing files: {missing_files}")
                return False
            
            self.logger.info("✅ All expected files present")
            
            # Verify export file integrity
            export_files = list(Path('export').glob('*.json'))
            valid_exports = 0
            
            for export_file in export_files:
                try:
                    with open(export_file, 'r') as f:
                        data = json.load(f)
                    
                    # Check for required structure
                    if isinstance(data, dict):
                        if 'decisions' in data and isinstance(data['decisions'], list):
                            decisions = data['decisions']
                        elif 'export_timestamp' in data or 'total_decisions' in data:
                            decisions = data.get('decisions', [])
                        else:
                            decisions = [data]  # Single record
                    elif isinstance(data, list):
                        decisions = data
                    else:
                        self.logger.warning(f"Unexpected JSON structure in {export_file}")
                        continue
                    
                    # Validate decision records
                    required_fields = ['decision', 'date', 'type', 'active']
                    valid_records = 0
                    
                    for record in decisions:
                        if all(field in record for field in required_fields):
                            valid_records += 1
                    
                    self.logger.info(f"📄 {export_file.name}: {valid_records}/{len(decisions)} valid records")
                    
                    if valid_records > 0:
                        valid_exports += 1
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON in {export_file}: {e}")
                except Exception as e:
                    self.logger.error(f"Error reading {export_file}: {e}")
            
            if valid_exports == 0:
                self.logger.error("No valid export files found")
                return False
            
            self.logger.info(f"✅ {valid_exports}/{len(export_files)} export files are valid")
            return True
            
        except Exception as e:
            self.logger.error(f"File integrity check failed: {e}")
            return False
    
    def test_memory_bridge_compatibility(self) -> bool:
        """Test 4: Verify restored files match memory_bridge.py format requirements"""
        self.logger.info("🔗 Testing memory_bridge.py compatibility...")
        
        try:
            # Import memory bridge to test compatibility
            from memory_bridge import MemoryBridge
            
            # Test if we can initialize the memory bridge
            bridge = MemoryBridge()
            self.logger.info("✅ MemoryBridge initialized successfully")
            
            # Test database connection
            result = bridge.supabase.table("decision_vault").select("id").limit(1).execute()
            self.logger.info("✅ Database connection verified")
            
            # Test if decision format matches expectations
            recent_decisions = bridge.supabase.table("decision_vault").select("*").limit(5).execute()
            
            if recent_decisions.data:
                decision_sample = recent_decisions.data[0]
                expected_fields = ['id', 'decision', 'date', 'type', 'active']
                
                missing_fields = [field for field in expected_fields if field not in decision_sample]
                if missing_fields:
                    self.logger.error(f"Decision records missing required fields: {missing_fields}")
                    return False
                
                self.logger.info("✅ Decision record format matches memory_bridge.py requirements")
                
                # Log sample decision structure
                self.logger.info("📋 Sample decision structure:")
                for field in expected_fields:
                    value = decision_sample.get(field, 'N/A')
                    if field == 'decision':
                        value = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    self.logger.info(f"  {field}: {value}")
            else:
                self.logger.warning("No decisions found in database")
            
            return True
            
        except ImportError as e:
            self.logger.error(f"Failed to import memory_bridge: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Memory bridge compatibility test failed: {e}")
            return False
    
    def test_memory_bridge_execution(self) -> bool:
        """Test 5: Verify memory_bridge.py runs successfully after restore"""
        self.logger.info("🏃 Testing memory_bridge.py execution...")
        
        try:
            # Run memory_bridge.py
            self.logger.info("🚀 Executing memory_bridge.py...")
            
            bridge_result = subprocess.run([
                sys.executable, 'memory_bridge.py'
            ], capture_output=True, text=True, timeout=120)
            
            # Log the output
            if bridge_result.stdout:
                self.logger.info("📤 Memory bridge stdout:")
                for line in bridge_result.stdout.split('\n'):
                    if line.strip():
                        self.logger.info(f"  {line}")
            
            if bridge_result.stderr:
                self.logger.info("📥 Memory bridge stderr:")
                for line in bridge_result.stderr.split('\n'):
                    if line.strip():
                        self.logger.info(f"  {line}")
            
            # Check exit code
            if bridge_result.returncode == 0:
                self.logger.info("✅ memory_bridge.py executed successfully")
                return True
            else:
                self.logger.error(f"❌ memory_bridge.py failed with exit code: {bridge_result.returncode}")
                return False
            
        except subprocess.TimeoutExpired:
            self.logger.error("memory_bridge.py execution timed out")
            return False
        except Exception as e:
            self.logger.error(f"memory_bridge.py execution failed: {e}")
            return False
    
    def test_data_corruption_check(self) -> bool:
        """Test 6: Check for data corruption or missing files"""
        self.logger.info("🔍 Checking for data corruption...")
        
        try:
            corruption_found = False
            
            # Check JSON files for syntax errors
            json_files = list(Path('.').rglob('*.json'))
            for json_file in json_files:
                try:
                    with open(json_file, 'r') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Corrupted JSON file: {json_file} - {e}")
                    corruption_found = True
                except Exception as e:
                    self.logger.warning(f"Could not read {json_file}: {e}")
            
            if not corruption_found:
                self.logger.info("✅ No JSON file corruption detected")
            
            # Check for critical missing files
            critical_files = [
                'memory_bridge.py',
                'memory_sync_agent.py',
                'github_restore.py',
                'run_restore_now.py'
            ]
            
            missing_critical = []
            for file_path in critical_files:
                if not Path(file_path).exists():
                    missing_critical.append(file_path)
            
            if missing_critical:
                self.logger.error(f"Missing critical files: {missing_critical}")
                corruption_found = True
            else:
                self.logger.info("✅ All critical files present")
            
            # Check export directory structure
            export_dir = Path('export')
            if export_dir.exists():
                export_files = list(export_dir.glob('*.json'))
                if export_files:
                    self.logger.info(f"✅ Export directory contains {len(export_files)} files")
                else:
                    self.logger.warning("Export directory is empty")
            else:
                self.logger.error("Export directory missing")
                corruption_found = True
            
            return not corruption_found
            
        except Exception as e:
            self.logger.error(f"Data corruption check failed: {e}")
            return False
    
    def run_full_test_suite(self) -> Dict[str, Any]:
        """Run the complete restore test suite"""
        self.logger.info("🚀 STARTING COMPREHENSIVE RESTORE TEST SUITE")
        self.logger.info("=" * 60)
        
        try:
            # Define test sequence
            tests = [
                ("Git Repository Access", self.test_git_repository_access),
                ("Restore Execution", self.test_restore_execution),
                ("File Integrity", self.test_file_integrity),
                ("Memory Bridge Compatibility", self.test_memory_bridge_compatibility),
                ("Memory Bridge Execution", self.test_memory_bridge_execution),
                ("Data Corruption Check", self.test_data_corruption_check)
            ]
            
            # Run all tests
            for test_name, test_func in tests:
                success = self._run_test(test_name, test_func)
                if not success:
                    self.logger.warning(f"⚠️ Test failed: {test_name}")
            
            # Calculate results
            duration = (datetime.now() - self.start_time).total_seconds()
            pass_rate = (self.test_results["passed_tests"] / self.test_results["total_tests"]) * 100 if self.test_results["total_tests"] > 0 else 0
            
            # Determine overall status
            if self.test_results["failed_tests"] == 0:
                self.test_results["overall_status"] = "PASSED"
                overall_result = "✅ PASSED"
            else:
                self.test_results["overall_status"] = "FAILED"
                overall_result = "❌ FAILED"
            
            # Final summary
            self.logger.info("=" * 60)
            self.logger.info("🏁 RESTORE TEST SUITE COMPLETED")
            self.logger.info("=" * 60)
            self.logger.info(f"Duration: {duration:.2f} seconds")
            self.logger.info(f"Total Tests: {self.test_results['total_tests']}")
            self.logger.info(f"Passed: {self.test_results['passed_tests']}")
            self.logger.info(f"Failed: {self.test_results['failed_tests']}")
            self.logger.info(f"Pass Rate: {pass_rate:.1f}%")
            self.logger.info(f"Overall Status: {overall_result}")
            self.logger.info("=" * 60)
            
            # Add summary to results
            self.test_results.update({
                "duration_seconds": duration,
                "pass_rate_percent": pass_rate,
                "summary": f"Restore test suite completed with {self.test_results['passed_tests']}/{self.test_results['total_tests']} tests passing"
            })
            
            return self.test_results
            
        except Exception as e:
            self.logger.error(f"💥 Test suite execution failed: {e}")
            self.test_results["overall_status"] = "ERROR"
            self.test_results["error"] = str(e)
            return self.test_results
        
        finally:
            # Restore original state
            self._restore_state_backup()

def main():
    """Main entry point for manual restore testing"""
    try:
        print()
        print("🧪 ANGLES AI UNIVERSE™ MANUAL RESTORE TEST")
        print("=" * 55)
        print("Testing GitHub backup & restore pipeline...")
        print()
        
        # Run test suite
        test_suite = RestoreTestSuite()
        results = test_suite.run_full_test_suite()
        
        # Print final status
        print()
        print("🏁 FINAL TEST RESULTS:")
        print("=" * 30)
        print(f"Status: {results['overall_status']}")
        print(f"Passed: {results['passed_tests']}/{results['total_tests']}")
        print(f"Duration: {results.get('duration_seconds', 0):.1f}s")
        print(f"Details: logs/restore_test.log")
        print()
        
        # Exit with appropriate code
        if results['overall_status'] == 'PASSED':
            print("✅ All tests passed - Restore pipeline verified!")
            sys.exit(0)
        else:
            print("❌ Some tests failed - Check logs for details")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()