#!/usr/bin/env python3
"""
Angles AI Universe™ Performance Benchmarking System
Comprehensive performance monitoring for Supabase, Notion, and Git operations

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import csv
import json
import time
import logging
import requests
import subprocess
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import tempfile

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from alerts.notify import AlertManager
except ImportError:
    AlertManager = None

try:
    from git_helpers import GitHelper
except ImportError:
    GitHelper = None

class PerformanceBenchmarkSystem:
    """Comprehensive performance benchmarking system"""
    
    def __init__(self):
        """Initialize performance benchmarking system"""
        self.setup_logging()
        self.load_environment()
        self.alert_manager = AlertManager() if AlertManager else None
        self.git_helper = GitHelper() if GitHelper else None
        
        # Benchmark configuration
        self.config = {
            'supabase_read_limit': 50,
            'benchmark_timeout': 30,
            'warning_threshold_ms': 2000,
            'critical_threshold_ms': 5000,
            'temp_table_name': 'audit_perf_temp',
            'csv_date_format': '%Y%m%d',
            'summary_days': 30
        }
        
        # Initialize benchmark results
        self.benchmark_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'benchmark_id': f"perf_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'supabase_read_ms': None,
            'supabase_write_ms': None,
            'notion_write_ms': None,
            'git_push_ms': None,
            'overall_status': 'unknown',
            'warnings': [],
            'errors': [],
            'duration_total_ms': 0
        }
        
        self.logger.info("⚡ Angles AI Universe™ Performance Benchmarking Initialized")
    
    def setup_logging(self):
        """Setup logging for performance benchmarking"""
        os.makedirs("logs/perf", exist_ok=True)
        
        self.logger = logging.getLogger('perf_benchmark')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/perf/benchmark.log"
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
        
        self.logger.info("📋 Environment loaded for performance benchmarking")
    
    def get_supabase_headers(self) -> Dict[str, str]:
        """Get standard Supabase headers"""
        return {
            'apikey': self.env['supabase_key'],
            'Authorization': f"Bearer {self.env['supabase_key']}",
            'Content-Type': 'application/json'
        }
    
    def benchmark_supabase_read(self) -> Dict[str, Any]:
        """Benchmark Supabase read performance (latest 50 records)"""
        self.logger.info("📖 Benchmarking Supabase read performance...")
        
        read_result = {
            'success': False,
            'duration_ms': None,
            'records_read': 0,
            'error_message': None,
            'avg_ms_per_record': None
        }
        
        if not self.env['supabase_url'] or not self.env['supabase_key']:
            read_result['error_message'] = "Supabase credentials not available"
            return read_result
        
        try:
            headers = self.get_supabase_headers()
            url = f"{self.env['supabase_url']}/rest/v1/decision_vault"
            params = {
                'select': 'id,decision,date,active,created_at',
                'order': 'created_at.desc',
                'limit': str(self.config['supabase_read_limit'])
            }
            
            start_time = time.time()
            response = requests.get(url, headers=headers, params=params, timeout=self.config['benchmark_timeout'])
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                records_count = len(data)
                
                read_result['success'] = True
                read_result['duration_ms'] = duration_ms
                read_result['records_read'] = records_count
                read_result['avg_ms_per_record'] = duration_ms / records_count if records_count > 0 else 0
                
                # Check performance warnings
                if duration_ms > self.config['critical_threshold_ms']:
                    self.benchmark_results['errors'].append(f"Supabase read critical: {duration_ms:.1f}ms")
                elif duration_ms > self.config['warning_threshold_ms']:
                    self.benchmark_results['warnings'].append(f"Supabase read slow: {duration_ms:.1f}ms")
                
                self.logger.info(f"✅ Supabase read: {records_count} records in {duration_ms:.1f}ms")
            else:
                read_result['error_message'] = f"HTTP {response.status_code}: {response.text[:200]}"
                self.logger.error(f"❌ Supabase read failed: {read_result['error_message']}")
        
        except Exception as e:
            read_result['error_message'] = str(e)
            self.logger.error(f"❌ Supabase read error: {str(e)}")
        
        return read_result
    
    def benchmark_supabase_write(self) -> Dict[str, Any]:
        """Benchmark Supabase write performance (test row to temp table)"""
        self.logger.info("✍️ Benchmarking Supabase write performance...")
        
        write_result = {
            'success': False,
            'duration_ms': None,
            'test_record_id': None,
            'error_message': None,
            'cleanup_success': False
        }
        
        if not self.env['supabase_url'] or not self.env['supabase_key']:
            write_result['error_message'] = "Supabase credentials not available"
            return write_result
        
        try:
            headers = self.get_supabase_headers()
            
            # Create test record data
            test_data = {
                'benchmark_id': self.benchmark_results['benchmark_id'],
                'test_timestamp': datetime.now(timezone.utc).isoformat(),
                'test_data': f"Performance test at {datetime.now().isoformat()}"
            }
            
            # Try to insert into a temp table (create if not exists)
            temp_table_url = f"{self.env['supabase_url']}/rest/v1/{self.config['temp_table_name']}"
            
            start_time = time.time()
            response = requests.post(temp_table_url, headers=headers, json=test_data, timeout=self.config['benchmark_timeout'])
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code in [200, 201]:
                # Extract inserted record ID if available
                response_data = response.json()
                if response_data and isinstance(response_data, list) and len(response_data) > 0:
                    write_result['test_record_id'] = response_data[0].get('id')
                
                write_result['success'] = True
                write_result['duration_ms'] = duration_ms
                
                # Check performance warnings
                if duration_ms > self.config['critical_threshold_ms']:
                    self.benchmark_results['errors'].append(f"Supabase write critical: {duration_ms:.1f}ms")
                elif duration_ms > self.config['warning_threshold_ms']:
                    self.benchmark_results['warnings'].append(f"Supabase write slow: {duration_ms:.1f}ms")
                
                # Attempt cleanup
                if write_result['test_record_id']:
                    try:
                        delete_url = f"{temp_table_url}?id=eq.{write_result['test_record_id']}"
                        delete_response = requests.delete(delete_url, headers=headers, timeout=10)
                        write_result['cleanup_success'] = delete_response.status_code in [200, 204]
                    except:
                        pass  # Cleanup is best effort
                
                self.logger.info(f"✅ Supabase write: {duration_ms:.1f}ms")
            else:
                write_result['error_message'] = f"HTTP {response.status_code}: {response.text[:200]}"
                self.logger.error(f"❌ Supabase write failed: {write_result['error_message']}")
        
        except Exception as e:
            write_result['error_message'] = str(e)
            self.logger.error(f"❌ Supabase write error: {str(e)}")
        
        return write_result
    
    def benchmark_notion_write(self) -> Dict[str, Any]:
        """Benchmark Notion write performance"""
        self.logger.info("📝 Benchmarking Notion write performance...")
        
        notion_result = {
            'success': False,
            'duration_ms': None,
            'page_id': None,
            'error_message': None,
            'fallback_used': False
        }
        
        if not self.env['notion_token']:
            notion_result['error_message'] = "Notion token not available"
            return notion_result
        
        try:
            headers = {
                'Authorization': f"Bearer {self.env['notion_token']}",
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
            
            # Try to write to perf logs database or fallback
            if self.env['notion_database_id']:
                # Use main database with perf tag
                page_data = {
                    'parent': {'database_id': self.env['notion_database_id']},
                    'properties': {
                        'Message': {
                            'rich_text': [{
                                'text': {
                                    'content': f"Performance benchmark test {self.benchmark_results['benchmark_id']}"
                                }
                            }]
                        }
                    }
                }
                
                # Add perf tag if possible
                if 'Tag' in page_data.get('properties', {}):
                    page_data['properties']['Tag'] = {
                        'select': {'name': 'perf'}
                    }
                
                url = 'https://api.notion.com/v1/pages'
            else:
                notion_result['error_message'] = "No Notion database ID available"
                return notion_result
            
            start_time = time.time()
            response = requests.post(url, headers=headers, json=page_data, timeout=self.config['benchmark_timeout'])
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                notion_result['page_id'] = response_data.get('id')
                notion_result['success'] = True
                notion_result['duration_ms'] = duration_ms
                
                # Check performance warnings
                if duration_ms > self.config['critical_threshold_ms']:
                    self.benchmark_results['errors'].append(f"Notion write critical: {duration_ms:.1f}ms")
                elif duration_ms > self.config['warning_threshold_ms']:
                    self.benchmark_results['warnings'].append(f"Notion write slow: {duration_ms:.1f}ms")
                
                self.logger.info(f"✅ Notion write: {duration_ms:.1f}ms")
            else:
                notion_result['error_message'] = f"HTTP {response.status_code}: {response.text[:200]}"
                self.logger.error(f"❌ Notion write failed: {notion_result['error_message']}")
        
        except Exception as e:
            notion_result['error_message'] = str(e)
            self.logger.error(f"❌ Notion write error: {str(e)}")
        
        return notion_result
    
    def benchmark_git_push(self) -> Dict[str, Any]:
        """Benchmark Git push performance (noop commit)"""
        self.logger.info("🔀 Benchmarking Git push performance...")
        
        git_result = {
            'success': False,
            'duration_ms': None,
            'commit_hash': None,
            'error_message': None,
            'operations': {'add': False, 'commit': False, 'push': False}
        }
        
        try:
            # Create a temporary file for the noop commit
            temp_file = f"logs/perf/.benchmark_{self.benchmark_results['benchmark_id']}.tmp"
            
            with open(temp_file, 'w') as f:
                f.write(f"Performance benchmark test\nTimestamp: {datetime.now().isoformat()}\nBenchmark ID: {self.benchmark_results['benchmark_id']}\n")
            
            total_start_time = time.time()
            
            # Git add
            add_result = subprocess.run(['git', 'add', temp_file], capture_output=True, text=True, timeout=30)
            git_result['operations']['add'] = add_result.returncode == 0
            
            if add_result.returncode == 0:
                # Git commit
                commit_msg = f"Perf benchmark noop commit {self.benchmark_results['benchmark_id']}"
                commit_result = subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True, timeout=30)
                git_result['operations']['commit'] = commit_result.returncode == 0
                
                if commit_result.returncode == 0:
                    # Extract commit hash
                    hash_result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, timeout=10)
                    if hash_result.returncode == 0:
                        git_result['commit_hash'] = hash_result.stdout.strip()
                    
                    # Git push (if git_helper available and configured)
                    if self.git_helper:
                        push_start = time.time()
                        push_result = self.git_helper.safe_commit_and_push([temp_file], commit_msg)
                        push_duration = (time.time() - push_start) * 1000
                        
                        if push_result.get('success', False):
                            git_result['operations']['push'] = True
                        else:
                            # Push failed but we still have add/commit timing
                            pass
                    else:
                        # No git helper, just try basic push
                        push_result = subprocess.run(['git', 'push'], capture_output=True, text=True, timeout=60)
                        git_result['operations']['push'] = push_result.returncode == 0
            
            duration_ms = (time.time() - total_start_time) * 1000
            git_result['duration_ms'] = duration_ms
            git_result['success'] = git_result['operations']['add'] and git_result['operations']['commit']
            
            # Check performance warnings
            if duration_ms > self.config['critical_threshold_ms']:
                self.benchmark_results['errors'].append(f"Git push critical: {duration_ms:.1f}ms")
            elif duration_ms > self.config['warning_threshold_ms']:
                self.benchmark_results['warnings'].append(f"Git push slow: {duration_ms:.1f}ms")
            
            # Clean up temp file
            try:
                os.remove(temp_file)
            except:
                pass
            
            operations_status = ", ".join([f"{op}: {'✅' if success else '❌'}" for op, success in git_result['operations'].items()])
            self.logger.info(f"✅ Git operations ({operations_status}): {duration_ms:.1f}ms")
        
        except Exception as e:
            git_result['error_message'] = str(e)
            self.logger.error(f"❌ Git push error: {str(e)}")
        
        return git_result
    
    def emit_csv_results(self) -> bool:
        """Emit benchmark results to CSV file"""
        try:
            # Generate CSV filename
            csv_date = datetime.now().strftime(self.config['csv_date_format'])
            csv_file = f"logs/perf/perf_{csv_date}.csv"
            
            # Prepare CSV row
            csv_row = {
                'timestamp': self.benchmark_results['timestamp'],
                'benchmark_id': self.benchmark_results['benchmark_id'],
                'supabase_read_ms': self.benchmark_results['supabase_read_ms'],
                'supabase_write_ms': self.benchmark_results['supabase_write_ms'],
                'notion_write_ms': self.benchmark_results['notion_write_ms'],
                'git_push_ms': self.benchmark_results['git_push_ms'],
                'overall_status': self.benchmark_results['overall_status'],
                'duration_total_ms': self.benchmark_results['duration_total_ms'],
                'warnings_count': len(self.benchmark_results['warnings']),
                'errors_count': len(self.benchmark_results['errors'])
            }
            
            # Check if file exists to determine if we need headers
            file_exists = os.path.exists(csv_file)
            
            with open(csv_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_row.keys())
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow(csv_row)
            
            self.logger.info(f"📊 CSV results written to {csv_file}")
            return True
        
        except Exception as e:
            self.logger.error(f"❌ CSV export failed: {str(e)}")
            return False
    
    def update_rolling_summary(self) -> bool:
        """Update rolling performance summary"""
        try:
            # Collect recent performance data
            perf_data = self.collect_recent_performance_data()
            
            if not perf_data:
                self.logger.warning("⚠️ No performance data available for summary")
                return False
            
            # Calculate statistics
            summary = self.calculate_performance_statistics(perf_data)
            
            # Generate Markdown summary
            summary_content = self.generate_summary_markdown(summary)
            
            # Write summary file
            os.makedirs("docs/perf", exist_ok=True)
            summary_file = "docs/perf/summary.md"
            
            with open(summary_file, 'w') as f:
                f.write(summary_content)
            
            self.logger.info(f"📈 Rolling summary updated: {summary_file}")
            return True
        
        except Exception as e:
            self.logger.error(f"❌ Rolling summary update failed: {str(e)}")
            return False
    
    def collect_recent_performance_data(self) -> List[Dict[str, Any]]:
        """Collect performance data from recent CSV files"""
        perf_data = []
        
        try:
            # Look for CSV files in the last N days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.config['summary_days'])
            
            current_date = start_date
            while current_date <= end_date:
                csv_file = f"logs/perf/perf_{current_date.strftime(self.config['csv_date_format'])}.csv"
                
                if os.path.exists(csv_file):
                    with open(csv_file, 'r') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            # Convert numeric fields
                            try:
                                for field in ['supabase_read_ms', 'supabase_write_ms', 'notion_write_ms', 'git_push_ms', 'duration_total_ms']:
                                    if row[field] and row[field] != 'None':
                                        row[field] = float(row[field])
                                    else:
                                        row[field] = None
                            except:
                                pass
                            
                            perf_data.append(row)
                
                current_date += timedelta(days=1)
        
        except Exception as e:
            self.logger.error(f"❌ Error collecting performance data: {str(e)}")
        
        return perf_data
    
    def calculate_performance_statistics(self, perf_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance statistics (min/avg/p95)"""
        stats = {
            'total_benchmarks': len(perf_data),
            'date_range': {
                'start': None,
                'end': None
            },
            'metrics': {}
        }
        
        if not perf_data:
            return stats
        
        # Date range
        timestamps = [row['timestamp'] for row in perf_data if row['timestamp']]
        if timestamps:
            stats['date_range']['start'] = min(timestamps)
            stats['date_range']['end'] = max(timestamps)
        
        # Calculate stats for each metric
        metrics = ['supabase_read_ms', 'supabase_write_ms', 'notion_write_ms', 'git_push_ms', 'duration_total_ms']
        
        for metric in metrics:
            values = [row[metric] for row in perf_data if row[metric] is not None]
            
            if values:
                stats['metrics'][metric] = {
                    'count': len(values),
                    'min': min(values),
                    'avg': statistics.mean(values),
                    'p95': self.calculate_percentile(values, 95),
                    'max': max(values)
                }
            else:
                stats['metrics'][metric] = {
                    'count': 0,
                    'min': None,
                    'avg': None,
                    'p95': None,
                    'max': None
                }
        
        return stats
    
    def calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * len(sorted_values)
        
        if index.is_integer():
            return sorted_values[int(index) - 1]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[min(int(index) + 1, len(sorted_values) - 1)]
            return lower + (upper - lower) * (index - int(index))
    
    def generate_summary_markdown(self, summary: Dict[str, Any]) -> str:
        """Generate Markdown summary content"""
        now = datetime.now(timezone.utc)
        
        content = f"""# Performance Summary

**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Total Benchmarks:** {summary['total_benchmarks']}  
**Date Range:** {summary['date_range']['start']} to {summary['date_range']['end']}

## Performance Metrics (Last {self.config['summary_days']} Days)

| Metric | Count | Min (ms) | Avg (ms) | P95 (ms) | Max (ms) |
|--------|-------|----------|----------|----------|----------|
"""
        
        for metric_name, stats in summary['metrics'].items():
            display_name = metric_name.replace('_', ' ').title()
            count = stats['count']
            min_val = f"{stats['min']:.1f}" if stats['min'] is not None else "N/A"
            avg_val = f"{stats['avg']:.1f}" if stats['avg'] is not None else "N/A"
            p95_val = f"{stats['p95']:.1f}" if stats['p95'] is not None else "N/A"
            max_val = f"{stats['max']:.1f}" if stats['max'] is not None else "N/A"
            
            content += f"| {display_name} | {count} | {min_val} | {avg_val} | {p95_val} | {max_val} |\n"
        
        content += f"""
## Performance Thresholds

- **Warning:** {self.config['warning_threshold_ms']}ms
- **Critical:** {self.config['critical_threshold_ms']}ms

## Latest Benchmark

**ID:** {self.benchmark_results['benchmark_id']}  
**Status:** {self.benchmark_results['overall_status']}  
**Timestamp:** {self.benchmark_results['timestamp']}

### Latest Results
- **Supabase Read:** {self.benchmark_results['supabase_read_ms']:.1f}ms
- **Supabase Write:** {self.benchmark_results['supabase_write_ms']:.1f}ms  
- **Notion Write:** {self.benchmark_results['notion_write_ms']:.1f}ms
- **Git Push:** {self.benchmark_results['git_push_ms']:.1f}ms

---
*Auto-generated by Angles AI Universe™ Performance Benchmarking System*
"""
        return content
    
    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run complete performance benchmark"""
        self.logger.info("🚀 Starting Comprehensive Performance Benchmark")
        self.logger.info("=" * 60)
        
        total_start_time = time.time()
        
        try:
            # Step 1: Benchmark Supabase read
            self.logger.info("1️⃣ Benchmarking Supabase read operations...")
            supabase_read = self.benchmark_supabase_read()
            self.benchmark_results['supabase_read_ms'] = supabase_read['duration_ms']
            
            # Step 2: Benchmark Supabase write
            self.logger.info("2️⃣ Benchmarking Supabase write operations...")
            supabase_write = self.benchmark_supabase_write()
            self.benchmark_results['supabase_write_ms'] = supabase_write['duration_ms']
            
            # Step 3: Benchmark Notion write
            self.logger.info("3️⃣ Benchmarking Notion write operations...")
            notion_write = self.benchmark_notion_write()
            self.benchmark_results['notion_write_ms'] = notion_write['duration_ms']
            
            # Step 4: Benchmark Git push
            self.logger.info("4️⃣ Benchmarking Git push operations...")
            git_push = self.benchmark_git_push()
            self.benchmark_results['git_push_ms'] = git_push['duration_ms']
            
            # Calculate total duration
            total_duration_ms = (time.time() - total_start_time) * 1000
            self.benchmark_results['duration_total_ms'] = total_duration_ms
            
            # Determine overall status
            if self.benchmark_results['errors']:
                self.benchmark_results['overall_status'] = 'failed'
            elif self.benchmark_results['warnings']:
                self.benchmark_results['overall_status'] = 'warning'
            else:
                self.benchmark_results['overall_status'] = 'healthy'
            
            # Step 5: Emit CSV results
            self.logger.info("5️⃣ Exporting results to CSV...")
            csv_success = self.emit_csv_results()
            
            # Step 6: Update rolling summary
            self.logger.info("6️⃣ Updating performance summary...")
            summary_success = self.update_rolling_summary()
            
            # Log final results
            self.logger.info("=" * 60)
            self.logger.info(f"🏁 Performance Benchmark Complete")
            self.logger.info(f"   Overall Status: {self.benchmark_results['overall_status']}")
            self.logger.info(f"   Total Duration: {total_duration_ms:.1f}ms")
            self.logger.info(f"   Warnings: {len(self.benchmark_results['warnings'])}")
            self.logger.info(f"   Errors: {len(self.benchmark_results['errors'])}")
            
            if self.benchmark_results['warnings']:
                for warning in self.benchmark_results['warnings']:
                    self.logger.warning(f"⚠️ {warning}")
            
            if self.benchmark_results['errors']:
                for error in self.benchmark_results['errors']:
                    self.logger.error(f"❌ {error}")
            
            # Send alerts for critical performance issues
            if self.alert_manager and self.benchmark_results['errors']:
                self.alert_manager.send_alert(
                    title="Performance Benchmark Critical Issues",
                    message=f"Performance benchmark detected critical issues: {', '.join(self.benchmark_results['errors'])}",
                    severity="warning",
                    tags=['performance', 'benchmark', 'critical']
                )
        
        except Exception as e:
            self.benchmark_results['overall_status'] = 'error'
            self.benchmark_results['errors'].append(f"Benchmark failed: {str(e)}")
            self.logger.error(f"💥 Benchmark error: {str(e)}")
            
            if self.alert_manager:
                self.alert_manager.send_alert(
                    title="Performance Benchmark System Failure",
                    message=f"Performance benchmark system encountered an error: {str(e)}",
                    severity="critical",
                    tags=['performance', 'benchmark', 'failure']
                )
        
        return self.benchmark_results

def main():
    """Main entry point for performance benchmarking"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Performance benchmarking system')
    parser.add_argument('--run', action='store_true', help='Run complete benchmark')
    parser.add_argument('--summary', action='store_true', help='Update performance summary only')
    parser.add_argument('--test-supabase', action='store_true', help='Test Supabase operations only')
    parser.add_argument('--test-notion', action='store_true', help='Test Notion operations only')
    parser.add_argument('--test-git', action='store_true', help='Test Git operations only')
    
    args = parser.parse_args()
    
    try:
        benchmark = PerformanceBenchmarkSystem()
        
        if args.run:
            results = benchmark.run_comprehensive_benchmark()
            print(f"\n⚡ Performance Benchmark Complete")
            print(f"Overall Status: {results['overall_status']}")
            print(f"Duration: {results['duration_total_ms']:.1f}ms")
        
        elif args.summary:
            success = benchmark.update_rolling_summary()
            print(f"\n📈 Summary Update: {'Success' if success else 'Failed'}")
        
        elif args.test_supabase:
            read_result = benchmark.benchmark_supabase_read()
            write_result = benchmark.benchmark_supabase_write()
            print(f"\n📊 Supabase Performance:")
            print(f"  Read: {read_result['duration_ms']:.1f}ms ({read_result['records_read']} records)")
            print(f"  Write: {write_result['duration_ms']:.1f}ms")
        
        elif args.test_notion:
            notion_result = benchmark.benchmark_notion_write()
            print(f"\n📊 Notion Performance:")
            print(f"  Write: {notion_result['duration_ms']:.1f}ms")
        
        elif args.test_git:
            git_result = benchmark.benchmark_git_push()
            print(f"\n📊 Git Performance:")
            print(f"  Push: {git_result['duration_ms']:.1f}ms")
        
        else:
            # Default: run complete benchmark
            results = benchmark.run_comprehensive_benchmark()
            print(f"\n⚡ Performance Benchmark Complete")
            print(f"Overall Status: {results['overall_status']}")
    
    except KeyboardInterrupt:
        print("\n🛑 Performance benchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Performance benchmark failed: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()