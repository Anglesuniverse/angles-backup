#!/usr/bin/env python3
"""
Pre-Backup Sanity Check for Angles AI Universe™ Memory System
Comprehensive validation system that runs before every backup operation

This module provides:
- File integrity validation (JSON syntax, empty files)
- Schema verification for decision files 
- Timestamp validation (ISO 8601 format)
- File size checks (10MB+ warnings)
- Sensitive data detection
- Version tag verification
- Comprehensive logging and Notion integration

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import re
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass, field

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from notion_backup_logger import create_notion_logger

@dataclass
class SanityCheckResult:
    """Data structure for sanity check results"""
    check_name: str
    passed: bool
    files_checked: int = 0
    errors_found: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    details: str = ""

class SanityChecker:
    """Comprehensive pre-backup sanity checking system"""
    
    def __init__(self):
        """Initialize the sanity checker"""
        self.logger = self._setup_logging()
        self.notion_logger = create_notion_logger()
        self.start_time = datetime.now()
        
        # Configuration
        self.max_file_size_mb = 10
        self.expected_version = "2.0.0"  # Based on export files
        
        # Sensitive data patterns (basic detection)
        self.sensitive_patterns = [
            r'sk-[a-zA-Z0-9]{48}',  # OpenAI API keys
            r'ghp_[a-zA-Z0-9]{36}',  # GitHub tokens
            r'supabase_[a-zA-Z0-9]{40}',  # Supabase keys
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN format
            r'\b4[0-9]{12}(?:[0-9]{3})?\b',  # Credit card numbers (Visa)
        ]
        
        # Expected schema for decision files
        self.required_decision_fields = {
            "id": str,
            "decision": str, 
            "type": str,
            "date": str,
            "active": bool
        }
        
        # Optional fields that are commonly present
        self.optional_decision_fields = {
            "synced_at": str,
            "export_timestamp": str,
            "comment": str
        }
        
        self.logger.info("🔍 SANITY CHECKER INITIALIZED")
        self.logger.info("=" * 50)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup sanity check logging"""
        # Ensure logs directory exists
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('sanity_check')
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Rotating file handler
        file_handler = RotatingFileHandler(
            'logs/sanity_check.log',
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
    
    def check_file_integrity(self) -> SanityCheckResult:
        """Check file integrity: valid JSON and no empty files"""
        self.logger.info("🔍 Checking file integrity...")
        
        result = SanityCheckResult(
            check_name="File Integrity",
            passed=True
        )
        
        # Check export and logs directories
        check_dirs = ['export', 'logs']
        
        for dir_name in check_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                result.warnings.append(f"Directory {dir_name}/ does not exist")
                continue
            
            # Check all files in directory
            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    result.files_checked += 1
                    
                    # Check for empty files
                    if file_path.stat().st_size == 0:
                        error_msg = f"Empty file found: {file_path}"
                        result.errors.append(error_msg)
                        result.errors_found += 1
                        self.logger.error(f"❌ {error_msg}")
                        continue
                    
                    # Check JSON validity for .json files
                    if file_path.suffix.lower() == '.json':
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                json.load(f)
                            self.logger.debug(f"✅ Valid JSON: {file_path}")
                        except json.JSONDecodeError as e:
                            error_msg = f"Invalid JSON in {file_path}: {e}"
                            result.errors.append(error_msg)
                            result.errors_found += 1
                            self.logger.error(f"❌ {error_msg}")
                        except Exception as e:
                            error_msg = f"Could not read {file_path}: {e}"
                            result.errors.append(error_msg)
                            result.errors_found += 1
                            self.logger.error(f"❌ {error_msg}")
        
        if result.errors_found > 0:
            result.passed = False
            result.details = f"Found {result.errors_found} file integrity issues"
        else:
            result.details = f"All {result.files_checked} files passed integrity checks"
            self.logger.info(f"✅ File integrity check passed: {result.files_checked} files")
        
        return result
    
    def check_schema_verification(self) -> SanityCheckResult:
        """Check that decision files contain required schema fields"""
        self.logger.info("🔍 Checking schema verification...")
        
        result = SanityCheckResult(
            check_name="Schema Verification",
            passed=True
        )
        
        export_dir = Path('export')
        if not export_dir.exists():
            result.errors.append("Export directory does not exist")
            result.errors_found += 1
            result.passed = False
            return result
        
        json_files = list(export_dir.glob('*.json'))
        
        for json_file in json_files:
            result.files_checked += 1
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle different JSON structures
                if isinstance(data, dict):
                    if 'decisions' in data and isinstance(data['decisions'], list):
                        decisions = data['decisions']
                    else:
                        decisions = [data]  # Single decision
                elif isinstance(data, list):
                    decisions = data
                else:
                    error_msg = f"Unexpected JSON structure in {json_file}"
                    result.errors.append(error_msg)
                    result.errors_found += 1
                    continue
                
                # Check each decision record
                for i, decision in enumerate(decisions):
                    missing_fields = []
                    invalid_types = []
                    
                    # Check required fields
                    for field_name, expected_type in self.required_decision_fields.items():
                        if field_name not in decision:
                            missing_fields.append(field_name)
                        elif not isinstance(decision[field_name], expected_type):
                            invalid_types.append(f"{field_name} (expected {expected_type.__name__}, got {type(decision[field_name]).__name__})")
                    
                    if missing_fields:
                        error_msg = f"Missing required fields in {json_file} record {i}: {missing_fields}"
                        result.errors.append(error_msg)
                        result.errors_found += 1
                        self.logger.error(f"❌ {error_msg}")
                    
                    if invalid_types:
                        error_msg = f"Invalid field types in {json_file} record {i}: {invalid_types}"
                        result.errors.append(error_msg)
                        result.errors_found += 1
                        self.logger.error(f"❌ {error_msg}")
                
                if not decisions:
                    warning_msg = f"No decision records found in {json_file}"
                    result.warnings.append(warning_msg)
                    self.logger.warning(f"⚠️ {warning_msg}")
                else:
                    self.logger.debug(f"✅ Schema validated: {json_file} ({len(decisions)} records)")
                    
            except Exception as e:
                error_msg = f"Error reading {json_file} for schema check: {e}"
                result.errors.append(error_msg)
                result.errors_found += 1
                self.logger.error(f"❌ {error_msg}")
        
        if result.errors_found > 0:
            result.passed = False
            result.details = f"Found {result.errors_found} schema validation errors"
        else:
            result.details = f"All {result.files_checked} files passed schema validation"
            self.logger.info(f"✅ Schema verification passed: {result.files_checked} files")
        
        return result
    
    def check_timestamp_validation(self) -> SanityCheckResult:
        """Check that all timestamps are in valid ISO 8601 format"""
        self.logger.info("🔍 Checking timestamp validation...")
        
        result = SanityCheckResult(
            check_name="Timestamp Validation",
            passed=True
        )
        
        export_dir = Path('export')
        if not export_dir.exists():
            result.errors.append("Export directory does not exist")
            result.errors_found += 1
            result.passed = False
            return result
        
        # ISO 8601 regex pattern
        iso_pattern = re.compile(
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$'
        )
        
        # Simple date pattern (YYYY-MM-DD)
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        
        json_files = list(export_dir.glob('*.json'))
        
        for json_file in json_files:
            result.files_checked += 1
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check top-level timestamps
                if isinstance(data, dict):
                    for key, value in data.items():
                        if 'timestamp' in key.lower() and isinstance(value, str):
                            if not iso_pattern.match(value):
                                error_msg = f"Invalid timestamp format in {json_file}.{key}: {value}"
                                result.errors.append(error_msg)
                                result.errors_found += 1
                                self.logger.error(f"❌ {error_msg}")
                
                # Get decisions array
                if isinstance(data, dict) and 'decisions' in data:
                    decisions = data['decisions']
                elif isinstance(data, list):
                    decisions = data
                else:
                    decisions = [data] if isinstance(data, dict) else []
                
                # Check decision timestamps
                for i, decision in enumerate(decisions):
                    if isinstance(decision, dict):
                        # Check date field (should be YYYY-MM-DD)
                        if 'date' in decision:
                            date_value = decision['date']
                            if isinstance(date_value, str) and not date_pattern.match(date_value):
                                error_msg = f"Invalid date format in {json_file} record {i}: {date_value}"
                                result.errors.append(error_msg)
                                result.errors_found += 1
                                self.logger.error(f"❌ {error_msg}")
                        
                        # Check timestamp fields
                        for field_name, field_value in decision.items():
                            if 'timestamp' in field_name.lower() and isinstance(field_value, str):
                                if not iso_pattern.match(field_value):
                                    error_msg = f"Invalid timestamp format in {json_file} record {i}.{field_name}: {field_value}"
                                    result.errors.append(error_msg)
                                    result.errors_found += 1
                                    self.logger.error(f"❌ {error_msg}")
                
                self.logger.debug(f"✅ Timestamps validated: {json_file}")
                
            except Exception as e:
                error_msg = f"Error reading {json_file} for timestamp check: {e}"
                result.errors.append(error_msg)
                result.errors_found += 1
                self.logger.error(f"❌ {error_msg}")
        
        if result.errors_found > 0:
            result.passed = False
            result.details = f"Found {result.errors_found} timestamp validation errors"
        else:
            result.details = f"All timestamps in {result.files_checked} files are valid"
            self.logger.info(f"✅ Timestamp validation passed: {result.files_checked} files")
        
        return result
    
    def check_file_sizes(self) -> SanityCheckResult:
        """Check for files larger than 10MB"""
        self.logger.info("🔍 Checking file sizes...")
        
        result = SanityCheckResult(
            check_name="File Size Check",
            passed=True
        )
        
        # Check export and logs directories
        check_dirs = ['export', 'logs']
        max_size_bytes = self.max_file_size_mb * 1024 * 1024
        
        for dir_name in check_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                continue
            
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    result.files_checked += 1
                    file_size = file_path.stat().st_size
                    file_size_mb = file_size / (1024 * 1024)
                    
                    if file_size > max_size_bytes:
                        warning_msg = f"Large file detected: {file_path} ({file_size_mb:.2f} MB)"
                        result.warnings.append(warning_msg)
                        self.logger.warning(f"⚠️ {warning_msg}")
                    
                    self.logger.debug(f"📏 {file_path}: {file_size_mb:.2f} MB")
        
        result.details = f"Checked {result.files_checked} files, {len(result.warnings)} large files found"
        self.logger.info(f"✅ File size check completed: {result.files_checked} files")
        
        return result
    
    def check_sensitive_data(self) -> SanityCheckResult:
        """Check for sensitive data patterns"""
        self.logger.info("🔍 Checking for sensitive data...")
        
        result = SanityCheckResult(
            check_name="Sensitive Data Check",
            passed=True
        )
        
        # Check export directory only (logs may contain sensitive data for debugging)
        export_dir = Path('export')
        if not export_dir.exists():
            result.warnings.append("Export directory does not exist")
            return result
        
        for file_path in export_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.json', '.txt', '.log']:
                result.files_checked += 1
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for sensitive patterns
                    for pattern in self.sensitive_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            error_msg = f"Potential sensitive data found in {file_path}: {len(matches)} matches for pattern"
                            result.errors.append(error_msg)
                            result.errors_found += len(matches)
                            self.logger.error(f"❌ {error_msg}")
                    
                    self.logger.debug(f"✅ Sensitive data check passed: {file_path}")
                    
                except Exception as e:
                    warning_msg = f"Could not scan {file_path}: {e}"
                    result.warnings.append(warning_msg)
                    self.logger.warning(f"⚠️ {warning_msg}")
        
        if result.errors_found > 0:
            result.passed = False
            result.details = f"Found {result.errors_found} potential sensitive data items"
        else:
            result.details = f"No sensitive data detected in {result.files_checked} files"
            self.logger.info(f"✅ Sensitive data check passed: {result.files_checked} files")
        
        return result
    
    def check_version_tags(self) -> SanityCheckResult:
        """Check that each export file has the current system_version"""
        self.logger.info("🔍 Checking version tags...")
        
        result = SanityCheckResult(
            check_name="Version Tag Check",
            passed=True
        )
        
        export_dir = Path('export')
        if not export_dir.exists():
            result.errors.append("Export directory does not exist")
            result.errors_found += 1
            result.passed = False
            return result
        
        json_files = list(export_dir.glob('*.json'))
        
        for json_file in json_files:
            result.files_checked += 1
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                version_found = False
                version_value = None
                
                # Check for version fields (including nested in metadata)
                if isinstance(data, dict):
                    version_fields = ['export_version', 'system_version', 'version']
                    
                    # Check top-level fields first
                    for field in version_fields:
                        if field in data:
                            version_found = True
                            version_value = data[field]
                            break
                    
                    # If not found, check in metadata section
                    if not version_found and 'metadata' in data and isinstance(data['metadata'], dict):
                        for field in version_fields:
                            if field in data['metadata']:
                                version_found = True
                                version_value = data['metadata'][field]
                                break
                
                if not version_found:
                    error_msg = f"No version tag found in {json_file}"
                    result.errors.append(error_msg)
                    result.errors_found += 1
                    self.logger.error(f"❌ {error_msg}")
                elif version_value != self.expected_version:
                    warning_msg = f"Version mismatch in {json_file}: expected {self.expected_version}, found {version_value}"
                    result.warnings.append(warning_msg)
                    self.logger.warning(f"⚠️ {warning_msg}")
                else:
                    self.logger.debug(f"✅ Version tag validated: {json_file} (v{version_value})")
                
            except Exception as e:
                error_msg = f"Error reading {json_file} for version check: {e}"
                result.errors.append(error_msg)
                result.errors_found += 1
                self.logger.error(f"❌ {error_msg}")
        
        if result.errors_found > 0:
            result.passed = False
            result.details = f"Found {result.errors_found} version tag issues"
        else:
            result.details = f"All {result.files_checked} files have valid version tags"
            self.logger.info(f"✅ Version tag check passed: {result.files_checked} files")
        
        return result
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all sanity checks and return comprehensive results"""
        self.logger.info("🚀 STARTING COMPREHENSIVE SANITY CHECKS")
        self.logger.info("=" * 50)
        
        # Define all checks
        checks = [
            ("File Integrity", self.check_file_integrity),
            ("Schema Verification", self.check_schema_verification),
            ("Timestamp Validation", self.check_timestamp_validation),
            ("File Size Check", self.check_file_sizes),
            ("Sensitive Data Check", self.check_sensitive_data),
            ("Version Tag Check", self.check_version_tags)
        ]
        
        # Run all checks
        check_results = []
        total_files_checked = 0
        total_errors_found = 0
        total_warnings_found = 0
        
        for check_name, check_func in checks:
            self.logger.info(f"Running {check_name}...")
            try:
                result = check_func()
                check_results.append(result)
                total_files_checked += result.files_checked
                total_errors_found += result.errors_found
                total_warnings_found += len(result.warnings)
                
                if result.passed:
                    self.logger.info(f"✅ {check_name}: PASSED")
                else:
                    self.logger.error(f"❌ {check_name}: FAILED ({result.errors_found} errors)")
                    
            except Exception as e:
                error_result = SanityCheckResult(
                    check_name=check_name,
                    passed=False,
                    errors_found=1,
                    errors=[f"Check execution failed: {e}"]
                )
                check_results.append(error_result)
                total_errors_found += 1
                self.logger.error(f"💥 {check_name}: ERROR - {e}")
        
        # Calculate overall results
        duration = (datetime.now() - self.start_time).total_seconds()
        passed_checks = sum(1 for result in check_results if result.passed)
        total_checks = len(check_results)
        overall_passed = total_errors_found == 0
        
        # Create summary
        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_passed": overall_passed,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": total_checks - passed_checks,
            "total_files_checked": total_files_checked,
            "total_errors_found": total_errors_found,
            "total_warnings_found": total_warnings_found,
            "duration_seconds": duration,
            "check_results": [
                {
                    "check_name": result.check_name,
                    "passed": result.passed,
                    "files_checked": result.files_checked,
                    "errors_found": result.errors_found,
                    "warnings_count": len(result.warnings),
                    "details": result.details,
                    "errors": result.errors,
                    "warnings": result.warnings
                }
                for result in check_results
            ]
        }
        
        # Log final results
        self.logger.info("=" * 50)
        self.logger.info("🏁 SANITY CHECK RESULTS")
        self.logger.info("=" * 50)
        self.logger.info(f"Overall Status: {'✅ PASSED' if overall_passed else '❌ FAILED'}")
        self.logger.info(f"Checks: {passed_checks}/{total_checks} passed")
        self.logger.info(f"Files Checked: {total_files_checked}")
        self.logger.info(f"Errors Found: {total_errors_found}")
        self.logger.info(f"Warnings: {total_warnings_found}")
        self.logger.info(f"Duration: {duration:.2f} seconds")
        self.logger.info("=" * 50)
        
        # Log to Notion
        try:
            notion_success = self.notion_logger.log_sanity_check(
                success=overall_passed,
                files_checked=total_files_checked,
                errors_found=total_errors_found,
                warnings_found=total_warnings_found,
                duration=duration,
                details=f"Sanity check completed: {passed_checks}/{total_checks} checks passed"
            )
            if notion_success:
                self.logger.info("📝 Results logged to Notion")
        except Exception as e:
            self.logger.warning(f"Failed to log to Notion: {e}")
        
        return summary

def main():
    """Main entry point for sanity check"""
    try:
        print()
        print("🔍 ANGLES AI UNIVERSE™ PRE-BACKUP SANITY CHECK")
        print("=" * 55)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print()
        
        # Run sanity checks
        checker = SanityChecker()
        results = checker.run_all_checks()
        
        # Print console summary
        print()
        print("🏁 SANITY CHECK RESULTS:")
        print("=" * 30)
        
        if results['overall_passed']:
            print("✅ Status: PASSED")
            print("🟢 All checks passed - backup can proceed")
        else:
            print("❌ Status: FAILED")
            print("🔴 Issues found - backup should NOT proceed")
        
        print(f"📊 Summary: {results['passed_checks']}/{results['total_checks']} checks passed")
        print(f"📁 Files: {results['total_files_checked']} checked")
        print(f"🚨 Errors: {results['total_errors_found']} found")
        print(f"⚠️ Warnings: {results['total_warnings_found']} found")
        print(f"⏱️ Duration: {results['duration_seconds']:.1f}s")
        print(f"📝 Details: logs/sanity_check.log")
        print()
        
        # Exit with appropriate code
        sys.exit(0 if results['overall_passed'] else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Sanity check interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Sanity check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()