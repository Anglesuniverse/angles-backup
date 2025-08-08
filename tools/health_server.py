#!/usr/bin/env python3
"""
Angles AI Universe™ Hardened Health Dashboard Server
Stable JSON snapshots and comprehensive health monitoring
Built-in HTTP server with auto-refresh dashboard

Author: Angles AI Universe™ Backend Team
Version: 2.0.0
"""

import os
import json
import sys
import threading
import time
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import health status loader (with fallback)
try:
    from sync.logging_util import load_health_status
except ImportError:
    def load_health_status(path: str) -> Optional[Dict[str, Any]]:
        """Fallback health status loader"""
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return None


class HealthDashboardServer:
    """Hardened health dashboard server with stable JSON snapshots"""
    
    def __init__(self, port: int = 5000):
        """Initialize health dashboard server"""
        self.port = port
        self.setup_logging()
        self.snapshot_interval = 300  # 5 minutes
        self.last_snapshot_time = None
        self.cached_status = None
        
        # Ensure directories exist
        os.makedirs("logs/health", exist_ok=True)
        os.makedirs("logs/active", exist_ok=True)
        
        self.logger.info(f"🏥 Health Dashboard Server initialized on port {port}")
        
        # Start background snapshot thread
        self.snapshot_thread = threading.Thread(target=self._snapshot_loop, daemon=True)
        self.snapshot_thread.start()
    
    def setup_logging(self):
        """Setup logging for health server"""
        self.logger = logging.getLogger('health_server')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/active/health_server.log"
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
    
    def _snapshot_loop(self):
        """Background thread for generating health snapshots"""
        while True:
            try:
                self._generate_health_snapshot()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"❌ Snapshot loop error: {str(e)}")
                time.sleep(30)  # Retry in 30 seconds on error
    
    def _generate_health_snapshot(self):
        """Generate comprehensive health snapshot"""
        now = datetime.now(timezone.utc)
        
        # Generate snapshot every 5 minutes or if none exists
        if (self.last_snapshot_time is None or 
            (now - self.last_snapshot_time).total_seconds() >= self.snapshot_interval):
            
            self.logger.info("📸 Generating health snapshot...")
            
            try:
                snapshot = self._collect_comprehensive_status()
                
                # Save snapshot
                timestamp = now.strftime('%Y%m%d_%H%M%S')
                snapshot_file = f"logs/health/snapshot_{timestamp}.json"
                
                with open(snapshot_file, 'w') as f:
                    json.dump(snapshot, f, indent=2, default=str)
                
                # Update cached status
                self.cached_status = snapshot
                self.last_snapshot_time = now
                
                # Save latest snapshot for quick access
                with open("logs/health/latest_snapshot.json", 'w') as f:
                    json.dump(snapshot, f, indent=2, default=str)
                
                self.logger.info(f"✅ Health snapshot saved: {snapshot_file}")
                
                # Cleanup old snapshots (keep 24 hours worth)
                self._cleanup_old_snapshots()
                
            except Exception as e:
                self.logger.error(f"❌ Failed to generate health snapshot: {str(e)}")
    
    def _collect_comprehensive_status(self) -> Dict[str, Any]:
        """Collect comprehensive system status"""
        status = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'server_uptime': self._get_server_uptime(),
            'sync_status': self._get_sync_status(),
            'scheduler_status': self._get_scheduler_status(),
            'backup_status': self._get_backup_status(),
            'alert_status': self._get_recent_alerts(),
            'system_metrics': self._get_system_metrics(),
            'health_score': 0
        }
        
        # Calculate health score
        status['health_score'] = self._calculate_health_score(status)
        
        return status
    
    def _get_server_uptime(self) -> str:
        """Get server uptime information"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                uptime_str = str(timedelta(seconds=int(uptime_seconds)))
                return uptime_str
        except:
            return "Unknown"
    
    def _get_sync_status(self) -> Dict[str, Any]:
        """Get sync status from health files"""
        sync_status = {
            'last_run': None,
            'status': 'unknown',
            'statistics': {},
            'error_details': []
        }
        
        # Check multiple possible health files
        health_files = [
            "logs/last_success.json",
            "logs/health/latest_snapshot.json",
            "logs/active/sync_health.json"
        ]
        
        for health_file in health_files:
            health_data = load_health_status(health_file)
            if health_data:
                sync_status.update(health_data)
                break
        
        return sync_status
    
    def _get_scheduler_status(self) -> Dict[str, Any]:
        """Get operations scheduler status"""
        scheduler_status = {
            'running': False,
            'last_health_check': None,
            'last_backup': None,
            'next_scheduled': {}
        }
        
        try:
            # Check if ops scheduler log exists
            ops_log = "logs/active/ops_scheduler.log"
            if os.path.exists(ops_log):
                # Get last few lines to check if running
                with open(ops_log, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1]
                        # Check if recent activity (within last 10 minutes)
                        if 'Starting' in last_line or 'Time for' in last_line:
                            scheduler_status['running'] = True
        except Exception as e:
            self.logger.warning(f"⚠️ Could not check scheduler status: {e}")
        
        return scheduler_status
    
    def _get_backup_status(self) -> Dict[str, Any]:
        """Get backup operation status"""
        backup_status = {
            'last_backup': None,
            'backup_count_today': 0,
            'last_backup_size': None,
            'backup_errors': []
        }
        
        try:
            # Check backup logs
            backup_log = "logs/active/backup.log"
            if os.path.exists(backup_log):
                with open(backup_log, 'r') as f:
                    content = f.read()
                    # Count today's backups
                    today = datetime.now().strftime('%Y-%m-%d')
                    backup_status['backup_count_today'] = content.count(today)
        except Exception as e:
            self.logger.warning(f"⚠️ Could not check backup status: {e}")
        
        return backup_status
    
    def _get_recent_alerts(self) -> Dict[str, Any]:
        """Get recent alerts from alert logs"""
        alert_status = {
            'alerts_today': 0,
            'critical_alerts': 0,
            'last_alert': None
        }
        
        try:
            # Check today's alert file
            today = datetime.now().strftime('%Y-%m-%d')
            alert_file = f"logs/alerts/alerts_{today}.json"
            
            if os.path.exists(alert_file):
                with open(alert_file, 'r') as f:
                    alerts = json.load(f)
                    alert_status['alerts_today'] = len(alerts)
                    
                    # Count critical alerts
                    critical_count = sum(1 for alert in alerts if alert.get('severity') == 'critical')
                    alert_status['critical_alerts'] = critical_count
                    
                    # Get last alert
                    if alerts:
                        alert_status['last_alert'] = alerts[-1]
        except Exception as e:
            self.logger.warning(f"⚠️ Could not check alert status: {e}")
        
        return alert_status
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get basic system metrics"""
        metrics = {
            'disk_usage': None,
            'log_file_count': 0,
            'active_workflows': 0
        }
        
        try:
            # Get disk usage for logs directory
            if os.path.exists("logs"):
                total_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                               for dirpath, dirnames, filenames in os.walk("logs")
                               for filename in filenames)
                metrics['disk_usage'] = f"{total_size / (1024*1024):.1f} MB"
                
                # Count log files
                log_count = sum(len(filenames) for dirpath, dirnames, filenames in os.walk("logs"))
                metrics['log_file_count'] = log_count
        except Exception as e:
            self.logger.warning(f"⚠️ Could not get system metrics: {e}")
        
        return metrics
    
    def _calculate_health_score(self, status: Dict) -> int:
        """Calculate overall health score (0-100)"""
        score = 100
        
        # Deduct points for issues
        sync_status = status.get('sync_status', {})
        if sync_status.get('status') == 'error':
            score -= 30
        elif sync_status.get('status') == 'unknown':
            score -= 15
        
        alert_status = status.get('alert_status', {})
        critical_alerts = alert_status.get('critical_alerts', 0)
        score -= critical_alerts * 20  # -20 per critical alert
        
        total_alerts = alert_status.get('alerts_today', 0)
        score -= min(total_alerts * 5, 25)  # -5 per alert, max -25
        
        scheduler_status = status.get('scheduler_status', {})
        if not scheduler_status.get('running', False):
            score -= 20
        
        return max(0, score)
    
    def _cleanup_old_snapshots(self):
        """Clean up old snapshot files (keep 24 hours)"""
        try:
            snapshot_dir = Path("logs/health")
            if not snapshot_dir.exists():
                return
            
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            
            for snapshot_file in snapshot_dir.glob("snapshot_*.json"):
                if snapshot_file.stat().st_mtime < cutoff_time.timestamp():
                    snapshot_file.unlink()
                    self.logger.info(f"🗑️ Cleaned up old snapshot: {snapshot_file.name}")
        except Exception as e:
            self.logger.warning(f"⚠️ Snapshot cleanup failed: {str(e)}")

