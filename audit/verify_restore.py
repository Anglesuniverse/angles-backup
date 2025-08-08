#!/usr/bin/env python3
"""
Angles AI Universe™ Restore Verification System
Dry-run restore validation and backup integrity verification

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import tempfile
import shutil
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

class RestoreVerificationSystem:
    """Comprehensive restore verification and backup validation"""
    
    def __init__(self):
        """Initialize restore verification system"""
        self.setup_logging()
        self.load_environment()
        
        # Verification configuration
        self.config = {
            'temp_dir_prefix': 'angles_restore_verify_',
            'required_export_files': ['decision_vault', 'ai_decision_log'],
            'schema_validation_rules': {
                'decision_vault': {
                    'required_columns': ['id', 'decision', 'date', 'type', 'active', 'created_at'],
                    'optional_columns': ['comment', 'updated_at', 'synced', 'synced_at']
                },
                'ai_decision_log': {
                    'required_columns': ['id', 'decision_text', 'decision_type', 'timestamp'],
                    'optional_columns': ['confidence', 'metadata']
                }
            }
        }
        
        # Initialize verification results
        self.verification_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'verification_id': f"restore_verify_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'overall_status': 'unknown',
            'repo_clone_status': 'unknown',
            'export_files_found': [],
            'schema_validation': {},
            'data_validation': {},
            'restore_readiness': 'unknown',
            'critical_issues': [],
            'warning_issues': [],
            'duration_seconds': 0,
            'temp_dir_used': None
        }
        
        self.logger.info("🔄 Angles AI Universe™ Restore Verification Initialized")
    
    def setup_logging(self):
        """Setup logging for restore verification"""
        os.makedirs("logs/audit", exist_ok=True)
        
        self.logger = logging.getLogger('restore_verification')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/audit/restore_check.log"
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
        """Load required environment variables"""
        self.env = {
            'supabase_url': os.getenv('SUPABASE_URL'),
            'supabase_key': os.getenv('SUPABASE_KEY'),
            'github_token': os.getenv('GITHUB_TOKEN'),
            'repo_url': os.getenv('REPO_URL', '')
        }
        
        self.logger.info("📋 Environment loaded for restore verification")
    
    def clone_backup_repository(self, temp_dir: str) -> Dict[str, Any]:
        """Clone latest backup repository to temp directory"""
        self.logger.info("🐙 Cloning backup repository...")
        
        clone_results = {
            'success': False,
            'repo_path': None,
            'clone_time_seconds': 0,
            'error_message': None,
            'commit_hash': None,
            'commit_date': None
        }
        
        if not self.env['repo_url']:
            clone_results['error_message'] = "Repository URL not configured"
            return clone_results
        
        start_time = datetime.now()
        
        try:
            repo_path = os.path.join(temp_dir, 'backup_repo')
            
            # Construct clone URL with token if available
            clone_url = self.env['repo_url']
            if self.env['github_token'] and 'github.com' in clone_url:
                # Insert token into URL
                clone_url = clone_url.replace('https://github.com/', f'https://{self.env["github_token"]}@github.com/')
            
            # Clone repository
            clone_cmd = ['git', 'clone', clone_url, repo_path]
            result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                clone_results['success'] = True
                clone_results['repo_path'] = repo_path
                
                # Get latest commit info
                commit_cmd = ['git', 'log', '-1', '--format=%H|%ad', '--date=iso']
                commit_result = subprocess.run(commit_cmd, cwd=repo_path, capture_output=True, text=True, timeout=30)
                
                if commit_result.returncode == 0:
                    commit_info = commit_result.stdout.strip().split('|')
                    if len(commit_info) >= 2:
                        clone_results['commit_hash'] = commit_info[0]
                        clone_results['commit_date'] = commit_info[1]
                
                self.logger.info(f"✅ Repository cloned successfully to {repo_path}")
            else:
                clone_results['error_message'] = f"Git clone failed: {result.stderr}"
                self.logger.error(f"❌ {clone_results['error_message']}")
        
        except subprocess.TimeoutExpired:
            clone_results['error_message'] = "Git clone timeout after 300 seconds"
            self.logger.error(f"❌ {clone_results['error_message']}")
        except Exception as e:
            clone_results['error_message'] = f"Clone failed: {str(e)}"
            self.logger.error(f"❌ {clone_results['error_message']}")
        
        clone_results['clone_time_seconds'] = (datetime.now() - start_time).total_seconds()
        return clone_results
    
    def discover_export_files(self, repo_path: str) -> Dict[str, Any]:
        """Discover and catalog export files in the repository"""
        self.logger.info("📁 Discovering export files...")
        
        discovery_results = {
            'export_dir_exists': False,
            'export_files': [],
            'latest_decision_export': None,
            'file_analysis': {},
            'total_files': 0,
            'total_size_mb': 0
        }
        
        export_dir = os.path.join(repo_path, 'export')
        
        if os.path.exists(export_dir):
            discovery_results['export_dir_exists'] = True
            
            try:
                # List all files in export directory
                for root, dirs, files in os.walk(export_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, export_dir)
                        
                        # Get file stats
                        stat_info = os.stat(file_path)
                        file_size_mb = stat_info.st_size / (1024 * 1024)
                        
                        file_info = {
                            'name': file,
                            'path': relative_path,
                            'size_mb': file_size_mb,
                            'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                        }
                        
                        discovery_results['export_files'].append(file_info)
                        discovery_results['total_files'] += 1
                        discovery_results['total_size_mb'] += file_size_mb
                
                # Find latest decision export
                decision_files = [f for f in discovery_results['export_files'] if 'decision' in f['name'].lower() and f['name'].endswith('.json')]
                if decision_files:
                    # Sort by modification time (most recent first)
                    decision_files.sort(key=lambda x: x['modified'], reverse=True)
                    discovery_results['latest_decision_export'] = decision_files[0]
                
                # Analyze file types
                for file_info in discovery_results['export_files']:
                    file_name = file_info['name']
                    
                    if 'decision_vault' in file_name:
                        discovery_results['file_analysis']['decision_vault'] = file_info
                    elif 'ai_decision_log' in file_name:
                        discovery_results['file_analysis']['ai_decision_log'] = file_info
                    elif 'decisions_' in file_name:
                        discovery_results['file_analysis']['combined_decisions'] = file_info
                
                self.logger.info(f"✅ Found {discovery_results['total_files']} export files ({discovery_results['total_size_mb']:.1f}MB)")
            
            except Exception as e:
                self.logger.error(f"❌ Error discovering export files: {str(e)}")
        
        else:
            self.logger.warning("⚠️ Export directory not found in repository")
        
        return discovery_results
    
    def validate_export_schema(self, repo_path: str, file_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate schema of export files against expected structure"""
        self.logger.info("🔍 Validating export file schemas...")
        
        schema_results = {
            'validation_passed': False,
            'files_validated': 0,
            'schema_errors': [],
            'table_schemas': {}
        }
        
        export_dir = os.path.join(repo_path, 'export')
        
        for table_name in self.config['required_export_files']:
            if table_name in file_analysis:
                file_info = file_analysis[table_name]
                file_path = os.path.join(export_dir, file_info['path'])
                
                try:
                    self.logger.info(f"🔍 Validating {table_name} schema...")
                    
                    # Load and validate JSON structure
                    with open(file_path, 'r') as f:
                        export_data = json.load(f)
                    
                    table_validation = self.validate_table_schema(table_name, export_data)
                    schema_results['table_schemas'][table_name] = table_validation
                    schema_results['files_validated'] += 1
                    
                    # Collect errors
                    if table_validation['errors']:
                        schema_results['schema_errors'].extend(table_validation['errors'])
                    
                    self.logger.info(f"✅ {table_name}: {table_validation['records_checked']} records, {len(table_validation['errors'])} errors")
                
                except Exception as e:
                    error_msg = f"Schema validation failed for {table_name}: {str(e)}"
                    schema_results['schema_errors'].append(error_msg)
                    self.logger.error(f"❌ {error_msg}")
            else:
                error_msg = f"Required export file missing: {table_name}"
                schema_results['schema_errors'].append(error_msg)
                self.logger.error(f"❌ {error_msg}")
        
        schema_results['validation_passed'] = len(schema_results['schema_errors']) == 0
        
        return schema_results
    
    def validate_table_schema(self, table_name: str, export_data: List[Dict]) -> Dict[str, Any]:
        """Validate individual table schema against expected structure"""
        validation_result = {
            'records_checked': len(export_data),
            'errors': [],
            'warnings': [],
            'column_analysis': {}
        }
        
        if not export_data:
            validation_result['errors'].append(f"{table_name}: No data to validate")
            return validation_result
        
        # Get schema rules for this table
        schema_rules = self.config['schema_validation_rules'].get(table_name, {})
        required_columns = schema_rules.get('required_columns', [])
        optional_columns = schema_rules.get('optional_columns', [])
        
        # Analyze first record for column structure
        first_record = export_data[0]
        present_columns = set(first_record.keys())
        required_columns_set = set(required_columns)
        
        # Check for missing required columns
        missing_required = required_columns_set - present_columns
        if missing_required:
            validation_result['errors'].append(f"{table_name}: Missing required columns: {list(missing_required)}")
        
        # Check for unexpected columns
        expected_columns = set(required_columns + optional_columns)
        unexpected_columns = present_columns - expected_columns
        if unexpected_columns:
            validation_result['warnings'].append(f"{table_name}: Unexpected columns: {list(unexpected_columns)}")
        
        # Validate data types and constraints for sample records
        sample_size = min(100, len(export_data))
        for i, record in enumerate(export_data[:sample_size]):
            record_errors = self.validate_record_constraints(table_name, record, i)
            validation_result['errors'].extend(record_errors)
        
        # Column analysis
        for column in present_columns:
            null_count = sum(1 for record in export_data[:sample_size] if record.get(column) is None)
            validation_result['column_analysis'][column] = {
                'null_count': null_count,
                'null_percentage': (null_count / sample_size) * 100 if sample_size > 0 else 0
            }
        
        return validation_result
    
    def validate_record_constraints(self, table_name: str, record: Dict, record_index: int) -> List[str]:
        """Validate individual record constraints"""
        errors = []
        
        # Common validations
        if not record.get('id'):
            errors.append(f"{table_name}[{record_index}]: Missing or empty id field")
        
        # Table-specific validations
        if table_name == 'decision_vault':
            errors.extend(self.validate_decision_vault_record(record, record_index))
        elif table_name == 'ai_decision_log':
            errors.extend(self.validate_ai_log_record(record, record_index))
        
        return errors
    
    def validate_decision_vault_record(self, record: Dict, index: int) -> List[str]:
        """Validate decision_vault record constraints"""
        errors = []
        
        # Validate date field
        if record.get('date'):
            try:
                datetime.fromisoformat(record['date'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                errors.append(f"decision_vault[{index}]: Invalid date format: {record.get('date')}")
        
        # Validate boolean fields
        for bool_field in ['active', 'synced']:
            value = record.get(bool_field)
            if value is not None and not isinstance(value, bool):
                errors.append(f"decision_vault[{index}]: Invalid boolean for {bool_field}: {value}")
        
        # Validate timestamps
        for ts_field in ['created_at', 'updated_at', 'synced_at']:
            value = record.get(ts_field)
            if value:
                try:
                    datetime.fromisoformat(value.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    errors.append(f"decision_vault[{index}]: Invalid timestamp for {ts_field}: {value}")
        
        return errors
    
    def validate_ai_log_record(self, record: Dict, index: int) -> List[str]:
        """Validate ai_decision_log record constraints"""
        errors = []
        
        # Validate decision_type enum
        valid_types = ['general', 'technical', 'business', 'architectural']
        decision_type = record.get('decision_type')
        if decision_type and decision_type not in valid_types:
            errors.append(f"ai_decision_log[{index}]: Invalid decision_type: {decision_type}")
        
        # Validate confidence range
        confidence = record.get('confidence')
        if confidence is not None:
            try:
                conf_float = float(confidence)
                if conf_float < 0 or conf_float > 1:
                    errors.append(f"ai_decision_log[{index}]: Confidence out of range [0,1]: {confidence}")
            except (ValueError, TypeError):
                errors.append(f"ai_decision_log[{index}]: Invalid confidence value: {confidence}")
        
        # Validate timestamp
        timestamp = record.get('timestamp')
        if timestamp:
            try:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                errors.append(f"ai_decision_log[{index}]: Invalid timestamp: {timestamp}")
        
        return errors
    
    def compare_with_live_supabase(self, repo_path: str, file_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Compare export data with live Supabase data"""
        self.logger.info("🔄 Comparing with live Supabase data...")
        
        comparison_results = {
            'comparison_performed': False,
            'tables_compared': 0,
            'discrepancies': [],
            'record_count_comparison': {},
            'sample_data_comparison': {}
        }
        
        if not self.env['supabase_url'] or not self.env['supabase_key']:
            comparison_results['discrepancies'].append("Supabase credentials not available for comparison")
            self.logger.warning("⚠️ Supabase comparison skipped - credentials not available")
            return comparison_results
        
        headers = {
            'apikey': self.env['supabase_key'],
            'Authorization': f"Bearer {self.env['supabase_key']}",
            'Content-Type': 'application/json'
        }
        
        export_dir = os.path.join(repo_path, 'export')
        
        for table_name in ['decision_vault', 'ai_decision_log']:
            if table_name in file_analysis:
                try:
                    # Load export data
                    file_info = file_analysis[table_name]
                    file_path = os.path.join(export_dir, file_info['path'])
                    
                    with open(file_path, 'r') as f:
                        export_data = json.load(f)
                    
                    export_count = len(export_data)
                    
                    # Get live Supabase count
                    url = f"{self.env['supabase_url']}/rest/v1/{table_name}"
                    response = requests.head(url, headers=headers, params={'select': 'count'}, timeout=30)
                    
                    if response.status_code == 200:
                        content_range = response.headers.get('content-range', '0-0/0')
                        live_count = int(content_range.split('/')[-1]) if '/' in content_range else 0
                        
                        comparison_results['record_count_comparison'][table_name] = {
                            'export_count': export_count,
                            'live_count': live_count,
                            'difference': abs(export_count - live_count)
                        }
                        
                        # Check for significant discrepancies
                        difference_pct = (abs(export_count - live_count) / max(live_count, 1)) * 100
                        if difference_pct > 10:  # More than 10% difference
                            comparison_results['discrepancies'].append(
                                f"{table_name}: Significant count difference - Export: {export_count}, Live: {live_count} ({difference_pct:.1f}% diff)"
                            )
                        
                        comparison_results['tables_compared'] += 1
                        self.logger.info(f"✅ {table_name}: Export {export_count}, Live {live_count} records")
                    
                    else:
                        comparison_results['discrepancies'].append(f"Cannot access live {table_name} table: HTTP {response.status_code}")
                
                except Exception as e:
                    comparison_results['discrepancies'].append(f"Comparison failed for {table_name}: {str(e)}")
                    self.logger.error(f"❌ Comparison failed for {table_name}: {str(e)}")
        
        comparison_results['comparison_performed'] = comparison_results['tables_compared'] > 0
        
        return comparison_results
    
    def run_verification(self) -> Dict[str, Any]:
        """Run complete restore verification process"""
        self.logger.info("🚀 Starting Restore Verification Process")
        self.logger.info("=" * 60)
        
        start_time = datetime.now()
        temp_dir = None
        
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix=self.config['temp_dir_prefix'])
            self.verification_results['temp_dir_used'] = temp_dir
            self.logger.info(f"📁 Created temp directory: {temp_dir}")
            
            # Step 1: Clone backup repository
            self.logger.info("1️⃣ Cloning backup repository...")
            clone_results = self.clone_backup_repository(temp_dir)
            self.verification_results['repo_clone_status'] = 'success' if clone_results['success'] else 'failed'
            
            if not clone_results['success']:
                self.verification_results['critical_issues'].append(f"Repository clone failed: {clone_results['error_message']}")
                self.verification_results['overall_status'] = 'failed'
                return self.verification_results
            
            repo_path = clone_results['repo_path']
            
            # Step 2: Discover export files
            self.logger.info("2️⃣ Discovering export files...")
            discovery_results = self.discover_export_files(repo_path)
            self.verification_results['export_files_found'] = discovery_results['export_files']
            
            if not discovery_results['export_dir_exists']:
                self.verification_results['critical_issues'].append("Export directory not found in backup repository")
            
            # Step 3: Validate export schemas
            self.logger.info("3️⃣ Validating export schemas...")
            schema_results = self.validate_export_schema(repo_path, discovery_results['file_analysis'])
            self.verification_results['schema_validation'] = schema_results
            
            if not schema_results['validation_passed']:
                for error in schema_results['schema_errors']:
                    self.verification_results['critical_issues'].append(f"Schema validation: {error}")
            
            # Step 4: Compare with live data
            self.logger.info("4️⃣ Comparing with live Supabase data...")
            comparison_results = self.compare_with_live_supabase(repo_path, discovery_results['file_analysis'])
            self.verification_results['data_validation'] = comparison_results
            
            for discrepancy in comparison_results['discrepancies']:
                self.verification_results['warning_issues'].append(f"Data comparison: {discrepancy}")
            
            # Step 5: Determine overall status
            self.determine_restore_readiness()
            
            # Calculate duration
            self.verification_results['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            
            # Generate reports
            self.generate_verification_reports()
            
            # Log summary
            self.log_verification_summary()
            
            return self.verification_results
            
        except Exception as e:
            self.verification_results['overall_status'] = 'failed'
            self.verification_results['critical_issues'].append(f"Verification system failure: {str(e)}")
            self.verification_results['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(f"💥 Restore verification failed: {str(e)}")
            return self.verification_results
            
        finally:
            # Cleanup temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    self.logger.info(f"🧹 Cleaned up temp directory: {temp_dir}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to cleanup temp directory: {str(e)}")
    
    def determine_restore_readiness(self):
        """Determine overall restore readiness status"""
        if self.verification_results['critical_issues']:
            self.verification_results['overall_status'] = 'failed'
            self.verification_results['restore_readiness'] = 'not_ready'
        elif self.verification_results['warning_issues']:
            self.verification_results['overall_status'] = 'warning'
            self.verification_results['restore_readiness'] = 'ready_with_warnings'
        else:
            self.verification_results['overall_status'] = 'passed'
            self.verification_results['restore_readiness'] = 'ready'
    
    def generate_verification_reports(self):
        """Generate verification reports"""
        try:
            # Ensure directories exist
            os.makedirs("logs/audit", exist_ok=True)
            os.makedirs("docs/audit", exist_ok=True)
            os.makedirs("export/audit", exist_ok=True)
            
            # Generate JSON report
            json_path = "logs/audit/restore_check.json"
            with open(json_path, 'w') as f:
                json.dump(self.verification_results, f, indent=2, default=str)
            
            # Generate Markdown report
            md_path = "docs/audit/restore_check.md"
            markdown_content = self.generate_markdown_report()
            with open(md_path, 'w') as f:
                f.write(markdown_content)
            
            # Generate sanitized export
            sanitized_results = self.sanitize_verification_results()
            export_path = "export/audit/restore_check.json"
            with open(export_path, 'w') as f:
                json.dump(sanitized_results, f, indent=2, default=str)
            
            self.logger.info(f"📊 Verification reports generated: {json_path}, {md_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate verification reports: {str(e)}")
    
    def generate_markdown_report(self) -> str:
        """Generate Markdown verification report"""
        status_emoji = {
            'passed': '🟢',
            'warning': '🟡',
            'failed': '🔴'
        }
        
        readiness_emoji = {
            'ready': '✅',
            'ready_with_warnings': '⚠️',
            'not_ready': '❌'
        }
        
        markdown = f"""# Restore Verification Report

**Generated:** {self.verification_results['timestamp']}  
**Verification ID:** {self.verification_results['verification_id']}  
**Overall Status:** {status_emoji.get(self.verification_results['overall_status'], '⚪')} {self.verification_results['overall_status'].upper()}  
**Restore Readiness:** {readiness_emoji.get(self.verification_results['restore_readiness'], '⚪')} {self.verification_results['restore_readiness'].upper()}  
**Duration:** {self.verification_results['duration_seconds']:.2f} seconds

## 📊 Summary

- **Repository Clone:** {self.verification_results['repo_clone_status']}
- **Export Files Found:** {len(self.verification_results['export_files_found'])}
- **Critical Issues:** {len(self.verification_results['critical_issues'])}
- **Warning Issues:** {len(self.verification_results['warning_issues'])}

## 🐙 Repository Verification

**Clone Status:** {self.verification_results['repo_clone_status']}

"""
        
        # Export files
        if self.verification_results['export_files_found']:
            markdown += "### Export Files Found\n\n"
            for file_info in self.verification_results['export_files_found']:
                markdown += f"- **{file_info['name']}** ({file_info['size_mb']:.1f}MB) - {file_info['modified']}\n"
            markdown += "\n"
        
        # Schema validation
        schema_validation = self.verification_results.get('schema_validation', {})
        if schema_validation:
            markdown += f"""## 🔍 Schema Validation

**Validation Passed:** {'✅' if schema_validation.get('validation_passed') else '❌'}  
**Files Validated:** {schema_validation.get('files_validated', 0)}  
**Schema Errors:** {len(schema_validation.get('schema_errors', []))}

"""
            
            # Table schemas
            table_schemas = schema_validation.get('table_schemas', {})
            for table_name, table_validation in table_schemas.items():
                markdown += f"### {table_name}\n"
                markdown += f"- **Records Checked:** {table_validation['records_checked']}\n"
                markdown += f"- **Errors:** {len(table_validation['errors'])}\n"
                markdown += f"- **Warnings:** {len(table_validation['warnings'])}\n"
                
                if table_validation['errors']:
                    markdown += "\n**Errors:**\n"
                    for error in table_validation['errors'][:5]:
                        markdown += f"- {error}\n"
                
                markdown += "\n"
        
        # Data validation
        data_validation = self.verification_results.get('data_validation', {})
        if data_validation.get('comparison_performed'):
            markdown += f"""## 🔄 Data Comparison

**Tables Compared:** {data_validation.get('tables_compared', 0)}  
**Discrepancies:** {len(data_validation.get('discrepancies', []))}

"""
            
            # Record counts
            record_counts = data_validation.get('record_count_comparison', {})
            if record_counts:
                markdown += "### Record Count Comparison\n\n"
                for table_name, counts in record_counts.items():
                    markdown += f"**{table_name}:**\n"
                    markdown += f"- Export: {counts['export_count']:,} records\n"
                    markdown += f"- Live: {counts['live_count']:,} records\n"
                    markdown += f"- Difference: {counts['difference']:,} records\n\n"
        
        # Critical issues
        if self.verification_results['critical_issues']:
            markdown += "## 🔴 Critical Issues\n\n"
            for issue in self.verification_results['critical_issues']:
                markdown += f"- {issue}\n"
            markdown += "\n"
        
        # Warning issues
        if self.verification_results['warning_issues']:
            markdown += "## 🟡 Warning Issues\n\n"
            for issue in self.verification_results['warning_issues']:
                markdown += f"- {issue}\n"
            markdown += "\n"
        
        # Recommendations
        markdown += "## 📋 Recommendations\n\n"
        
        if self.verification_results['restore_readiness'] == 'ready':
            markdown += "✅ **Backup is ready for restore operation**\n"
            markdown += "- All validations passed\n"
            markdown += "- No critical issues detected\n"
            markdown += "- Restore can proceed safely\n"
        elif self.verification_results['restore_readiness'] == 'ready_with_warnings':
            markdown += "⚠️ **Backup is ready but has warnings**\n"
            markdown += "- Address warning issues before restore\n"
            markdown += "- Monitor restore process carefully\n"
            markdown += "- Verify data integrity after restore\n"
        else:
            markdown += "❌ **Backup is NOT ready for restore**\n"
            markdown += "- **CRITICAL:** Address all critical issues immediately\n"
            markdown += "- Do not attempt restore until issues are resolved\n"
            markdown += "- Check backup process and repository integrity\n"
        
        markdown += """
### Next Steps
1. Review all findings in detail
2. Address critical issues immediately
3. Monitor backup process for consistency
4. Re-run verification after fixes
5. Test restore in non-production environment

---
*Generated by Angles AI Universe™ Restore Verification System*
"""
        
        return markdown
    
    def sanitize_verification_results(self) -> Dict[str, Any]:
        """Create sanitized version for export"""
        sanitized = self.verification_results.copy()
        
        # Remove sensitive paths
        if 'temp_dir_used' in sanitized:
            del sanitized['temp_dir_used']
        
        # Sanitize file paths in export files
        if 'export_files_found' in sanitized:
            for file_info in sanitized['export_files_found']:
                if 'path' in file_info:
                    file_info['path'] = os.path.basename(file_info['path'])
        
        return sanitized
    
    def log_verification_summary(self):
        """Log verification summary"""
        self.logger.info("=" * 60)
        self.logger.info("🎉 Restore Verification Complete")
        self.logger.info(f"   Verification ID: {self.verification_results['verification_id']}")
        self.logger.info(f"   Overall Status: {self.verification_results['overall_status'].upper()}")
        self.logger.info(f"   Restore Readiness: {self.verification_results['restore_readiness'].upper()}")
        self.logger.info(f"   Duration: {self.verification_results['duration_seconds']:.2f} seconds")
        self.logger.info(f"   Export Files: {len(self.verification_results['export_files_found'])}")
        self.logger.info(f"   Critical Issues: {len(self.verification_results['critical_issues'])}")
        self.logger.info(f"   Warning Issues: {len(self.verification_results['warning_issues'])}")

def main():
    """Main entry point for restore verification"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Restore Verification System')
    parser.add_argument('--verify', action='store_true', help='Run restore verification')
    parser.add_argument('--report', action='store_true', help='Show latest verification report')
    parser.add_argument('--status', action='store_true', help='Show verification system status')
    
    args = parser.parse_args()
    
    try:
        verification_system = RestoreVerificationSystem()
        
        if args.verify or not any([args.report, args.status]):
            # Run verification
            results = verification_system.run_verification()
            
            print(f"\n🔄 Restore Verification Results:")
            print(f"  Verification ID: {results['verification_id']}")
            print(f"  Overall Status: {results['overall_status']}")
            print(f"  Restore Readiness: {results['restore_readiness']}")
            print(f"  Duration: {results['duration_seconds']:.2f}s")
            print(f"  Export Files: {len(results['export_files_found'])}")
            print(f"  Critical Issues: {len(results['critical_issues'])}")
            
            # Exit with appropriate code
            if results['overall_status'] == 'failed':
                sys.exit(2)
            elif results['overall_status'] == 'warning':
                sys.exit(1)
            else:
                sys.exit(0)
        
        elif args.report:
            # Show latest report
            try:
                with open("logs/audit/restore_check.json", 'r') as f:
                    report = json.load(f)
                
                print(f"\n📊 Latest Restore Verification Report:")
                print(f"  Verification ID: {report['verification_id']}")
                print(f"  Status: {report['overall_status']}")
                print(f"  Readiness: {report['restore_readiness']}")
                print(f"  Timestamp: {report['timestamp']}")
                print(f"  Critical Issues: {len(report['critical_issues'])}")
                
            except FileNotFoundError:
                print("\n📊 No verification report found. Run verification first.")
        
        elif args.status:
            print(f"\n🔄 Restore Verification System Status:")
            print(f"  System: Initialized")
            print(f"  Repository: {'Configured' if verification_system.env['repo_url'] else 'Not configured'}")
            print(f"  Supabase: {'Connected' if verification_system.env['supabase_url'] else 'Not configured'}")
    
    except KeyboardInterrupt:
        print("\n🛑 Restore verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Restore verification failed: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()