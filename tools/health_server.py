#!/usr/bin/env python3
"""
Health dashboard server for Supabase-Notion sync
Simple Flask server providing sync status and health monitoring for Angles AI Universe™

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from flask import Flask, jsonify, render_template_string
except ImportError:
    print("Error: Flask is required. Install with: pip install flask")
    sys.exit(1)

from sync.logging_util import load_health_status


app = Flask(__name__)


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
                <div class="stat-value">{{ stats.supabase_records }}</div>
                <div class="stat-label">Supabase Records</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.notion_records }}</div>
                <div class="stat-label">Notion Records</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.created }}</div>
                <div class="stat-label">Created</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.updated }}</div>
                <div class="stat-label">Updated</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ duration }}s</div>
                <div class="stat-label">Duration</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.errors }}</div>
                <div class="stat-label">Errors</div>
            </div>
        </div>
        
        <div>
            <strong>Last Run:</strong> {{ last_run }}<br>
            <strong>Status:</strong> {{ status.upper() }}
        </div>
        
        {% if error_details %}
        <div class="error-details">
            <strong>❌ Error Details:</strong>
            <ul>
            {% for error in error_details %}
                <li>{{ error }}</li>
            {% endfor %}
            </ul>
        </div>
        {% endif %}
        
        {% else %}
        <div class="status unknown">
            ℹ️ No sync runs found
        </div>
        {% endif %}
        
        <div class="refresh">
            <button class="btn" onclick="refreshData()">🔄 Refresh</button>
            <a href="/health" class="btn">📊 API Endpoint</a>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #666; font-size: 12px;">
            Auto-refreshes every 30 seconds
        </div>
    </div>
</body>
</html>
"""


@app.route('/')
def dashboard():
    """Main dashboard page"""
    
    health_data = load_health_status("logs/last_success.json")
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    
    if not health_data:
        return render_template_string(DASHBOARD_TEMPLATE,
            current_time=current_time,
            status_class="unknown",
            status_text="ℹ️ No sync data available",
            last_run=None
        )
    
    # Determine status
    status = health_data.get('status', 'unknown')
    if status == 'success':
        status_class = "success"
        status_text = "✅ Last sync completed successfully"
    elif status == 'error':
        status_class = "error"
        status_text = "❌ Last sync failed"
    else:
        status_class = "unknown"
        status_text = "⚠️ Sync status unknown"
    
    stats = health_data.get('statistics', {})
    
    return render_template_string(DASHBOARD_TEMPLATE,
        current_time=current_time,
        status_class=status_class,
        status_text=status_text,
        last_run=health_data.get('last_run', 'Unknown'),
        status=status,
        stats=stats,
        duration=health_data.get('duration_seconds', 0),
        error_details=health_data.get('error_details', [])
    )


@app.route('/health')
def health_api():
    """Health check API endpoint"""
    
    health_data = load_health_status("logs/last_success.json")
    
    if not health_data:
        return jsonify({
            'status': 'unknown',
            'message': 'No sync data available',
            'last_run': None,
            'statistics': {},
            'errors': []
        })
    
    return jsonify({
        'status': health_data.get('status', 'unknown'),
        'message': 'Sync health data loaded successfully',
        'last_run': health_data.get('last_run'),
        'duration_seconds': health_data.get('duration_seconds', 0),
        'statistics': health_data.get('statistics', {}),
        'error_details': health_data.get('error_details', []),
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@app.route('/ping')
def ping():
    """Simple ping endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'Sync Health Server',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


def main():
    """Start the health server"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync Health Dashboard Server")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to (default: 8080)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    print("🏥 Starting Sync Health Dashboard Server")
    print("=" * 50)
    print(f"🌐 URL: http://{args.host}:{args.port}")
    print(f"📊 Health API: http://{args.host}:{args.port}/health")
    print("🔄 Press Ctrl+C to stop")
    print()
    
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            use_reloader=False  # Disable reloader in production
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"💥 Server failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())