# HTML template for health dashboard
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sync Health Dashboard - Angles AI Universe™</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .status { padding: 15px; border-radius: 5px; margin: 10px 0; text-align: center; font-weight: bold; }
        .status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .status.unknown { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-card { background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }
        .stat-value { font-size: 24px; font-weight: bold; color: #007bff; }
        .stat-label { font-size: 14px; color: #666; margin-top: 5px; }
        .refresh { text-align: center; margin: 20px 0; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn:hover { background: #0056b3; }
        .error-details { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .timestamp { color: #666; font-size: 14px; }
    </style>
    <script>
        function refreshData() {
            location.reload();
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔄 Sync Health Dashboard</h1>
            <p>Angles AI Universe™ - Supabase ↔ Notion Bidirectional Sync</p>
            <p class="timestamp">Last Updated: <span id="timestamp">{{ current_time }}</span></p>
        </div>
        
        <div class="status {{ status_class }}">
            {{ status_text }}
        </div>
        
        {% if last_run %}
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{stats_supabase_records}</div>
                <div class="stat-label">Supabase Records</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats_notion_records}</div>
                <div class="stat-label">Notion Records</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats_created}</div>
                <div class="stat-label">Created</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats_updated}</div>
                <div class="stat-label">Updated</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{duration}s</div>
                <div class="stat-label">Duration</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats_errors}</div>
                <div class="stat-label">Errors</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{health_score}/100</div>
                <div class="stat-label">Health Score</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{alerts_today}</div>
                <div class="stat-label">Alerts Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{backup_count}</div>
                <div class="stat-label">Backups Today</div>
            </div>
        </div>
        
        <div>
            <strong>Last Run:</strong> {last_run}<br>
            <strong>Status:</strong> {status}
        </div>
        
        <div class="refresh">
            <button class="btn" onclick="refreshData()">🔄 Refresh</button>
            <a href="/health" class="btn">📊 API Endpoint</a>
            <a href="/snapshot" class="btn">📸 Snapshot</a>
        </div>
        
        
        <div style="text-align: center; margin-top: 30px; color: #666; font-size: 12px;">
            Auto-refreshes every 30 seconds
        </div>
    </div>
</body>
</html>
"""


class HealthHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health dashboard"""
    
    def __init__(self, server_instance, *args, **kwargs):
        self.server_instance = server_instance
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            if path == '/':
                self._serve_dashboard()
            elif path == '/health':
                self._serve_health_api()
            elif path == '/ping':
                self._serve_ping()
            elif path == '/snapshot':
                self._serve_snapshot()
            else:
                self._serve_404()
        except Exception as e:
            self.server_instance.logger.error(f"❌ Request handler error: {str(e)}")
            self._serve_500(str(e))
    
    def _serve_dashboard(self):
        """Serve main dashboard page"""
        try:
            # Get cached status or generate new one
            status_data = self.server_instance.cached_status
            if not status_data:
                # Load latest snapshot
                status_data = load_health_status("logs/health/latest_snapshot.json")
            
            if not status_data:
                status_data = {
                    'sync_status': {'status': 'unknown'},
                    'health_score': 0,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            
            current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            
            # Determine status display
            sync_status = status_data.get('sync_status', {})
            health_score = status_data.get('health_score', 0)
            
            if health_score >= 80:
                status_class = "success"
                status_text = f"✅ System Healthy (Score: {health_score}/100)"
            elif health_score >= 60:
                status_class = "unknown"
                status_text = f"⚠️ System Degraded (Score: {health_score}/100)"
            else:
                status_class = "error"
                status_text = f"❌ System Unhealthy (Score: {health_score}/100)"
            
            stats = sync_status.get('statistics', {})
            
            # Build HTML response
            html_content = DASHBOARD_TEMPLATE.format(
                current_time=current_time,
                status_class=status_class,
                status_text=status_text,
                last_run=sync_status.get('last_run', 'Unknown'),
                status=sync_status.get('status', 'unknown'),
                stats_supabase_records=stats.get('supabase_records', 0),
                stats_notion_records=stats.get('notion_records', 0),
                stats_created=stats.get('created', 0),
                stats_updated=stats.get('updated', 0),
                stats_errors=stats.get('errors', 0),
                duration=sync_status.get('duration_seconds', 0),
                health_score=health_score,
                alerts_today=status_data.get('alert_status', {}).get('alerts_today', 0),
                backup_count=status_data.get('backup_status', {}).get('backup_count_today', 0)
            )
            
            self._send_response(200, html_content, 'text/html')
            
        except Exception as e:
            self.server_instance.logger.error(f"❌ Dashboard error: {str(e)}")
            self._serve_500(str(e))
    
    def _serve_health_api(self):
        """Serve health API endpoint"""
        try:
            status_data = self.server_instance.cached_status
            if not status_data:
                status_data = load_health_status("logs/health/latest_snapshot.json")
            
            if not status_data:
                response = {
                    'status': 'unknown',
                    'message': 'No health data available',
                    'health_score': 0,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            else:
                response = {
                    'status': 'ok' if status_data.get('health_score', 0) >= 80 else 'degraded',
                    'message': 'Health data available',
                    'health_score': status_data.get('health_score', 0),
                    'timestamp': status_data.get('timestamp'),
                    'sync_status': status_data.get('sync_status', {}),
                    'scheduler_status': status_data.get('scheduler_status', {}),
                    'backup_status': status_data.get('backup_status', {}),
                    'alert_status': status_data.get('alert_status', {}),
                    'system_metrics': status_data.get('system_metrics', {})
                }
            
            self._send_response(200, json.dumps(response, indent=2, default=str), 'application/json')
            
        except Exception as e:
            self.server_instance.logger.error(f"❌ Health API error: {str(e)}")
            self._serve_500(str(e))
    
    def _serve_ping(self):
        """Serve ping endpoint"""
        response = {
            'status': 'ok',
            'service': 'Angles AI Universe™ Health Dashboard',
            'version': '2.0.0',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        self._send_response(200, json.dumps(response), 'application/json')
    
    def _serve_snapshot(self):
        """Serve latest snapshot data"""
        try:
            snapshot_data = load_health_status("logs/health/latest_snapshot.json")
            if snapshot_data:
                self._send_response(200, json.dumps(snapshot_data, indent=2, default=str), 'application/json')
            else:
                self._serve_404()
        except Exception as e:
            self._serve_500(str(e))
    
    def _serve_404(self):
        """Serve 404 error"""
        self._send_response(404, "404 Not Found", 'text/plain')
    
    def _serve_500(self, error_msg: str):
        """Serve 500 error"""
        response = {
            'error': 'Internal Server Error',
            'message': error_msg,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        self._send_response(500, json.dumps(response), 'application/json')
    
    def _send_response(self, code: int, content: str, content_type: str):
        """Send HTTP response"""
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content.encode('utf-8'))))
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        self.server_instance.logger.info(f"📡 {format % args}")


def create_handler(server_instance):
    """Create request handler with server instance"""
    def handler(*args, **kwargs):
        return HealthHTTPRequestHandler(server_instance, *args, **kwargs)
    return handler

def main():
    """Start the hardened health dashboard server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Angles AI Universe™ Hardened Health Dashboard Server")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    try:
        # Initialize health dashboard server
        dashboard_server = HealthDashboardServer(port=args.port)
        
        print("🏥 Starting Angles AI Universe™ Health Dashboard Server")
        print("=" * 60)
        print(f"🌐 Dashboard: http://{args.host}:{args.port}")
        print(f"📊 Health API: http://{args.host}:{args.port}/health")
        print(f"📸 Snapshots: http://{args.host}:{args.port}/snapshot")
        print(f"🏓 Ping: http://{args.host}:{args.port}/ping")
        print("🔄 Auto-refresh: 30 seconds")
        print("📸 Health snapshots: 5 minutes")
        print("🛑 Press Ctrl+C to stop")
        print()
        
        # Create HTTP server
        handler = create_handler(dashboard_server)
        httpd = HTTPServer((args.host, args.port), handler)
        
        dashboard_server.logger.info(f"🚀 Health dashboard server started on {args.host}:{args.port}")
        
        # Start server
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Health dashboard server stopped by user")
        try:
            dashboard_server.logger.info("🛑 Server shutdown by user")
        except NameError:
            pass
    except Exception as e:
        print(f"💥 Health dashboard server failed: {e}")
        try:
            dashboard_server.logger.error(f"💥 Server failed: {str(e)}")
        except NameError:
            pass
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())