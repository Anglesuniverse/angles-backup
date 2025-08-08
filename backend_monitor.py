#!/usr/bin/env python3
"""
Angles AI Universe™ Backend Monitor
Health monitoring and self-healing system

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import logging
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

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
    """Setup logging for backend monitor"""
    os.makedirs("logs/active", exist_ok=True)
    
    logger = logging.getLogger('backend_monitor')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler
    file_handler = logging.FileHandler('logs/active/system_health.log')
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

class BackendMonitor:
    """Comprehensive backend health monitoring"""
    
    def __init__(self):
        self.logger = setup_logging()
        
        # Health check results
        self.health_report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'overall_status': 'unknown',
            'checks': {},
            'critical_failures': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Thresholds
        self.thresholds = {
            'cpu_warning': 80,      # %
            'cpu_critical': 95,     # %
            'memory_warning': 80,   # %
            'memory_critical': 95,  # %
            'disk_warning': 85,     # %
            'disk_critical': 95     # %
        }
    
    def check_environment_variables(self) -> Dict[str, Any]:
        """Check required environment variables"""
        self.logger.info("🔧 Checking environment variables...")
        
        required_vars = {
            'SUPABASE_URL': 'Supabase database URL',
            'SUPABASE_KEY': 'Supabase API key',
            'NOTION_TOKEN': 'Notion integration token (or NOTION_API_KEY)',
            'NOTION_DATABASE_ID': 'Notion database ID',
            'GITHUB_TOKEN': 'GitHub personal access token',
            'REPO_URL': 'GitHub repository URL',
            'GIT_USERNAME': 'Git username',
            'GIT_EMAIL': 'Git email'
        }
        
        results = {}
        missing_critical = []
        
        for var_name, description in required_vars.items():
            value = os.getenv(var_name)
            
            # Handle alternative Notion token name
            if var_name == 'NOTION_TOKEN' and not value:
                value = os.getenv('NOTION_API_KEY')
            
            if value:
                # Mask sensitive values for logging
                if any(keyword in var_name.lower() for keyword in ['key', 'token', 'secret']):
                    display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                else:
                    display_value = value
                
                results[var_name] = {
                    'status': 'ok',
                    'value': display_value,
                    'description': description
                }
                self.logger.info(f"   ✅ {var_name}: {display_value}")
            else:
                results[var_name] = {
                    'status': 'missing',
                    'value': None,
                    'description': description
                }
                self.logger.error(f"   ❌ {var_name}: Missing")
                
                # Mark critical vs warning
                if var_name in ['SUPABASE_URL', 'SUPABASE_KEY']:
                    missing_critical.append(var_name)
        
        # Optional variables
        optional_vars = ['OPENAI_API_KEY']
        for var_name in optional_vars:
            value = os.getenv(var_name)
            if value:
                display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                results[var_name] = {
                    'status': 'ok',
                    'value': display_value,
                    'description': 'OpenAI API key (optional)'
                }
                self.logger.info(f"   ✅ {var_name}: {display_value}")
            else:
                results[var_name] = {
                    'status': 'optional',
                    'value': None,
                    'description': 'OpenAI API key (optional)'
                }
                self.logger.info(f"   ⚪ {var_name}: Not set (optional)")
        
        status = 'critical' if missing_critical else ('warning' if any(r['status'] == 'missing' for r in results.values()) else 'ok')
        
        return {
            'status': status,
            'variables': results,
            'missing_critical': missing_critical,
            'summary': f"{len([r for r in results.values() if r['status'] == 'ok'])}/{len(results)} configured"
        }
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Check Python dependencies"""
        self.logger.info("📦 Checking Python dependencies...")
        
        required_packages = [
            'requests', 'python-dotenv', 'supabase', 'pydantic', 'notion-client'
        ]
        
        recommended_packages = [
            'psutil', 'schedule', 'httpx', 'watchdog', 'typing-extensions'
        ]
        
        results = {}
        missing_required = []
        missing_recommended = []
        
        # Check required packages
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                results[package] = {'status': 'ok', 'type': 'required'}
                self.logger.info(f"   ✅ {package}: Available")
            except ImportError:
                results[package] = {'status': 'missing', 'type': 'required'}
                missing_required.append(package)
                self.logger.error(f"   ❌ {package}: Missing (required)")
        
        # Check recommended packages
        for package in recommended_packages:
            try:
                __import__(package.replace('-', '_'))
                results[package] = {'status': 'ok', 'type': 'recommended'}
                self.logger.info(f"   ✅ {package}: Available")
            except ImportError:
                results[package] = {'status': 'missing', 'type': 'recommended'}
                missing_recommended.append(package)
                self.logger.warning(f"   ⚠️ {package}: Missing (recommended)")
        
        status = 'critical' if missing_required else ('warning' if missing_recommended else 'ok')
        
        return {
            'status': status,
            'packages': results,
            'missing_required': missing_required,
            'missing_recommended': missing_recommended,
            'summary': f"{len([r for r in results.values() if r['status'] == 'ok'])}/{len(results)} available"
        }
    
    def check_system_metrics(self) -> Dict[str, Any]:
        """Check system performance metrics"""
        self.logger.info("📊 Checking system metrics...")
        
        if not PSUTIL_AVAILABLE:
            self.logger.warning("⚠️ psutil not available - system metrics disabled")
            return {
                'status': 'warning',
                'error': 'psutil not available',
                'summary': 'System metrics unavailable'
            }
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_status = 'critical' if cpu_percent > self.thresholds['cpu_critical'] else \
                        'warning' if cpu_percent > self.thresholds['cpu_warning'] else 'ok'
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_status = 'critical' if memory.percent > self.thresholds['memory_critical'] else \
                           'warning' if memory.percent > self.thresholds['memory_warning'] else 'ok'
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_status = 'critical' if disk_percent > self.thresholds['disk_critical'] else \
                         'warning' if disk_percent > self.thresholds['disk_warning'] else 'ok'
            
            # Load average (Linux/Mac only)
            load_avg = None
            try:
                load_avg = os.getloadavg()
            except (OSError, AttributeError):
                pass
            
            metrics = {
                'cpu': {
                    'percent': cpu_percent,
                    'status': cpu_status,
                    'threshold_warning': self.thresholds['cpu_warning'],
                    'threshold_critical': self.thresholds['cpu_critical']
                },
                'memory': {
                    'percent': memory.percent,
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'status': memory_status,
                    'threshold_warning': self.thresholds['memory_warning'],
                    'threshold_critical': self.thresholds['memory_critical']
                },
                'disk': {
                    'percent': round(disk_percent, 2),
                    'total_gb': round(disk.total / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'status': disk_status,
                    'threshold_warning': self.thresholds['disk_warning'],
                    'threshold_critical': self.thresholds['disk_critical']
                }
            }
            
            if load_avg:
                metrics['load_average'] = {
                    '1min': load_avg[0],
                    '5min': load_avg[1],
                    '15min': load_avg[2],
                    'status': 'warning' if load_avg[0] > 2.0 else 'ok'
                }
            
            # Overall status
            overall_status = 'critical' if any(m.get('status') == 'critical' for m in metrics.values()) else \
                            'warning' if any(m.get('status') == 'warning' for m in metrics.values()) else 'ok'
            
            # Log results
            self.logger.info(f"   📊 CPU: {cpu_percent:.1f}% ({cpu_status})")
            self.logger.info(f"   💾 Memory: {memory.percent:.1f}% ({memory_status})")
            self.logger.info(f"   💿 Disk: {disk_percent:.1f}% ({disk_status})")
            
            return {
                'status': overall_status,
                'metrics': metrics,
                'summary': f"CPU:{cpu_percent:.1f}% MEM:{memory.percent:.1f}% DISK:{disk_percent:.1f}%"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error checking system metrics: {e}")
            return {
                'status': 'critical',
                'error': str(e),
                'summary': 'System metrics check failed'
            }
    
    def check_services(self) -> Dict[str, Any]:
        """Check core services"""
        self.logger.info("🔧 Checking core services...")
        
        services = {
            'migration': {
                'command': [sys.executable, 'run_migration.py', '--dry-run'],
                'timeout': 30,
                'description': 'Database migration'
            },
            'memory_sync': {
                'command': [sys.executable, 'memory_sync.py', '--test'],
                'timeout': 30,
                'description': 'Memory sync to Notion'
            },
            'autosync': {
                'command': [sys.executable, 'autosync_files.py', '--once', '--dry-run'],
                'timeout': 30,
                'description': 'File change detection'
            }
        }
        
        results = {}
        failed_services = []
        
        for service_name, config in services.items():
            try:
                self.logger.info(f"   🔍 Testing {config['description']}...")
                
                result = subprocess.run(
                    config['command'],
                    capture_output=True,
                    text=True,
                    timeout=config['timeout']
                )
                
                if result.returncode == 0:
                    results[service_name] = {
                        'status': 'ok',
                        'description': config['description'],
                        'message': 'Service check passed'
                    }
                    self.logger.info(f"   ✅ {config['description']}: OK")
                else:
                    results[service_name] = {
                        'status': 'failed',
                        'description': config['description'],
                        'error': result.stderr or result.stdout,
                        'exit_code': result.returncode
                    }
                    failed_services.append(service_name)
                    self.logger.error(f"   ❌ {config['description']}: Failed (exit {result.returncode})")
                
            except subprocess.TimeoutExpired:
                results[service_name] = {
                    'status': 'timeout',
                    'description': config['description'],
                    'error': f"Timeout after {config['timeout']}s"
                }
                failed_services.append(service_name)
                self.logger.error(f"   ⏱️ {config['description']}: Timeout")
                
            except Exception as e:
                results[service_name] = {
                    'status': 'error',
                    'description': config['description'],
                    'error': str(e)
                }
                failed_services.append(service_name)
                self.logger.error(f"   💥 {config['description']}: Error - {e}")
        
        status = 'critical' if failed_services else 'ok'
        
        return {
            'status': status,
            'services': results,
            'failed_services': failed_services,
            'summary': f"{len(results) - len(failed_services)}/{len(results)} services OK"
        }
    
    def check_github_connectivity(self) -> Dict[str, Any]:
        """Check GitHub connectivity"""
        self.logger.info("🐙 Checking GitHub connectivity...")
        
        repo_url = os.getenv('REPO_URL')
        github_token = os.getenv('GITHUB_TOKEN')
        
        if not repo_url or not github_token:
            return {
                'status': 'warning',
                'error': 'GitHub not configured',
                'summary': 'GitHub credentials missing'
            }
        
        try:
            # Extract repo info from URL
            if 'github.com' in repo_url:
                repo_path = repo_url.split('github.com/')[-1].replace('.git', '')
                api_url = f"https://api.github.com/repos/{repo_path}"
                
                response = requests.get(
                    api_url,
                    headers={'Authorization': f'token {github_token}'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.logger.info("   ✅ GitHub: Connected")
                    return {
                        'status': 'ok',
                        'repo_url': repo_url,
                        'summary': 'GitHub connectivity OK'
                    }
                else:
                    self.logger.error(f"   ❌ GitHub: API error {response.status_code}")
                    return {
                        'status': 'failed',
                        'error': f"API error {response.status_code}",
                        'summary': 'GitHub API unreachable'
                    }
            else:
                self.logger.warning("   ⚠️ GitHub: Non-GitHub URL, skipping API test")
                return {
                    'status': 'warning',
                    'message': 'Non-GitHub repository',
                    'summary': 'GitHub check skipped'
                }
                
        except Exception as e:
            self.logger.error(f"   ❌ GitHub: Connection error - {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'summary': 'GitHub connectivity failed'
            }
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on health check results"""
        recommendations = []
        
        # Environment variables
        env_check = self.health_report['checks'].get('environment', {})
        if env_check.get('status') == 'critical':
            recommendations.append("Configure missing critical environment variables (SUPABASE_URL, SUPABASE_KEY)")
        
        # Dependencies
        deps_check = self.health_report['checks'].get('dependencies', {})
        if deps_check.get('missing_required'):
            missing = ', '.join(deps_check['missing_required'])
            recommendations.append(f"Install missing required packages: {missing}")
        if deps_check.get('missing_recommended'):
            missing = ', '.join(deps_check['missing_recommended'])
            recommendations.append(f"Install recommended packages for full functionality: {missing}")
        
        # System metrics
        metrics_check = self.health_report['checks'].get('system_metrics', {})
        if metrics_check.get('status') == 'critical':
            recommendations.append("System resources critically low - consider scaling up or optimizing workload")
        elif metrics_check.get('status') == 'warning':
            recommendations.append("System resources high - monitor usage and consider optimization")
        
        # Services
        services_check = self.health_report['checks'].get('services', {})
        if services_check.get('failed_services'):
            failed = ', '.join(services_check['failed_services'])
            recommendations.append(f"Fix failing services: {failed}")
        
        return recommendations
    
    def save_health_report(self) -> bool:
        """Save health report to JSON file"""
        try:
            health_file = "logs/active/system_health.json"
            
            with open(health_file, 'w') as f:
                json.dump(self.health_report, f, indent=2, default=str)
            
            self.logger.info(f"💾 Health report saved: {health_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error saving health report: {e}")
            return False
    
    def run_health_check(self) -> bool:
        """Run complete health check"""
        self.logger.info("🏥 Starting Angles AI Universe™ Backend Health Check")
        self.logger.info("=" * 60)
        
        # Run all checks
        self.health_report['checks']['environment'] = self.check_environment_variables()
        self.health_report['checks']['dependencies'] = self.check_dependencies()
        self.health_report['checks']['system_metrics'] = self.check_system_metrics()
        self.health_report['checks']['services'] = self.check_services()
        self.health_report['checks']['github'] = self.check_github_connectivity()
        
        # Determine overall status
        check_statuses = [check.get('status', 'unknown') for check in self.health_report['checks'].values()]
        
        if 'critical' in check_statuses:
            self.health_report['overall_status'] = 'critical'
        elif 'failed' in check_statuses:
            self.health_report['overall_status'] = 'failed'
        elif 'warning' in check_statuses:
            self.health_report['overall_status'] = 'warning'
        else:
            self.health_report['overall_status'] = 'healthy'
        
        # Collect critical failures and warnings
        for check_name, check_result in self.health_report['checks'].items():
            if check_result.get('status') == 'critical':
                self.health_report['critical_failures'].append(f"{check_name}: {check_result.get('summary', 'Critical failure')}")
            elif check_result.get('status') in ['warning', 'failed']:
                self.health_report['warnings'].append(f"{check_name}: {check_result.get('summary', 'Warning or failure')}")
        
        # Generate recommendations
        self.health_report['recommendations'] = self.generate_recommendations()
        
        # Print summary
        self.logger.info("=" * 60)
        self.logger.info("🏥 HEALTH CHECK SUMMARY")
        self.logger.info("=" * 60)
        
        status_icon = {
            'healthy': '✅',
            'warning': '⚠️',
            'failed': '❌',
            'critical': '🚨'
        }.get(self.health_report['overall_status'], '❓')
        
        self.logger.info(f"Overall Status: {status_icon} {self.health_report['overall_status'].upper()}")
        
        if self.health_report['critical_failures']:
            self.logger.error("🚨 Critical Failures:")
            for failure in self.health_report['critical_failures']:
                self.logger.error(f"   • {failure}")
        
        if self.health_report['warnings']:
            self.logger.warning("⚠️ Warnings:")
            for warning in self.health_report['warnings']:
                self.logger.warning(f"   • {warning}")
        
        if self.health_report['recommendations']:
            self.logger.info("💡 Recommendations:")
            for rec in self.health_report['recommendations']:
                self.logger.info(f"   • {rec}")
        
        # Save report
        self.save_health_report()
        
        # Return success if no critical failures
        return self.health_report['overall_status'] != 'critical'

def main():
    """Main entry point"""
    try:
        monitor = BackendMonitor()
        success = monitor.run_health_check()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"💥 Backend monitor failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()