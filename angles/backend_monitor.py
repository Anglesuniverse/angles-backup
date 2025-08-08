"""
Backend Monitor for Angles AI Universe™
Health checks and system monitoring
"""

import logging
import psutil
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any

from .config import print_config_status, has_supabase, has_openai, has_notion, has_github
from .supabase_client import SupabaseClient
from .openai_bridge import OpenAIBridge


logger = logging.getLogger(__name__)


class BackendMonitor:
    """System health monitoring and alerts"""
    
    def __init__(self):
        self.db = None
        self.openai = None
        self.health_status = {
            'overall': 'unknown',
            'timestamp': None,
            'checks': {},
            'recommendations': []
        }
        
        # Initialize available services
        if has_supabase():
            self.db = SupabaseClient()
        
        if has_openai():
            self.openai = OpenAIBridge()
    
    def check_database_connectivity(self) -> Dict[str, Any]:
        """Check database connection and recent activity"""
        result = {
            'name': 'Database Connectivity',
            'status': 'unknown',
            'details': {},
            'critical': True
        }
        
        if not self.db:
            result['status'] = 'unavailable'
            result['details']['message'] = 'Database not configured'
            result['critical'] = True
            return result
        
        try:
            # Test connection
            if self.db.test_connection():
                result['status'] = 'healthy'
                result['details']['connection'] = 'OK'
                
                # Check recent activity
                recent_logs = self.db.get_recent_logs(hours=1)
                result['details']['recent_logs'] = len(recent_logs)
                
                if len(recent_logs) == 0:
                    result['details']['warning'] = 'No recent activity'
                
            else:
                result['status'] = 'failed'
                result['details']['connection'] = 'FAILED'
                
        except Exception as e:
            result['status'] = 'error'
            result['details']['error'] = str(e)
        
        return result
    
    def check_memory_sync_activity(self) -> Dict[str, Any]:
        """Check memory sync last run time"""
        result = {
            'name': 'Memory Sync Activity',
            'status': 'unknown',
            'details': {},
            'critical': False
        }
        
        if not self.db:
            result['status'] = 'unavailable'
            return result
        
        try:
            # Look for recent memory sync logs
            recent_logs = self.db.get_recent_logs(hours=8, level='INFO')
            sync_logs = [log for log in recent_logs if 'memory_sync' in log.get('component', '').lower()]
            
            if sync_logs:
                last_sync = sync_logs[0]  # Most recent
                result['status'] = 'healthy'
                result['details']['last_sync'] = last_sync.get('ts')
                result['details']['recent_syncs'] = len(sync_logs)
            else:
                result['status'] = 'stale'
                result['details']['message'] = 'No memory sync activity in last 8 hours'
                
        except Exception as e:
            result['status'] = 'error'
            result['details']['error'] = str(e)
        
        return result
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        result = {
            'name': 'System Resources',
            'status': 'unknown',
            'details': {},
            'critical': False
        }
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            result['details']['cpu_percent'] = cpu_percent
            
            # Memory usage
            memory = psutil.virtual_memory()
            result['details']['memory_percent'] = memory.percent
            result['details']['memory_available_gb'] = round(memory.available / (1024**3), 2)
            
            # Disk usage
            disk = psutil.disk_usage('.')
            result['details']['disk_percent'] = round((disk.used / disk.total) * 100, 1)
            result['details']['disk_free_gb'] = round(disk.free / (1024**3), 2)
            
            # Determine status based on thresholds
            if cpu_percent > 80 or memory.percent > 85 or disk.used / disk.total > 0.9:
                result['status'] = 'warning'
                result['details']['message'] = 'High resource usage detected'
            else:
                result['status'] = 'healthy'
            
        except Exception as e:
            result['status'] = 'error'
            result['details']['error'] = str(e)
        
        return result
    
    def check_openai_connectivity(self) -> Dict[str, Any]:
        """Check OpenAI API connectivity"""
        result = {
            'name': 'OpenAI API',
            'status': 'unknown',
            'details': {},
            'critical': False
        }
        
        if not self.openai or not self.openai.is_available():
            result['status'] = 'unavailable'
            result['details']['message'] = 'OpenAI not configured'
            return result
        
        try:
            # Test API call
            test_response = self.openai.analyze_text("System health check - respond with 'OK'")
            
            if 'OK' in test_response.upper():
                result['status'] = 'healthy'
                result['details']['api_response'] = 'OK'
            else:
                result['status'] = 'warning'
                result['details']['api_response'] = test_response[:100]
                
        except Exception as e:
            result['status'] = 'error'
            result['details']['error'] = str(e)
        
        return result
    
    def check_integration_status(self) -> Dict[str, Any]:
        """Check status of all integrations"""
        result = {
            'name': 'Integration Status',
            'status': 'healthy',
            'details': {},
            'critical': False
        }
        
        integrations = {
            'supabase': has_supabase(),
            'notion': has_notion(), 
            'openai': has_openai(),
            'github': has_github()
        }
        
        result['details']['integrations'] = integrations
        result['details']['available_count'] = sum(integrations.values())
        result['details']['total_count'] = len(integrations)
        
        # At least Supabase should be available
        if not integrations['supabase']:
            result['status'] = 'critical'
            result['details']['message'] = 'Critical integration (Supabase) missing'
        
        return result
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        logger.info("🏥 Running system health checks")
        
        checks = [
            self.check_database_connectivity(),
            self.check_memory_sync_activity(),
            self.check_system_resources(),
            self.check_openai_connectivity(),
            self.check_integration_status()
        ]
        
        # Determine overall status
        critical_failed = any(check['status'] in ['failed', 'critical'] and check['critical'] for check in checks)
        any_failed = any(check['status'] in ['failed', 'error', 'critical'] for check in checks)
        any_warning = any(check['status'] == 'warning' for check in checks)
        
        if critical_failed:
            overall_status = 'critical'
        elif any_failed:
            overall_status = 'degraded'
        elif any_warning:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        self.health_status = {
            'overall': overall_status,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': {check['name']: check for check in checks},
            'recommendations': self.generate_recommendations(checks)
        }
        
        return self.health_status
    
    def generate_recommendations(self, checks: List[Dict]) -> List[str]:
        """Generate health recommendations"""
        recommendations = []
        
        for check in checks:
            if check['status'] == 'failed':
                if 'Database' in check['name']:
                    recommendations.append("Check SUPABASE_URL and SUPABASE_KEY environment variables")
                elif 'Memory Sync' in check['name']:
                    recommendations.append("Run memory sync manually: python -m angles.memory_sync_agent")
                elif 'OpenAI' in check['name']:
                    recommendations.append("Verify OPENAI_API_KEY environment variable")
            
            elif check['status'] == 'warning':
                if 'Resources' in check['name']:
                    if check['details'].get('cpu_percent', 0) > 80:
                        recommendations.append("High CPU usage - consider optimizing processes")
                    if check['details'].get('memory_percent', 0) > 85:
                        recommendations.append("High memory usage - restart services if needed")
                    if check['details'].get('disk_percent', 0) > 90:
                        recommendations.append("Low disk space - clean up old logs and backups")
        
        return recommendations
    
    def print_health_report(self):
        """Print detailed health report"""
        status = self.health_status
        
        print("\n🏥 ANGLES AI UNIVERSE™ HEALTH REPORT")
        print("=" * 50)
        print(f"Overall Status: {self.get_status_emoji(status['overall'])} {status['overall'].upper()}")
        print(f"Timestamp: {status['timestamp']}")
        print("\nComponent Status:")
        
        for name, check in status['checks'].items():
            emoji = self.get_status_emoji(check['status'])
            critical_marker = " (CRITICAL)" if check.get('critical') and check['status'] in ['failed', 'error'] else ""
            print(f"  {emoji} {name}{critical_marker}")
            
            # Show key details
            if 'cpu_percent' in check['details']:
                print(f"     CPU: {check['details']['cpu_percent']:.1f}%")
                print(f"     Memory: {check['details']['memory_percent']:.1f}%")
                print(f"     Disk: {check['details']['disk_percent']:.1f}%")
            elif 'connection' in check['details']:
                print(f"     Connection: {check['details']['connection']}")
            elif 'last_sync' in check['details']:
                print(f"     Last sync: {check['details']['last_sync']}")
        
        if status['recommendations']:
            print("\nRecommendations:")
            for i, rec in enumerate(status['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        print("=" * 50)
    
    def get_status_emoji(self, status: str) -> str:
        """Get emoji for status"""
        return {
            'healthy': '✅',
            'warning': '⚠️',
            'degraded': '🔶',
            'critical': '❌',
            'failed': '❌',
            'error': '❌',
            'unavailable': 'ℹ️',
            'unknown': '❓'
        }.get(status, '❓')
    
    def run_monitor(self) -> bool:
        """Run complete monitoring cycle"""
        logger.info("🚀 Starting Backend Monitor")
        print_config_status()
        
        # Run health checks
        health_status = self.run_health_checks()
        
        # Print report
        self.print_health_report()
        
        # Log to database if available
        if self.db:
            try:
                self.db.log_system_event(
                    level='INFO' if health_status['overall'] in ['healthy', 'warning'] else 'ERROR',
                    component='backend_monitor',
                    message=f'Health check completed - Status: {health_status["overall"]}',
                    meta=health_status
                )
            except Exception as e:
                logger.error(f"Failed to log health status: {e}")
        
        return health_status['overall'] in ['healthy', 'warning']


def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    monitor = BackendMonitor()
    success = monitor.run_monitor()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())