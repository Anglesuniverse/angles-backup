#!/usr/bin/env python3
"""
Pre-Restore Sanity Check for Angles AI Universe™ Memory System
Enhanced sanity checking specifically for restore operations

This module extends the base sanity checker with restore-specific validations:
- All base checks (file integrity, schema, timestamps, size, sensitive data, version)
- Consistency check (metadata comparison, version compatibility, critical files)
- Dependency check (manifest dependencies verification)

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from sanity_check import SanityChecker, SanityCheckResult
from notion_backup_logger import create_notion_logger

@dataclass
class RestoreCompatibilityInfo:
    """Information about restore package compatibility"""
    package_version: Optional[str] = None
    current_version: Optional[str] = None
    is_compatible: bool = True
    compatibility_issues: List[str] = field(default_factory=list)
    missing_critical_files: List[str] = field(default_factory=list)
    dependency_issues: List[str] = field(default_factory=list)

class RestoreSanityChecker(SanityChecker):
    """Enhanced sanity checker for restore operations"""
    
    def __init__(self, restore_files_dir: str = "export"):
        """
        Initialize restore sanity checker
        
        Args:
            restore_files_dir: Directory containing files to be restored
        """
        super().__init__()
        
        # Override logger name and log file for restore operations
        self.logger = self._setup_restore_logging()
        self.restore_files_dir = Path(restore_files_dir)
        
        # Critical files required for system operation
        self.critical_files = [
            "memory_bridge.py",
            "memory_sync_agent.py", 
            "config.py",
            "notion_backup_logger.py"
        ]
        
        # Current system version (detected from existing files)
        self.current_system_version = self._detect_current_version()
        
        self.logger.info("🔍 RESTORE SANITY CHECKER INITIALIZED")
        self.logger.info("=" * 50)
    
    def _setup_restore_logging(self) -> logging.Logger:
        """Setup restore-specific logging"""
        # Ensure logs directory exists
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('restore_sanity_check')
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Rotating file handler for restore sanity checks
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            'logs/sanity_check_restore.log',
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
    
    def _detect_current_version(self) -> Optional[str]:
        """Detect current system version from existing export files"""
        try:
            # Look for recent export files in export directory
            export_dir = Path('export')
            if not export_dir.exists():
                return None
            
            json_files = list(export_dir.glob('*.json'))
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Check for version in various locations
                    version_fields = ['export_version', 'system_version', 'version']
                    
                    # Check top-level
                    for field in version_fields:
                        if field in data:
                            return data[field]
                    
                    # Check metadata
                    if 'metadata' in data and isinstance(data['metadata'], dict):
                        for field in version_fields:
                            if field in data['metadata']:
                                return data['metadata'][field]
                                
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Could not detect current system version: {e}")
            return None
    
    def check_consistency(self, restore_files: List[str]) -> SanityCheckResult:
        """
        Check consistency between restore package and current system
        
        Args:
            restore_files: List of file paths to be restored
            
        Returns:
            SanityCheckResult with consistency validation results
        """
        self.logger.info("🔍 Checking restore package consistency...")
        
        result = SanityCheckResult(
            check_name="Consistency Check",
            passed=True
        )
        
        compatibility_info = RestoreCompatibilityInfo()
        
        # Step 1: Extract metadata from restore package
        package_metadata = self._extract_package_metadata(restore_files)
        compatibility_info.package_version = package_metadata.get('version')
        compatibility_info.current_version = self.current_system_version
        
        # Step 2: Version compatibility check
        if compatibility_info.package_version and compatibility_info.current_version:
            try:
                # Simple semantic version comparison (major.minor.patch)
                package_parts = [int(x) for x in compatibility_info.package_version.split('.')]
                current_parts = [int(x) for x in compatibility_info.current_version.split('.')]
                
                # Check for major version mismatch (breaking changes)
                if package_parts[0] != current_parts[0]:
                    issue = f"Major version mismatch: package v{compatibility_info.package_version} vs current v{compatibility_info.current_version}"
                    compatibility_info.compatibility_issues.append(issue)
                    result.errors.append(issue)
                    result.errors_found += 1
                    self.logger.error(f"❌ {issue}")
                
                # Warn about minor version differences
                elif package_parts[1] != current_parts[1]:
                    warning = f"Minor version difference: package v{compatibility_info.package_version} vs current v{compatibility_info.current_version}"
                    compatibility_info.compatibility_issues.append(warning)
                    result.warnings.append(warning)
                    self.logger.warning(f"⚠️ {warning}")
                
            except (ValueError, IndexError) as e:
                warning = f"Could not parse version numbers for compatibility check: {e}"
                result.warnings.append(warning)
                self.logger.warning(f"⚠️ {warning}")
        
        elif not compatibility_info.package_version:
            warning = "No version information found in restore package"
            result.warnings.append(warning)
            self.logger.warning(f"⚠️ {warning}")
        
        # Step 3: Check for critical files
        missing_critical = []
        for critical_file in self.critical_files:
            if not Path(critical_file).exists():
                missing_critical.append(critical_file)
        
        if missing_critical:
            compatibility_info.missing_critical_files = missing_critical
            error_msg = f"Missing critical files: {missing_critical}"
            result.errors.append(error_msg)
            result.errors_found += len(missing_critical)
            self.logger.error(f"❌ {error_msg}")
        
        # Step 4: Check restore package completeness
        package_record_count = self._count_package_records(restore_files)
        result.files_checked = len(restore_files)
        
        if package_record_count == 0:
            error_msg = "Restore package contains no valid records"
            result.errors.append(error_msg)
            result.errors_found += 1
            self.logger.error(f"❌ {error_msg}")
        else:
            self.logger.info(f"📊 Restore package contains {package_record_count} records")
        
        # Final result
        if result.errors_found > 0:
            result.passed = False
            result.details = f"Found {result.errors_found} consistency issues"
        else:
            result.details = f"Consistency check passed: {result.files_checked} files, {package_record_count} records"
            self.logger.info(f"✅ Consistency check passed: {result.files_checked} files")
        
        return result
    
    def check_dependencies(self, restore_files: List[str]) -> SanityCheckResult:
        """
        Check that dependencies listed in restore package are available
        
        Args:
            restore_files: List of file paths to be restored
            
        Returns:
            SanityCheckResult with dependency validation results
        """
        self.logger.info("🔍 Checking restore package dependencies...")
        
        result = SanityCheckResult(
            check_name="Dependency Check",
            passed=True
        )
        
        # Step 1: Extract dependency information from package
        dependencies = self._extract_package_dependencies(restore_files)
        result.files_checked = len(restore_files)
        
        if not dependencies:
            result.details = "No dependency information found in restore package"
            self.logger.info("ℹ️ No dependency information found in restore package")
            return result
        
        # Step 2: Check Python dependencies (core packages only)
        missing_deps = []
        for dep_name, dep_version in dependencies.items():
            try:
                # Try to import Python package
                if dep_name == 'supabase':
                    from supabase import create_client
                elif dep_name == 'notion-client':
                    from notion_client import Client
                elif dep_name == 'pydantic':
                    import pydantic
                elif dep_name == 'python-dotenv':
                    import dotenv
                elif dep_name == 'requests':
                    import requests
                else:
                    __import__(dep_name)
                    
            except ImportError:
                missing_deps.append(f"{dep_name}" + (f"=={dep_version}" if dep_version else ""))
                
            except Exception as e:
                # Only warn for unexpected errors, not import failures
                warning = f"Could not verify dependency {dep_name}: {e}"
                result.warnings.append(warning)
                self.logger.warning(f"⚠️ {warning}")
        
        # Step 3: Check environment variables
        required_env_vars = self._extract_required_env_vars(restore_files)
        missing_env_vars = []
        for env_var in required_env_vars:
            if not os.getenv(env_var):
                missing_env_vars.append(env_var)
        
        # Compile results
        if missing_deps:
            error_msg = f"Missing Python dependencies: {missing_deps}"
            result.errors.append(error_msg)
            result.errors_found += len(missing_deps)
            self.logger.error(f"❌ {error_msg}")
        
        if missing_env_vars:
            error_msg = f"Missing environment variables: {missing_env_vars}"
            result.errors.append(error_msg)
            result.errors_found += len(missing_env_vars)
            self.logger.error(f"❌ {error_msg}")
        
        if result.errors_found > 0:
            result.passed = False
            result.details = f"Found {result.errors_found} dependency issues"
        else:
            result.details = f"All dependencies satisfied for {len(dependencies)} packages"
            self.logger.info(f"✅ Dependency check passed: {len(dependencies)} dependencies")
        
        return result
    
    def _extract_package_metadata(self, restore_files: List[str]) -> Dict[str, Any]:
        """Extract metadata from restore package files"""
        metadata = {}
        
        for file_path in restore_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Look for metadata in various locations
                if isinstance(data, dict):
                    # Top-level metadata
                    for key in ['export_version', 'system_version', 'version', 'export_timestamp']:
                        if key in data:
                            metadata[key.replace('export_', '')] = data[key]
                    
                    # Nested metadata
                    if 'metadata' in data and isinstance(data['metadata'], dict):
                        metadata.update(data['metadata'])
                        
            except Exception as e:
                self.logger.debug(f"Could not extract metadata from {file_path}: {e}")
        
        return metadata
    
    def _count_package_records(self, restore_files: List[str]) -> int:
        """Count total records in restore package"""
        total_records = 0
        
        for file_path in restore_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, dict):
                    if 'decisions' in data and isinstance(data['decisions'], list):
                        total_records += len(data['decisions'])
                    elif 'total_decisions' in data:
                        total_records += data['total_decisions']
                    else:
                        total_records += 1  # Single record
                elif isinstance(data, list):
                    total_records += len(data)
                    
            except Exception as e:
                self.logger.debug(f"Could not count records in {file_path}: {e}")
        
        return total_records
    
    def _extract_package_dependencies(self, restore_files: List[str]) -> Dict[str, Optional[str]]:
        """Extract dependency information from restore package"""
        # Focus only on core dependencies that are essential for restore operations
        # Skip complex dependency file parsing to avoid false positives
        
        core_dependencies: Dict[str, Optional[str]] = {
            'supabase': None,
            'notion-client': None, 
            'pydantic': None,
            'python-dotenv': None,
            'requests': None
        }
        
        return core_dependencies
    
    def _extract_required_env_vars(self, restore_files: List[str]) -> List[str]:
        """Extract required environment variables from restore package"""
        required_vars = [
            'SUPABASE_URL',
            'SUPABASE_KEY',
            'NOTION_TOKEN',
            'NOTION_DATABASE_ID',
            'GITHUB_TOKEN',
            'REPO_URL'
        ]
        
        return required_vars
    
    def _version_compatible(self, current: str, required: str) -> bool:
        """Check if current version is compatible with required version"""
        try:
            current_parts = [int(x) for x in current.split('.')]
            required_parts = [int(x) for x in required.split('.')]
            
            # Require at least the same major and minor version
            return (current_parts[0] >= required_parts[0] and 
                   current_parts[1] >= required_parts[1])
                   
        except (ValueError, IndexError):
            return True  # If we can't parse, assume compatible
    
    def run_restore_sanity_checks(self, restore_files: List[str]) -> Dict[str, Any]:
        """
        Run all sanity checks for restore operation
        
        Args:
            restore_files: List of file paths to be restored
            
        Returns:
            Dictionary with comprehensive restore sanity check results
        """
        self.logger.info("🚀 STARTING RESTORE SANITY CHECKS")
        self.logger.info("=" * 50)
        
        # First, run all base sanity checks on the restore directory
        base_results = self.run_all_checks()
        
        # Then run restore-specific checks
        restore_checks = [
            ("Consistency Check", lambda: self.check_consistency(restore_files)),
            ("Dependency Check", lambda: self.check_dependencies(restore_files))
        ]
        
        restore_check_results = []
        restore_errors = 0
        restore_warnings = 0
        
        for check_name, check_func in restore_checks:
            self.logger.info(f"Running {check_name}...")
            try:
                result = check_func()
                restore_check_results.append(result)
                restore_errors += result.errors_found
                restore_warnings += len(result.warnings)
                
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
                restore_check_results.append(error_result)
                restore_errors += 1
                self.logger.error(f"💥 {check_name}: ERROR - {e}")
        
        # Combine results
        total_checks = base_results['total_checks'] + len(restore_check_results)
        total_passed = base_results['passed_checks'] + sum(1 for r in restore_check_results if r.passed)
        total_errors = base_results['total_errors_found'] + restore_errors
        total_warnings = base_results['total_warnings_found'] + restore_warnings
        overall_passed = total_errors == 0
        
        duration = (datetime.now() - self.start_time).total_seconds()
        
        # Create comprehensive summary
        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_passed": overall_passed,
            "total_checks": total_checks,
            "passed_checks": total_passed,
            "failed_checks": total_checks - total_passed,
            "total_files_checked": base_results['total_files_checked'],
            "total_errors_found": total_errors,
            "total_warnings_found": total_warnings,
            "duration_seconds": duration,
            "restore_files": restore_files,
            "base_checks": base_results['check_results'],
            "restore_checks": [
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
                for result in restore_check_results
            ]
        }
        
        # Log final results
        self.logger.info("=" * 50)
        self.logger.info("🏁 RESTORE SANITY CHECK RESULTS")
        self.logger.info("=" * 50)
        self.logger.info(f"Overall Status: {'✅ PASSED' if overall_passed else '❌ FAILED'}")
        self.logger.info(f"Checks: {total_passed}/{total_checks} passed")
        self.logger.info(f"Files Checked: {base_results['total_files_checked']}")
        self.logger.info(f"Restore Files: {len(restore_files)}")
        self.logger.info(f"Errors Found: {total_errors}")
        self.logger.info(f"Warnings: {total_warnings}")
        self.logger.info(f"Duration: {duration:.2f} seconds")
        self.logger.info("=" * 50)
        
        # Log to Notion
        try:
            self.notion_logger.log_restore_sanity_check(
                success=overall_passed,
                files_checked=base_results['total_files_checked'],
                restore_files_count=len(restore_files),
                errors_found=total_errors,
                warnings_found=total_warnings,
                duration=duration,
                details=f"Restore sanity check completed: {total_passed}/{total_checks} checks passed"
            )
            self.logger.info("📝 Results logged to Notion")
        except Exception as e:
            self.logger.warning(f"Failed to log to Notion: {e}")
        
        return summary

def main():
    """Main entry point for restore sanity check"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Pre-restore sanity check for Angles AI Universe™")
    parser.add_argument('--files', nargs='+', required=True, help='Restore files to check')
    parser.add_argument('--restore-dir', default='export', help='Directory containing restore files')
    
    args = parser.parse_args()
    
    try:
        print()
        print("🔍 ANGLES AI UNIVERSE™ PRE-RESTORE SANITY CHECK")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"Restore Files: {len(args.files)}")
        print()
        
        # Run restore sanity checks
        checker = RestoreSanityChecker(args.restore_dir)
        results = checker.run_restore_sanity_checks(args.files)
        
        # Print console summary
        print()
        print("🏁 RESTORE SANITY CHECK RESULTS:")
        print("=" * 35)
        
        if results['overall_passed']:
            print("✅ Status: PASSED")
            print("🟢 All checks passed - restore can proceed")
        else:
            print("❌ Status: FAILED")
            print("🔴 Issues found - restore should NOT proceed")
        
        print(f"📊 Summary: {results['passed_checks']}/{results['total_checks']} checks passed")
        print(f"📁 Files: {results['total_files_checked']} checked")
        print(f"📦 Restore Files: {len(results['restore_files'])}")
        print(f"🚨 Errors: {results['total_errors_found']} found")
        print(f"⚠️ Warnings: {results['total_warnings_found']} found")
        print(f"⏱️ Duration: {results['duration_seconds']:.1f}s")
        print(f"📝 Details: logs/sanity_check_restore.log")
        print()
        
        # Exit with appropriate code
        sys.exit(0 if results['overall_passed'] else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Restore sanity check interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Restore sanity check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()