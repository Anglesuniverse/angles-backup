#!/usr/bin/env python3
"""
Angles AI Universe™ Deep Health Check System
Comprehensive system health monitoring and validation

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import psutil
import logging
import requests
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import hashlib

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from alerts.notify import AlertManager
except ImportError:
    AlertManager = None

try:
    from memory_bridge import get_bridge
except ImportError:
    get_bridge = None

class DeepHealthCheckSystem:
    """Comprehensive system health monitoring"""
    
    def __init__(self):
        """Initialize health check system"""
        self.setup_logging()
        self.load_environment()
        self.alert_manager = AlertManager() if AlertManager else None
        
        # Health check configuration
        self.config = {
            'timeout_per_check': 30,
            'critical_disk_usage': 90,  # %
            'warning_disk_usage': 80,   # %
            'critical_memory_usage': 95,  # %
            'warning_memory_usage': 85,   # %
            'max_response_time_ms': 5000,
            'warning_response_time_ms': 2000,
            'check_external_services': True,
            'validate_data_integrity': True,
            'check_log_rotation': True,
            'verify_backup_freshness': True,
            'max_backup_age_hours': 48
        }
        
        # Health check results
        self.health_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'check_id': f"health_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'overall_status': 'unknown',
            'overall_score': 0,
            'checks': {},
            'system_metrics': {},
            'warnings': [],
            'critical_issues': [],
            'recommendations': [],
            'duration_seconds': 0
        }
        
        # Define health checks
        self.health_checks = [
            ('system_resources', self.check_system_resources, True),
            ('disk_space', self.check_disk_space, True),
            ('supabase_connectivity', self.check_supabase_health, True),
            ('notion_connectivity', self.check_notion_health, False),
            ('git_operations', self.check_git_health, False),
            ('memory_bridge', self.check_memory_bridge_health, True),
            ('log_system', self.check_log_system_health, False),
            ('backup_freshness', self.check_backup_freshness, False),
            ('data_integrity', self.check_data_integrity, True),
            ('service_processes', self.check_service_processes, False)
        ]
        
        self.logger.info("❤️ Angles AI Universe™ Deep Health Check System Initialized")
    
    def setup_logging(self):
        """Setup logging for health check system"""
        os.makedirs("logs/health", exist_ok=True)
        
        self.logger = logging.getLogger('health_check')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/health/health_check.log"
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
        
        self.logger.info("📋 Environment loaded for health checks")
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Load average (Unix systems)
            load_avg = None
            try:
                load_avg = os.getloadavg()
            except:
                pass
            
            result = {
                'status': 'healthy',
                'metrics': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'memory_available_mb': memory.available / (1024 * 1024),
                    'memory_total_mb': memory.total / (1024 * 1024),
                    'load_average': load_avg
                },
                'issues': []
            }
            
            # Check thresholds
            if memory_percent >= self.config['critical_memory_usage']:
                result['status'] = 'critical'
                result['issues'].append(f"Critical memory usage: {memory_percent}%")
            elif memory_percent >= self.config['warning_memory_usage']:
                result['status'] = 'warning'
                result['issues'].append(f"High memory usage: {memory_percent}%")
            
            if cpu_percent >= 90:
                result['status'] = 'critical' if result['status'] != 'critical' else 'critical'
                result['issues'].append(f"Critical CPU usage: {cpu_percent}%")
            elif cpu_percent >= 75:
                result['status'] = 'warning' if result['status'] == 'healthy' else result['status']
                result['issues'].append(f"High CPU usage: {cpu_percent}%")
            
            self.logger.info(f"💻 System resources: CPU {cpu_percent}%, Memory {memory_percent}%")
            return result
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'metrics': {},
                'issues': [f"System resource check failed: {e}"]
            }
    
    def check_disk_space(self) -> Dict[str, Any]:
        """Check disk space usage"""
        try:
            disk_usage = psutil.disk_usage('.')
            used_percent = (disk_usage.used / disk_usage.total) * 100
            
            result = {
                'status': 'healthy',
                'metrics': {
                    'used_percent': used_percent,
                    'free_gb': disk_usage.free / (1024**3),
                    'total_gb': disk_usage.total / (1024**3),
                    'used_gb': disk_usage.used / (1024**3)
                },
                'issues': []
            }
            
            # Check thresholds
            if used_percent >= self.config['critical_disk_usage']:
                result['status'] = 'critical'
                result['issues'].append(f"Critical disk usage: {used_percent:.1f}%")
            elif used_percent >= self.config['warning_disk_usage']:
                result['status'] = 'warning'
                result['issues'].append(f"High disk usage: {used_percent:.1f}%")
            
            self.logger.info(f"💾 Disk space: {used_percent:.1f}% used ({result['metrics']['free_gb']:.1f}GB free)")
            return result
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'metrics': {},
                'issues': [f"Disk space check failed: {e}"]
            }
    
    def check_supabase_health(self) -> Dict[str, Any]:
        """Check Supabase connectivity and response time"""
        if not self.env['supabase_url'] or not self.env['supabase_key']:
            return {
                'status': 'warning',
                'metrics': {},
                'issues': ['Supabase credentials not configured']
            }
        
        try:
            headers = {
                'apikey': self.env['supabase_key'],
                'Authorization': f"Bearer {self.env['supabase_key']}",
                'Content-Type': 'application/json'
            }
            
            # Test connection with simple query
            url = f"{self.env['supabase_url']}/rest/v1/decision_vault"
            params = {'select': 'id', 'limit': '1'}
            
            start_time = time.time()
            response = requests.get(url, headers=headers, params=params, timeout=self.config['timeout_per_check'])
            response_time = (time.time() - start_time) * 1000
            
            result = {
                'status': 'healthy',
                'metrics': {
                    'response_time_ms': response_time,
                    'status_code': response.status_code,
                    'url': self.env['supabase_url']
                },
                'issues': []
            }
            
            # Check response
            if response.status_code != 200:
                result['status'] = 'critical'
                result['issues'].append(f"Supabase HTTP {response.status_code}")
            elif response_time >= self.config['max_response_time_ms']:
                result['status'] = 'critical'
                result['issues'].append(f"Supabase slow response: {response_time:.0f}ms")
            elif response_time >= self.config['warning_response_time_ms']:
                result['status'] = 'warning'
                result['issues'].append(f"Supabase slow response: {response_time:.0f}ms")
            
            self.logger.info(f"🗄️ Supabase: {response.status_code} in {response_time:.0f}ms")
            return result
        
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'metrics': {},
                'issues': [f"Supabase connection failed: {e}"]
            }
    
    def check_notion_health(self) -> Dict[str, Any]:
        """Check Notion API connectivity"""
        if not self.env['notion_token']:
            return {
                'status': 'info',
                'metrics': {},
                'issues': ['Notion credentials not configured (optional)']
            }
        
        try:
            headers = {
                'Authorization': f"Bearer {self.env['notion_token']}",
                'Notion-Version': '2022-06-28'
            }
            
            # Test with simple API call
            url = 'https://api.notion.com/v1/users/me'
            
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=self.config['timeout_per_check'])
            response_time = (time.time() - start_time) * 1000
            
            result = {
                'status': 'healthy',
                'metrics': {
                    'response_time_ms': response_time,
                    'status_code': response.status_code
                },
                'issues': []
            }
            
            if response.status_code != 200:
                result['status'] = 'warning'
                result['issues'].append(f"Notion HTTP {response.status_code}")
            elif response_time >= self.config['max_response_time_ms']:
                result['status'] = 'warning'
                result['issues'].append(f"Notion slow response: {response_time:.0f}ms")
            
            self.logger.info(f"📝 Notion: {response.status_code} in {response_time:.0f}ms")
            return result
        
        except Exception as e:
            return {
                'status': 'warning',
                'error': str(e),
                'metrics': {},
                'issues': [f"Notion connection failed: {e}"]
            }
    
    def check_git_health(self) -> Dict[str, Any]:
        """Check Git operations and repository status"""
        try:
            # Check git status
            result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, timeout=10)
            
            git_result = {
                'status': 'healthy',
                'metrics': {
                    'git_available': True,
                    'uncommitted_changes': len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
                },
                'issues': []
            }
            
            # Check for uncommitted changes
            if result.stdout.strip():
                git_result['status'] = 'info'
                git_result['issues'].append(f"Uncommitted changes: {git_result['metrics']['uncommitted_changes']}")
            
            # Check last commit
            try:
                commit_result = subprocess.run(['git', 'log', '-1', '--format=%cr'], capture_output=True, text=True, timeout=5)
                if commit_result.returncode == 0:
                    git_result['metrics']['last_commit'] = commit_result.stdout.strip()
            except:
                pass
            
            self.logger.info(f"🔀 Git: {git_result['metrics']['uncommitted_changes']} uncommitted changes")
            return git_result
        
        except Exception as e:
            return {
                'status': 'warning',
                'error': str(e),
                'metrics': {'git_available': False},
                'issues': [f"Git check failed: {e}"]
            }
    
    def check_memory_bridge_health(self) -> Dict[str, Any]:
        """Check memory bridge functionality"""
        if not get_bridge:
            return {
                'status': 'warning',
                'metrics': {},
                'issues': ['Memory bridge not available']
            }
        
        try:
            bridge = get_bridge()
            
            # Test health check
            bridge_healthy = bridge.healthcheck()
            
            result = {
                'status': 'healthy' if bridge_healthy else 'critical',
                'metrics': {
                    'bridge_available': True,
                    'supabase_connected': bridge_healthy,
                    'notion_enabled': bridge.notion_enabled
                },
                'issues': []
            }
            
            if not bridge_healthy:
                result['issues'].append('Memory bridge health check failed')
            
            # Check queue file size
            if os.path.exists(bridge.queue_file):
                queue_size = os.path.getsize(bridge.queue_file)
                result['metrics']['queue_size_bytes'] = queue_size
                
                if queue_size > 1024 * 1024:  # 1MB
                    result['status'] = 'warning' if result['status'] == 'healthy' else result['status']
                    result['issues'].append(f"Large sync queue: {queue_size / 1024:.0f}KB")
            
            self.logger.info(f"🔗 Memory bridge: {'healthy' if bridge_healthy else 'unhealthy'}")
            return result
        
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'metrics': {'bridge_available': False},
                'issues': [f"Memory bridge check failed: {e}"]
            }
    
    def check_log_system_health(self) -> Dict[str, Any]:
        """Check log system health and rotation"""
        try:
            log_dirs = ['logs/health', 'logs/backup', 'logs/audit', 'logs/perf']
            
            result = {
                'status': 'healthy',
                'metrics': {
                    'log_dirs_exist': 0,
                    'total_log_size_mb': 0,
                    'old_logs_count': 0
                },
                'issues': []
            }
            
            total_size = 0
            old_logs = 0
            cutoff_date = datetime.now() - timedelta(days=30)
            
            for log_dir in log_dirs:
                if os.path.exists(log_dir):
                    result['metrics']['log_dirs_exist'] += 1
                    
                    for root, dirs, files in os.walk(log_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                size = os.path.getsize(file_path)
                                total_size += size
                                
                                # Check file age
                                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                                if mtime < cutoff_date:
                                    old_logs += 1
                            except:
                                pass
            
            result['metrics']['total_log_size_mb'] = total_size / (1024 * 1024)
            result['metrics']['old_logs_count'] = old_logs
            
            # Check for issues
            if result['metrics']['total_log_size_mb'] > 1000:  # 1GB
                result['status'] = 'warning'
                result['issues'].append(f"Large log size: {result['metrics']['total_log_size_mb']:.0f}MB")
            
            if old_logs > 100:
                result['status'] = 'info' if result['status'] == 'healthy' else result['status']
                result['issues'].append(f"Many old logs: {old_logs}")
            
            self.logger.info(f"📝 Log system: {result['metrics']['total_log_size_mb']:.1f}MB total")
            return result
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'metrics': {},
                'issues': [f"Log system check failed: {e}"]
            }
    
    def check_backup_freshness(self) -> Dict[str, Any]:
        """Check backup freshness and availability"""
        try:
            backup_dir = 'backups'
            
            result = {
                'status': 'healthy',
                'metrics': {
                    'backup_dir_exists': os.path.exists(backup_dir),
                    'backup_count': 0,
                    'latest_backup_age_hours': None
                },
                'issues': []
            }
            
            if not os.path.exists(backup_dir):
                result['status'] = 'warning'
                result['issues'].append('Backup directory not found')
                return result
            
            # Find backups
            backup_files = []
            for filename in os.listdir(backup_dir):
                if filename.endswith('.zip') and filename.startswith('backup_'):
                    backup_files.append(filename)
            
            result['metrics']['backup_count'] = len(backup_files)
            
            if backup_files:
                # Find latest backup
                backup_files.sort(reverse=True)
                latest_backup = os.path.join(backup_dir, backup_files[0])
                
                # Check age
                backup_time = datetime.fromtimestamp(os.path.getmtime(latest_backup))
                age_hours = (datetime.now() - backup_time).total_seconds() / 3600
                result['metrics']['latest_backup_age_hours'] = age_hours
                
                if age_hours > self.config['max_backup_age_hours'] * 2:
                    result['status'] = 'critical'
                    result['issues'].append(f"Very old backup: {age_hours:.1f} hours")
                elif age_hours > self.config['max_backup_age_hours']:
                    result['status'] = 'warning'
                    result['issues'].append(f"Old backup: {age_hours:.1f} hours")
            else:
                result['status'] = 'critical'
                result['issues'].append('No backups found')
            
            self.logger.info(f"💾 Backups: {result['metrics']['backup_count']} files")
            return result
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'metrics': {},
                'issues': [f"Backup freshness check failed: {e}"]
            }
    
    def check_data_integrity(self) -> Dict[str, Any]:
        """Basic data integrity checks"""
        if not self.env['supabase_url'] or not self.env['supabase_key']:
            return {
                'status': 'info',
                'metrics': {},
                'issues': ['Data integrity check skipped - no Supabase credentials']
            }
        
        try:
            headers = {
                'apikey': self.env['supabase_key'],
                'Authorization': f"Bearer {self.env['supabase_key']}",
                'Content-Type': 'application/json'
            }
            
            tables_to_check = ['decision_vault', 'memory_log']
            
            result = {
                'status': 'healthy',
                'metrics': {
                    'tables_checked': 0,
                    'total_records': 0,
                    'null_percentages': {}
                },
                'issues': []
            }
            
            for table in tables_to_check:
                try:
                    # Get record count
                    url = f"{self.env['supabase_url']}/rest/v1/{table}"
                    params = {'select': 'id', 'limit': '1000'}
                    
                    response = requests.get(url, headers=headers, params=params, timeout=15)
                    
                    if response.status_code == 200:
                        records = response.json()
                        record_count = len(records)
                        result['metrics']['total_records'] += record_count
                        result['metrics']['tables_checked'] += 1
                        
                        # Check for null values in critical fields
                        if records:
                            null_counts = {}
                            for record in records:
                                for field, value in record.items():
                                    if field not in null_counts:
                                        null_counts[field] = 0
                                    if value is None:
                                        null_counts[field] += 1
                            
                            # Calculate null percentages
                            for field, null_count in null_counts.items():
                                null_percentage = (null_count / record_count) * 100
                                result['metrics']['null_percentages'][f"{table}.{field}"] = null_percentage
                                
                                if null_percentage > 50:
                                    result['status'] = 'warning' if result['status'] == 'healthy' else result['status']
                                    result['issues'].append(f"High null rate in {table}.{field}: {null_percentage:.1f}%")
                
                except Exception as e:
                    result['issues'].append(f"Failed to check {table}: {e}")
            
            self.logger.info(f"🔍 Data integrity: {result['metrics']['tables_checked']} tables, {result['metrics']['total_records']} records")
            return result
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'metrics': {},
                'issues': [f"Data integrity check failed: {e}"]
            }
    
    def check_service_processes(self) -> Dict[str, Any]:
        """Check for running service processes"""
        try:
            result = {
                'status': 'healthy',
                'metrics': {
                    'total_processes': len(psutil.pids()),
                    'python_processes': 0,
                    'high_cpu_processes': 0,
                    'high_memory_processes': 0
                },
                'issues': []
            }
            
            high_cpu_threshold = 20  # %
            high_memory_threshold = 500  # MB
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    if 'python' in proc.info['name'].lower():
                        result['metrics']['python_processes'] += 1
                    
                    if proc.info['cpu_percent'] and proc.info['cpu_percent'] > high_cpu_threshold:
                        result['metrics']['high_cpu_processes'] += 1
                    
                    if proc.info['memory_info'] and proc.info['memory_info'].rss / (1024*1024) > high_memory_threshold:
                        result['metrics']['high_memory_processes'] += 1
                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Check for concerning patterns
            if result['metrics']['high_cpu_processes'] > 5:
                result['status'] = 'warning'
                result['issues'].append(f"Many high-CPU processes: {result['metrics']['high_cpu_processes']}")
            
            if result['metrics']['high_memory_processes'] > 10:
                result['status'] = 'warning' if result['status'] == 'healthy' else result['status']
                result['issues'].append(f"Many high-memory processes: {result['metrics']['high_memory_processes']}")
            
            self.logger.info(f"⚙️ Processes: {result['metrics']['python_processes']} Python processes")
            return result
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'metrics': {},
                'issues': [f"Process check failed: {e}"]
            }
    
    def calculate_overall_score(self) -> int:
        """Calculate overall health score (0-100)"""
        total_checks = len(self.health_checks)
        healthy_checks = 0
        warning_checks = 0
        critical_checks = 0
        
        for check_name, _, _ in self.health_checks:
            if check_name in self.health_results['checks']:
                status = self.health_results['checks'][check_name]['status']
                if status == 'healthy':
                    healthy_checks += 1
                elif status in ['warning', 'info']:
                    warning_checks += 1
                elif status in ['critical', 'error']:
                    critical_checks += 1
        
        # Calculate weighted score
        score = (healthy_checks * 100 + warning_checks * 60) / total_checks
        
        # Penalize critical issues
        if critical_checks > 0:
            score = max(0, score - (critical_checks * 20))
        
        return int(score)
    
    def determine_overall_status(self) -> str:
        """Determine overall system status"""
        has_critical = any(
            self.health_results['checks'][check_name]['status'] in ['critical', 'error']
            for check_name, _, _ in self.health_checks
            if check_name in self.health_results['checks']
        )
        
        has_warning = any(
            self.health_results['checks'][check_name]['status'] in ['warning']
            for check_name, _, _ in self.health_checks
            if check_name in self.health_results['checks']
        )
        
        if has_critical:
            return 'critical'
        elif has_warning:
            return 'warning'
        else:
            return 'healthy'
    
    def generate_recommendations(self):
        """Generate actionable recommendations"""
        recommendations = []
        
        for check_name, _, is_critical in self.health_checks:
            if check_name in self.health_results['checks']:
                check_result = self.health_results['checks'][check_name]
                
                if check_result['status'] == 'critical':
                    if check_name == 'disk_space':
                        recommendations.append("🚨 Free up disk space immediately - consider log cleanup or backup archival")
                    elif check_name == 'system_resources':
                        recommendations.append("🚨 Reduce system load - check for runaway processes or increase resources")
                    elif check_name == 'supabase_connectivity':
                        recommendations.append("🚨 Check Supabase credentials and network connectivity")
                    elif check_name == 'memory_bridge':
                        recommendations.append("🚨 Restart memory bridge service or check Supabase connection")
                
                elif check_result['status'] == 'warning':
                    if check_name == 'backup_freshness':
                        recommendations.append("⚠️ Run manual backup to ensure data protection")
                    elif check_name == 'log_system':
                        recommendations.append("⚠️ Consider log rotation to manage disk usage")
                    elif check_name == 'notion_connectivity':
                        recommendations.append("⚠️ Check Notion API credentials if sync is required")
        
        if not recommendations:
            recommendations.append("✅ System is healthy - continue regular monitoring")
        
        self.health_results['recommendations'] = recommendations
    
    def send_health_alert(self):
        """Send health status alert"""
        if not self.alert_manager:
            return
        
        try:
            status = self.health_results['overall_status']
            score = self.health_results['overall_score']
            critical_count = len(self.health_results['critical_issues'])
            warning_count = len(self.health_results['warnings'])
            
            if status == 'critical':
                title = "🚨 System Health Critical"
                message = f"Critical system health issues detected!\n"
                message += f"• Health score: {score}/100\n"
                message += f"• Critical issues: {critical_count}\n"
                message += f"• Warnings: {warning_count}"
                severity = "critical"
            elif status == 'warning':
                title = "⚠️ System Health Warning"
                message = f"System health warnings detected.\n"
                message += f"• Health score: {score}/100\n"
                message += f"• Warnings: {warning_count}"
                severity = "warning"
            else:
                title = "✅ System Health OK"
                message = f"System health check passed.\n"
                message += f"• Health score: {score}/100"
                severity = "info"
            
            self.alert_manager.send_alert(
                title=title,
                message=message,
                severity=severity,
                tags=['health-check', 'monitoring', 'system']
            )
            
            self.logger.info("📢 Health alert sent")
        
        except Exception as e:
            self.logger.error(f"❌ Failed to send health alert: {e}")
    
    def run_deep_health_check(self) -> Dict[str, Any]:
        """Run complete deep health check"""
        self.logger.info("❤️ Starting deep system health check...")
        self.logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Run all health checks
            for check_name, check_function, is_critical in self.health_checks:
                self.logger.info(f"🔍 Running {check_name} check...")
                
                try:
                    check_result = check_function()
                    self.health_results['checks'][check_name] = check_result
                    
                    # Collect issues
                    if check_result.get('issues'):
                        if check_result['status'] in ['critical', 'error']:
                            self.health_results['critical_issues'].extend(check_result['issues'])
                        elif check_result['status'] == 'warning':
                            self.health_results['warnings'].extend(check_result['issues'])
                    
                    # Log status
                    status_icon = {
                        'healthy': '✅',
                        'warning': '⚠️',
                        'critical': '🚨',
                        'error': '❌',
                        'info': 'ℹ️'
                    }.get(check_result['status'], '❓')
                    
                    self.logger.info(f"   {status_icon} {check_name}: {check_result['status']}")
                    
                    if check_result.get('issues'):
                        for issue in check_result['issues'][:3]:  # Show first 3 issues
                            self.logger.info(f"      • {issue}")
                
                except Exception as e:
                    self.logger.error(f"❌ {check_name} check failed: {e}")
                    self.health_results['checks'][check_name] = {
                        'status': 'error',
                        'error': str(e),
                        'metrics': {},
                        'issues': [f"Check execution failed: {e}"]
                    }
                    self.health_results['critical_issues'].append(f"{check_name} check failed: {e}")
            
            # Calculate overall results
            self.health_results['overall_score'] = self.calculate_overall_score()
            self.health_results['overall_status'] = self.determine_overall_status()
            
            # Generate recommendations
            self.generate_recommendations()
            
            # Calculate duration
            duration = datetime.now() - start_time
            self.health_results['duration_seconds'] = duration.total_seconds()
            
            # Send alerts
            self.send_health_alert()
            
            # Save detailed health snapshot
            self.save_health_snapshot()
            
            # Final summary
            self.logger.info("\n" + "=" * 60)
            self.logger.info("🏁 DEEP HEALTH CHECK COMPLETE")
            self.logger.info("=" * 60)
            self.logger.info(f"📊 SUMMARY:")
            self.logger.info(f"   Overall Status: {self.health_results['overall_status'].upper()}")
            self.logger.info(f"   Health Score: {self.health_results['overall_score']}/100")
            self.logger.info(f"   Checks Run: {len(self.health_results['checks'])}")
            self.logger.info(f"   Critical Issues: {len(self.health_results['critical_issues'])}")
            self.logger.info(f"   Warnings: {len(self.health_results['warnings'])}")
            self.logger.info(f"   Duration: {self.health_results['duration_seconds']:.1f} seconds")
            
            if self.health_results['critical_issues']:
                self.logger.error("🚨 CRITICAL ISSUES:")
                for issue in self.health_results['critical_issues']:
                    self.logger.error(f"   • {issue}")
            
            if self.health_results['warnings']:
                self.logger.warning("⚠️ WARNINGS:")
                for warning in self.health_results['warnings']:
                    self.logger.warning(f"   • {warning}")
            
            if self.health_results['recommendations']:
                self.logger.info("💡 RECOMMENDATIONS:")
                for rec in self.health_results['recommendations']:
                    self.logger.info(f"   • {rec}")
            
            self.logger.info("=" * 60)
            
            return self.health_results
        
        except Exception as e:
            self.health_results['overall_status'] = 'error'
            self.health_results['critical_issues'].append(f"Health check system failed: {e}")
            self.logger.error(f"💥 Health check system failed: {e}")
            return self.health_results
    
    def save_health_snapshot(self):
        """Save detailed health snapshot"""
        try:
            snapshot_file = f"logs/health/health_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(snapshot_file, 'w') as f:
                json.dump(self.health_results, f, indent=2, default=str)
            
            self.logger.info(f"📸 Health snapshot saved: {snapshot_file}")
        
        except Exception as e:
            self.logger.error(f"❌ Failed to save health snapshot: {e}")

def main():
    """Main entry point for health check system"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deep Health Check System')
    parser.add_argument('--run', action='store_true', help='Run deep health check')
    parser.add_argument('--quick', action='store_true', help='Run only critical checks')
    parser.add_argument('--no-alerts', action='store_true', help='Disable alert notifications')
    parser.add_argument('--save-snapshot', action='store_true', help='Save detailed health snapshot')
    
    args = parser.parse_args()
    
    try:
        health_system = DeepHealthCheckSystem()
        
        # Override configuration based on args
        if args.no_alerts:
            health_system.alert_manager = None
        
        if args.quick:
            # Only run critical checks
            health_system.health_checks = [
                (name, func, critical) for name, func, critical in health_system.health_checks if critical
            ]
        
        if args.run or not any(vars(args).values()):
            results = health_system.run_deep_health_check()
            
            # Exit codes based on health status
            if results['overall_status'] == 'healthy':
                sys.exit(0)
            elif results['overall_status'] == 'warning':
                sys.exit(1)
            else:
                sys.exit(2)
        
    except KeyboardInterrupt:
        print("\n🛑 Health check interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Health check system failure: {e}")
        sys.exit(255)

if __name__ == "__main__":
    main()