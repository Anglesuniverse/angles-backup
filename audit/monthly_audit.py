#!/usr/bin/env python3
"""
Angles AI Universe™ Monthly Deep Audit System
Comprehensive data integrity, consistency, and backup verification

Author: Angles AI Universe™ Backend Team  
Version: 1.0.0
"""

import os
import sys
import json
import time
import requests
import logging
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import our existing components
try:
    from alerts.notify import AlertManager
    from git_helpers import GitHelper
except ImportError:
    AlertManager = None
    GitHelper = None

class MonthlyAuditSystem:
    """Comprehensive monthly deep audit system"""
    
    def __init__(self):
        """Initialize monthly audit system"""
        self.setup_logging()
        self.load_environment()
        self.alert_manager = AlertManager() if AlertManager else None
        self.git_helper = GitHelper() if GitHelper else None
        
        # Audit configuration
        self.config = {
            'slow_query_threshold_ms': 200,
            'max_null_percentage': 5.0,
            'critical_findings_threshold': 3,
            'temp_table_prefix': 'audit_temp_',
            'required_tables': ['decision_vault', 'ai_decision_log'],
            'required_indexes': ['idx_decision_date', 'idx_ai_log_timestamp']
        }
        
        # Initialize audit results
        self.audit_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'month_year': datetime.now().strftime('%Y%m'),
            'audit_id': f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'overall_status': 'unknown',
            'critical_findings': [],
            'warning_findings': [],
            'info_findings': [],
            'performance_metrics': {},
            'data_integrity': {},
            'sync_consistency': {},
            'backup_verification': {},
            'duration_seconds': 0,
            'tables_checked': 0,
            'total_records': 0
        }
        
        self.logger.info("🔍 Angles AI Universe™ Monthly Deep Audit Initialized")
    
    def setup_logging(self):
        """Setup logging for monthly audit"""
        os.makedirs("logs/audit", exist_ok=True)
        
        self.logger = logging.getLogger('monthly_audit')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/audit/monthly_audit.log"
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
            'notion_token': os.getenv('NOTION_TOKEN') or os.getenv('NOTION_API_KEY'),
            'notion_database_id': os.getenv('NOTION_DATABASE_ID'),
            'github_token': os.getenv('GITHUB_TOKEN'),
            'repo_url': os.getenv('REPO_URL', '')
        }
        
        # Validate required credentials
        if not self.env['supabase_url'] or not self.env['supabase_key']:
            raise ValueError("Missing required Supabase credentials for audit")
        
        self.logger.info("📋 Environment loaded for monthly audit")
    
    def get_supabase_headers(self) -> Dict[str, str]:
        """Get standard Supabase headers"""
        return {
            'apikey': self.env['supabase_key'],
            'Authorization': f"Bearer {self.env['supabase_key']}",
            'Content-Type': 'application/json'
        }
    
    def validate_supabase_tables(self) -> Dict[str, Any]:
        """Validate Supabase tables for data integrity"""
        self.logger.info("🗃️ Validating Supabase tables...")
        
        validation_results = {
            'tables_validated': 0,
            'total_rows': 0,
            'integrity_issues': [],
            'performance_issues': [],
            'null_analysis': {},
            'enum_validation': {},
            'orphaned_refs': []
        }
        
        headers = self.get_supabase_headers()
        
        for table_name in self.config['required_tables']:
            try:
                self.logger.info(f"🔍 Analyzing table: {table_name}")
                table_results = self._analyze_table(table_name, headers)
                
                validation_results['tables_validated'] += 1
                validation_results['total_rows'] += table_results['row_count']
                validation_results['null_analysis'][table_name] = table_results['null_analysis']
                
                # Check for integrity issues
                if table_results['critical_issues']:
                    validation_results['integrity_issues'].extend(table_results['critical_issues'])
                
                # Check performance
                if table_results['slow_queries']:
                    validation_results['performance_issues'].extend(table_results['slow_queries'])
                
                self.audit_results['tables_checked'] += 1
                
            except Exception as e:
                error_msg = f"Failed to analyze table {table_name}: {str(e)}"
                validation_results['integrity_issues'].append(error_msg)
                self.logger.error(f"❌ {error_msg}")
        
        # Update totals
        self.audit_results['total_records'] = validation_results['total_rows']
        
        self.logger.info(f"✅ Supabase validation complete: {validation_results['tables_validated']} tables, {validation_results['total_rows']} total rows")
        return validation_results
    
    def _analyze_table(self, table_name: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Analyze individual table for integrity issues"""
        table_results = {
            'row_count': 0,
            'null_analysis': {},
            'critical_issues': [],
            'slow_queries': [],
            'enum_issues': []
        }
        
        try:
            # Get row count
            url = f"{self.env['supabase_url']}/rest/v1/{table_name}"
            params = {'select': 'count', 'head': 'true'}
            
            start_time = time.time()
            response = requests.head(url, headers=headers, params=params, timeout=30)
            query_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Extract count from content-range header
                content_range = response.headers.get('content-range', '0-0/0')
                total_count = int(content_range.split('/')[-1]) if '/' in content_range else 0
                table_results['row_count'] = total_count
                
                # Check query performance
                if query_time > self.config['slow_query_threshold_ms']:
                    slow_query = f"Count query on {table_name} took {query_time:.1f}ms (threshold: {self.config['slow_query_threshold_ms']}ms)"
                    table_results['slow_queries'].append(slow_query)
                
                # Sample data for null analysis (get first 100 rows)
                sample_params = {'select': '*', 'limit': '100'}
                sample_response = requests.get(url, headers=headers, params=sample_params, timeout=30)
                
                if sample_response.status_code == 200:
                    sample_data = sample_response.json()
                    
                    if sample_data:
                        # Analyze null percentages
                        null_analysis = self._analyze_nulls(sample_data, table_name)
                        table_results['null_analysis'] = null_analysis
                        
                        # Check for critical null issues
                        for column, null_pct in null_analysis.items():
                            if null_pct > self.config['max_null_percentage']:
                                critical_issue = f"High null percentage in {table_name}.{column}: {null_pct:.1f}%"
                                table_results['critical_issues'].append(critical_issue)
                        
                        # Validate specific table constraints
                        if table_name == 'decision_vault':
                            constraint_issues = self._validate_decision_vault_constraints(sample_data)
                            table_results['critical_issues'].extend(constraint_issues)
                        elif table_name == 'ai_decision_log':
                            constraint_issues = self._validate_ai_log_constraints(sample_data)
                            table_results['critical_issues'].extend(constraint_issues)
            
            else:
                table_results['critical_issues'].append(f"Cannot access table {table_name}: HTTP {response.status_code}")
        
        except Exception as e:
            table_results['critical_issues'].append(f"Table analysis failed for {table_name}: {str(e)}")
        
        return table_results
    
    def _analyze_nulls(self, data: List[Dict], table_name: str) -> Dict[str, float]:
        """Analyze null percentages in sample data"""
        if not data:
            return {}
        
        null_counts = {}
        total_rows = len(data)
        
        # Get all columns from first row
        columns = list(data[0].keys())
        
        for column in columns:
            null_count = sum(1 for row in data if row.get(column) is None)
            null_percentage = (null_count / total_rows) * 100
            null_counts[column] = null_percentage
        
        return null_counts
    
    def _validate_decision_vault_constraints(self, data: List[Dict]) -> List[str]:
        """Validate decision_vault specific constraints"""
        issues = []
        
        for row in data:
            # Check required fields
            if not row.get('id'):
                issues.append(f"decision_vault record missing required id")
            
            # Validate date format
            if row.get('date'):
                try:
                    datetime.fromisoformat(row['date'].replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    issues.append(f"Invalid date format in decision_vault: {row.get('date')}")
            
            # Validate boolean fields
            for bool_field in ['active', 'synced']:
                if row.get(bool_field) is not None and not isinstance(row[bool_field], bool):
                    issues.append(f"Invalid boolean value in decision_vault.{bool_field}: {row.get(bool_field)}")
        
        return issues
    
    def _validate_ai_log_constraints(self, data: List[Dict]) -> List[str]:
        """Validate ai_decision_log specific constraints"""
        issues = []
        
        valid_decision_types = ['general', 'technical', 'business', 'architectural']
        
        for row in data:
            # Check required fields
            if not row.get('id'):
                issues.append(f"ai_decision_log record missing required id")
            
            # Validate decision_type enum
            decision_type = row.get('decision_type')
            if decision_type and decision_type not in valid_decision_types:
                issues.append(f"Invalid decision_type in ai_decision_log: {decision_type}")
            
            # Validate confidence range
            confidence = row.get('confidence')
            if confidence is not None:
                try:
                    conf_float = float(confidence)
                    if conf_float < 0 or conf_float > 1:
                        issues.append(f"Confidence out of range [0,1] in ai_decision_log: {confidence}")
                except (ValueError, TypeError):
                    issues.append(f"Invalid confidence value in ai_decision_log: {confidence}")
        
        return issues
    
    def verify_notion_sync_consistency(self) -> Dict[str, Any]:
        """Verify Notion sync consistency"""
        self.logger.info("🔄 Verifying Notion sync consistency...")
        
        consistency_results = {
            'supabase_synced_count': 0,
            'notion_pages_found': 0,
            'sync_drift_count': 0,
            'missing_notion_pages': [],
            'orphaned_notion_pages': [],
            'sync_status': 'unknown'
        }
        
        if not self.env['notion_token'] or not self.env['notion_database_id']:
            consistency_results['sync_status'] = 'skipped_no_credentials'
            self.logger.warning("⚠️ Notion sync check skipped - credentials not available")
            return consistency_results
        
        try:
            # Get Supabase records marked as synced
            headers = self.get_supabase_headers()
            url = f"{self.env['supabase_url']}/rest/v1/decision_vault"
            params = {'select': 'id,decision,synced,synced_at', 'synced': 'eq.true'}
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                synced_decisions = response.json()
                consistency_results['supabase_synced_count'] = len(synced_decisions)
                
                # Check corresponding Notion pages
                notion_headers = {
                    'Authorization': f"Bearer {self.env['notion_token']}",
                    'Notion-Version': '2022-06-28',
                    'Content-Type': 'application/json'
                }
                
                # Query Notion database
                notion_url = f"https://api.notion.com/v1/databases/{self.env['notion_database_id']}/query"
                notion_response = requests.post(notion_url, headers=notion_headers, json={}, timeout=30)
                
                if notion_response.status_code == 200:
                    notion_data = notion_response.json()
                    notion_pages = notion_data.get('results', [])
                    consistency_results['notion_pages_found'] = len(notion_pages)
                    
                    # Build Notion pages lookup by decision text
                    notion_decisions = {}
                    for page in notion_pages:
                        try:
                            message_prop = page.get('properties', {}).get('Message', {})
                            if message_prop.get('rich_text'):
                                decision_text = message_prop['rich_text'][0]['text']['content']
                                notion_decisions[decision_text[:100]] = page  # Use first 100 chars as key
                        except (KeyError, IndexError):
                            continue
                    
                    # Check for missing Notion pages
                    for decision in synced_decisions:
                        decision_text = decision.get('decision', '')
                        decision_key = decision_text[:100] if decision_text else ''
                        
                        if decision_key and decision_key not in notion_decisions:
                            consistency_results['missing_notion_pages'].append({
                                'supabase_id': decision['id'],
                                'decision': decision_text[:50] + '...' if len(decision_text) > 50 else decision_text,
                                'synced_at': decision.get('synced_at')
                            })
                    
                    consistency_results['sync_drift_count'] = len(consistency_results['missing_notion_pages'])
                    
                    # Determine sync status
                    if consistency_results['sync_drift_count'] == 0:
                        consistency_results['sync_status'] = 'consistent'
                    elif consistency_results['sync_drift_count'] <= 3:
                        consistency_results['sync_status'] = 'minor_drift'
                    else:
                        consistency_results['sync_status'] = 'major_drift'
                
                else:
                    consistency_results['sync_status'] = 'notion_api_error'
                    self.logger.error(f"❌ Notion API error: HTTP {notion_response.status_code}")
            
            else:
                consistency_results['sync_status'] = 'supabase_error'
                self.logger.error(f"❌ Supabase API error: HTTP {response.status_code}")
        
        except Exception as e:
            consistency_results['sync_status'] = 'error'
            self.logger.error(f"❌ Notion sync consistency check failed: {str(e)}")
        
        self.logger.info(f"✅ Notion sync check complete: {consistency_results['sync_drift_count']} drift items")
        return consistency_results
    
    def verify_github_backup_state(self) -> Dict[str, Any]:
        """Verify GitHub backup state"""
        self.logger.info("🐙 Verifying GitHub backup state...")
        
        backup_results = {
            'repository_accessible': False,
            'latest_commit_date': None,
            'backup_files_found': [],
            'export_files_count': 0,
            'backup_freshness_hours': None,
            'backup_status': 'unknown'
        }
        
        if not self.env['github_token'] or not self.env['repo_url']:
            backup_results['backup_status'] = 'skipped_no_credentials'
            self.logger.warning("⚠️ GitHub backup check skipped - credentials not available")
            return backup_results
        
        try:
            # Parse repo info
            repo_parts = self.env['repo_url'].rstrip('/').split('/')
            if len(repo_parts) >= 2:
                repo_owner = repo_parts[-2]
                repo_name = repo_parts[-1].replace('.git', '')
            else:
                repo_owner = 'angles-ai'
                repo_name = 'angles-backup'
            
            # Check repository accessibility
            headers = {
                'Authorization': f"token {self.env['github_token']}",
                'Accept': 'application/vnd.github.v3+json'
            }
            
            repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
            response = requests.get(repo_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                repo_data = response.json()
                backup_results['repository_accessible'] = True
                
                # Get latest commit
                commits_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits"
                commits_response = requests.get(commits_url, headers=headers, params={'per_page': 1}, timeout=30)
                
                if commits_response.status_code == 200:
                    commits = commits_response.json()
                    if commits:
                        latest_commit = commits[0]
                        commit_date_str = latest_commit['commit']['author']['date']
                        commit_date = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00'))
                        backup_results['latest_commit_date'] = commit_date.isoformat()
                        
                        # Calculate backup freshness
                        hours_old = (datetime.now(timezone.utc) - commit_date).total_seconds() / 3600
                        backup_results['backup_freshness_hours'] = hours_old
                        
                        # Check for export files in latest commit
                        contents_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/export"
                        contents_response = requests.get(contents_url, headers=headers, timeout=30)
                        
                        if contents_response.status_code == 200:
                            contents = contents_response.json()
                            export_files = [item['name'] for item in contents if item['type'] == 'file']
                            backup_results['backup_files_found'] = export_files
                            backup_results['export_files_count'] = len(export_files)
                            
                            # Look for recent decision exports
                            recent_exports = [f for f in export_files if 'decisions_' in f and f.endswith('.json')]
                            
                            # Determine backup status
                            if hours_old <= 48 and recent_exports:  # Fresh backup with exports
                                backup_results['backup_status'] = 'healthy'
                            elif hours_old <= 168:  # Within a week
                                backup_results['backup_status'] = 'stale'
                            else:
                                backup_results['backup_status'] = 'outdated'
                        
                        else:
                            backup_results['backup_status'] = 'no_exports'
                    
                    else:
                        backup_results['backup_status'] = 'no_commits'
                
                else:
                    backup_results['backup_status'] = 'commits_error'
            
            else:
                backup_results['backup_status'] = 'repo_inaccessible'
                self.logger.error(f"❌ GitHub repository not accessible: HTTP {response.status_code}")
        
        except Exception as e:
            backup_results['backup_status'] = 'error'
            self.logger.error(f"❌ GitHub backup verification failed: {str(e)}")
        
        self.logger.info(f"✅ GitHub backup check complete: {backup_results['backup_status']}")
        return backup_results
    
    def run_comprehensive_audit(self) -> Dict[str, Any]:
        """Run complete monthly audit"""
        self.logger.info("🚀 Starting Comprehensive Monthly Deep Audit")
        self.logger.info("=" * 70)
        
        start_time = time.time()
        
        try:
            # Step 1: Validate Supabase tables
            self.logger.info("1️⃣ Validating Supabase data integrity...")
            self.audit_results['data_integrity'] = self.validate_supabase_tables()
            
            # Step 2: Verify Notion sync consistency
            self.logger.info("2️⃣ Verifying Notion sync consistency...")
            self.audit_results['sync_consistency'] = self.verify_notion_sync_consistency()
            
            # Step 3: Verify GitHub backup state
            self.logger.info("3️⃣ Verifying GitHub backup state...")
            self.audit_results['backup_verification'] = self.verify_github_backup_state()
            
            # Step 4: Analyze findings and determine status
            self.analyze_audit_findings()
            
            # Calculate duration
            self.audit_results['duration_seconds'] = time.time() - start_time
            
            # Step 5: Generate reports
            self.generate_audit_reports()
            
            # Step 6: Handle critical findings
            if len(self.audit_results['critical_findings']) >= self.config['critical_findings_threshold']:
                self.handle_critical_findings()
            
            # Log summary
            self.log_audit_summary()
            
            return self.audit_results
            
        except Exception as e:
            self.audit_results['overall_status'] = 'failed'
            self.audit_results['critical_findings'].append(f"Audit system failure: {str(e)}")
            self.audit_results['duration_seconds'] = time.time() - start_time
            
            self.logger.error(f"💥 Monthly audit failed: {str(e)}")
            
            # Generate failure report
            self.generate_audit_reports()
            
            return self.audit_results
    
    def analyze_audit_findings(self):
        """Analyze all audit findings and categorize them"""
        # Extract findings from each audit component
        
        # Data integrity findings
        integrity_issues = self.audit_results['data_integrity'].get('integrity_issues', [])
        performance_issues = self.audit_results['data_integrity'].get('performance_issues', [])
        
        for issue in integrity_issues:
            if any(keyword in issue.lower() for keyword in ['critical', 'missing', 'failed', 'cannot access']):
                self.audit_results['critical_findings'].append(f"Data Integrity: {issue}")
            else:
                self.audit_results['warning_findings'].append(f"Data Integrity: {issue}")
        
        for issue in performance_issues:
            self.audit_results['warning_findings'].append(f"Performance: {issue}")
        
        # Sync consistency findings
        sync_status = self.audit_results['sync_consistency'].get('sync_status')
        drift_count = self.audit_results['sync_consistency'].get('sync_drift_count', 0)
        
        if sync_status == 'major_drift':
            self.audit_results['critical_findings'].append(f"Notion Sync: Major drift detected ({drift_count} items)")
        elif sync_status == 'minor_drift':
            self.audit_results['warning_findings'].append(f"Notion Sync: Minor drift detected ({drift_count} items)")
        elif sync_status in ['error', 'supabase_error', 'notion_api_error']:
            self.audit_results['critical_findings'].append(f"Notion Sync: Verification failed ({sync_status})")
        
        # Backup verification findings
        backup_status = self.audit_results['backup_verification'].get('backup_status')
        backup_age = self.audit_results['backup_verification'].get('backup_freshness_hours', 0)
        
        if backup_status in ['outdated', 'no_exports', 'no_commits', 'repo_inaccessible']:
            self.audit_results['critical_findings'].append(f"GitHub Backup: {backup_status}")
        elif backup_status == 'stale':
            self.audit_results['warning_findings'].append(f"GitHub Backup: Stale backup ({backup_age:.1f} hours old)")
        
        # Determine overall status
        if self.audit_results['critical_findings']:
            self.audit_results['overall_status'] = 'critical'
        elif self.audit_results['warning_findings']:
            self.audit_results['overall_status'] = 'warning'
        else:
            self.audit_results['overall_status'] = 'healthy'
    
    def generate_audit_reports(self):
        """Generate JSON and Markdown audit reports"""
        try:
            # Ensure directories exist
            os.makedirs("logs/audit", exist_ok=True)
            os.makedirs("docs/audit", exist_ok=True)
            os.makedirs("export/audit", exist_ok=True)
            
            month_year = self.audit_results['month_year']
            
            # Generate JSON report
            json_filename = f"monthly_audit_{month_year}.json"
            json_path = f"logs/audit/{json_filename}"
            
            with open(json_path, 'w') as f:
                json.dump(self.audit_results, f, indent=2, default=str)
            
            # Generate Markdown report
            md_filename = f"monthly_audit_{month_year}.md"
            md_path = f"docs/audit/{md_filename}"
            
            markdown_content = self.generate_markdown_report()
            with open(md_path, 'w') as f:
                f.write(markdown_content)
            
            # Generate sanitized export
            sanitized_results = self.sanitize_audit_results()
            export_path = f"export/audit/{json_filename}"
            
            with open(export_path, 'w') as f:
                json.dump(sanitized_results, f, indent=2, default=str)
            
            self.logger.info(f"📊 Audit reports generated: {json_path}, {md_path}, {export_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate audit reports: {str(e)}")
    
    def generate_markdown_report(self) -> str:
        """Generate comprehensive Markdown audit report"""
        status_emoji = {
            'critical': '🔴',
            'warning': '🟡', 
            'healthy': '🟢',
            'unknown': '⚪'
        }
        
        markdown = f"""# Angles AI Universe™ Monthly Deep Audit Report

**Month:** {datetime.now().strftime('%B %Y')}  
**Generated:** {self.audit_results['timestamp']}  
**Audit ID:** {self.audit_results['audit_id']}  
**Overall Status:** {status_emoji.get(self.audit_results['overall_status'], '⚪')} {self.audit_results['overall_status'].upper()}  
**Duration:** {self.audit_results['duration_seconds']:.2f} seconds

## 📊 Executive Summary

- **Tables Checked:** {self.audit_results['tables_checked']}
- **Total Records:** {self.audit_results['total_records']:,}
- **Critical Findings:** {len(self.audit_results['critical_findings'])}
- **Warning Findings:** {len(self.audit_results['warning_findings'])}
- **Info Findings:** {len(self.audit_results['info_findings'])}

## 🗃️ Data Integrity Analysis

### Supabase Tables Validation
"""
        
        data_integrity = self.audit_results.get('data_integrity', {})
        markdown += f"""
- **Tables Validated:** {data_integrity.get('tables_validated', 0)}
- **Total Rows:** {data_integrity.get('total_rows', 0):,}
- **Integrity Issues:** {len(data_integrity.get('integrity_issues', []))}
- **Performance Issues:** {len(data_integrity.get('performance_issues', []))}

"""
        
        # Add null analysis
        null_analysis = data_integrity.get('null_analysis', {})
        if null_analysis:
            markdown += "### Null Analysis\n\n"
            for table, columns in null_analysis.items():
                markdown += f"**{table}:**\n"
                for column, null_pct in columns.items():
                    status = "⚠️" if null_pct > 5 else "✅"
                    markdown += f"- {column}: {null_pct:.1f}% nulls {status}\n"
                markdown += "\n"
        
        # Sync consistency
        sync_consistency = self.audit_results.get('sync_consistency', {})
        markdown += f"""## 🔄 Notion Sync Consistency

- **Sync Status:** {sync_consistency.get('sync_status', 'unknown')}
- **Supabase Synced Records:** {sync_consistency.get('supabase_synced_count', 0)}
- **Notion Pages Found:** {sync_consistency.get('notion_pages_found', 0)}
- **Sync Drift Count:** {sync_consistency.get('sync_drift_count', 0)}

"""
        
        # Missing pages
        missing_pages = sync_consistency.get('missing_notion_pages', [])
        if missing_pages:
            markdown += "### Missing Notion Pages\n\n"
            for page in missing_pages[:5]:  # Show first 5
                markdown += f"- **ID:** {page['supabase_id']} - {page['decision']}\n"
            if len(missing_pages) > 5:
                markdown += f"- ... and {len(missing_pages) - 5} more\n"
            markdown += "\n"
        
        # Backup verification
        backup_verification = self.audit_results.get('backup_verification', {})
        markdown += f"""## 🐙 GitHub Backup Verification

- **Repository Accessible:** {'✅' if backup_verification.get('repository_accessible') else '❌'}
- **Backup Status:** {backup_verification.get('backup_status', 'unknown')}
- **Latest Commit:** {backup_verification.get('latest_commit_date', 'unknown')}
- **Backup Age:** {backup_verification.get('backup_freshness_hours', 0):.1f} hours
- **Export Files:** {backup_verification.get('export_files_count', 0)}

"""
        
        # Critical findings
        if self.audit_results['critical_findings']:
            markdown += "## 🔴 Critical Findings\n\n"
            for finding in self.audit_results['critical_findings']:
                markdown += f"- {finding}\n"
            markdown += "\n"
        
        # Warning findings
        if self.audit_results['warning_findings']:
            markdown += "## 🟡 Warning Findings\n\n"
            for finding in self.audit_results['warning_findings']:
                markdown += f"- {finding}\n"
            markdown += "\n"
        
        # Recommendations
        markdown += """## 📋 Recommendations

### Immediate Actions Required
"""
        
        if self.audit_results['overall_status'] == 'critical':
            markdown += "- **URGENT:** Address critical findings immediately\n"
            markdown += "- Review backup and sync processes\n"
            markdown += "- Verify data integrity and resolve corruption issues\n"
        elif self.audit_results['overall_status'] == 'warning':
            markdown += "- Address warning findings within 48 hours\n"
            markdown += "- Monitor system performance and sync consistency\n"
        else:
            markdown += "- No immediate actions required\n"
            markdown += "- Continue regular monitoring\n"
        
        markdown += """
### Ongoing Maintenance
- Schedule next audit for next month
- Monitor performance metrics daily
- Verify backup freshness weekly
- Review sync consistency weekly

---
*Generated by Angles AI Universe™ Monthly Deep Audit System*
"""
        
        return markdown
    
    def sanitize_audit_results(self) -> Dict[str, Any]:
        """Create sanitized version of audit results for export"""
        sanitized = self.audit_results.copy()
        
        # Remove sensitive data
        sensitive_keys = ['env', 'credentials', 'tokens']
        for key in sensitive_keys:
            if key in sanitized:
                del sanitized[key]
        
        # Sanitize sync consistency data
        if 'sync_consistency' in sanitized:
            sync_data = sanitized['sync_consistency']
            if 'missing_notion_pages' in sync_data:
                # Only include counts, not actual content
                missing_pages = sync_data['missing_notion_pages']
                sync_data['missing_notion_pages'] = [
                    {
                        'supabase_id': page.get('supabase_id'),
                        'decision_length': len(page.get('decision', '')),
                        'synced_at': page.get('synced_at')
                    }
                    for page in missing_pages
                ]
        
        return sanitized
    
    def handle_critical_findings(self):
        """Handle critical audit findings"""
        if not self.alert_manager:
            self.logger.warning("⚠️ Alert manager not available for critical findings")
            return
        
        try:
            # Create Notion audit report with RED status
            if self.env['notion_token'] and self.env['notion_database_id']:
                self.create_notion_audit_report()
            
            # Send alert
            critical_count = len(self.audit_results['critical_findings'])
            title = f"🔴 CRITICAL: Monthly Audit Found {critical_count} Critical Issues"
            
            message = f"**Monthly Deep Audit Alert**\n"
            message += f"**Audit ID:** {self.audit_results['audit_id']}\n"
            message += f"**Status:** {self.audit_results['overall_status'].upper()}\n"
            message += f"**Critical Findings:** {critical_count}\n\n"
            
            message += "**Critical Issues:**\n"
            for finding in self.audit_results['critical_findings'][:5]:
                message += f"- {finding}\n"
            
            if len(self.audit_results['critical_findings']) > 5:
                message += f"- ... and {len(self.audit_results['critical_findings']) - 5} more\n"
            
            message += "\n**Immediate Action Required:**\n"
            message += "1. Review full audit report in `logs/audit/`\n"
            message += "2. Address data integrity issues\n"
            message += "3. Verify backup and sync processes\n"
            message += "4. Run emergency verification: `python audit/verify_restore.py`\n"
            
            self.alert_manager.send_alert(
                title=title,
                message=message,
                severity="critical",
                tags=['monthly-audit', 'critical', 'data-integrity'],
                github_labels=['monthly-audit', 'critical']
            )
            
        except Exception as e:
            self.logger.error(f"❌ Failed to handle critical findings: {str(e)}")
    
    def create_notion_audit_report(self):
        """Create Notion audit report page"""
        try:
            headers = {
                'Authorization': f"Bearer {self.env['notion_token']}",
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
            
            # Create page data
            status_color = 'red' if self.audit_results['overall_status'] == 'critical' else 'yellow' if self.audit_results['overall_status'] == 'warning' else 'green'
            
            page_data = {
                'parent': {'database_id': self.env['notion_database_id']},
                'properties': {
                    'Name': {
                        'title': [{
                            'text': {'content': f"Monthly Audit Report - {datetime.now().strftime('%B %Y')}"}
                        }]
                    },
                    'Message': {
                        'rich_text': [{
                            'text': {'content': f"Monthly deep audit completed. Status: {self.audit_results['overall_status']}. Critical findings: {len(self.audit_results['critical_findings'])}. See full report in logs/audit/"}
                        }]
                    },
                    'Date': {
                        'date': {'start': datetime.now(timezone.utc).isoformat()}
                    },
                    'Tag': {
                        'multi_select': [
                            {'name': 'monthly-audit'},
                            {'name': f'status-{self.audit_results["overall_status"]}'},
                            {'name': 'automated'}
                        ]
                    }
                }
            }
            
            url = 'https://api.notion.com/v1/pages'
            response = requests.post(url, headers=headers, json=page_data, timeout=15)
            
            if response.status_code == 200:
                self.logger.info("✅ Notion audit report created")
            else:
                self.logger.error(f"❌ Failed to create Notion audit report: HTTP {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"❌ Notion audit report creation failed: {str(e)}")
    
    def log_audit_summary(self):
        """Log comprehensive audit summary"""
        self.logger.info("=" * 70)
        self.logger.info("🎉 Monthly Deep Audit Complete")
        self.logger.info(f"   Audit ID: {self.audit_results['audit_id']}")
        self.logger.info(f"   Overall Status: {self.audit_results['overall_status'].upper()}")
        self.logger.info(f"   Duration: {self.audit_results['duration_seconds']:.2f} seconds")
        self.logger.info(f"   Tables Checked: {self.audit_results['tables_checked']}")
        self.logger.info(f"   Total Records: {self.audit_results['total_records']:,}")
        self.logger.info(f"   Critical Findings: {len(self.audit_results['critical_findings'])}")
        self.logger.info(f"   Warning Findings: {len(self.audit_results['warning_findings'])}")
        
        data_integrity = self.audit_results.get('data_integrity', {})
        sync_consistency = self.audit_results.get('sync_consistency', {})
        backup_verification = self.audit_results.get('backup_verification', {})
        
        self.logger.info(f"   Sync Drift: {sync_consistency.get('sync_drift_count', 0)} items")
        self.logger.info(f"   Backup Status: {backup_verification.get('backup_status', 'unknown')}")
        self.logger.info(f"   Backup Age: {backup_verification.get('backup_freshness_hours', 0):.1f} hours")

def main():
    """Main entry point for monthly audit"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Angles AI Universe™ Monthly Deep Audit System')
    parser.add_argument('--run', action='store_true', help='Run comprehensive monthly audit')
    parser.add_argument('--report', action='store_true', help='Show latest audit report')
    parser.add_argument('--status', action='store_true', help='Show audit system status')
    
    args = parser.parse_args()
    
    try:
        audit_system = MonthlyAuditSystem()
        
        if args.run or not any([args.report, args.status]):
            # Run comprehensive audit
            results = audit_system.run_comprehensive_audit()
            
            print(f"\n🔍 Monthly Deep Audit Results:")
            print(f"  Audit ID: {results['audit_id']}")
            print(f"  Overall Status: {results['overall_status']}")
            print(f"  Duration: {results['duration_seconds']:.2f}s")
            print(f"  Critical Findings: {len(results['critical_findings'])}")
            print(f"  Tables Checked: {results['tables_checked']}")
            print(f"  Total Records: {results['total_records']:,}")
            
            # Exit with appropriate code
            if results['overall_status'] == 'critical':
                sys.exit(2)
            elif results['overall_status'] == 'warning':
                sys.exit(1)
            else:
                sys.exit(0)
        
        elif args.report:
            # Show latest report
            try:
                month_year = datetime.now().strftime('%Y%m')
                report_file = f"logs/audit/monthly_audit_{month_year}.json"
                
                with open(report_file, 'r') as f:
                    report = json.load(f)
                
                print(f"\n📊 Latest Monthly Audit Report:")
                print(f"  Audit ID: {report['audit_id']}")
                print(f"  Status: {report['overall_status']}")
                print(f"  Timestamp: {report['timestamp']}")
                print(f"  Critical: {len(report['critical_findings'])}")
                print(f"  Warnings: {len(report['warning_findings'])}")
                
            except FileNotFoundError:
                print(f"\n📊 No audit report found for {datetime.now().strftime('%B %Y')}")
        
        elif args.status:
            print(f"\n🔍 Monthly Audit System Status:")
            print(f"  System: Initialized")
            print(f"  Supabase: {'Connected' if audit_system.env['supabase_url'] else 'Not configured'}")
            print(f"  Notion: {'Connected' if audit_system.env['notion_token'] else 'Not configured'}")
            print(f"  GitHub: {'Connected' if audit_system.env['github_token'] else 'Not configured'}")
    
    except KeyboardInterrupt:
        print("\n🛑 Monthly audit interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Monthly audit failed: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()