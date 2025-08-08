#!/usr/bin/env python3
"""
Angles AI Universe™ Weekly Summary Generator
Compiles weekly operational metrics and creates reports for GitHub and Notion

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import glob

# Import helpers
try:
    from alerts.notify import AlertManager
except ImportError:
    AlertManager = None

try:
    from git_helpers import GitHelper
except ImportError:
    GitHelper = None

class WeeklySummaryGenerator:
    """Weekly operational summary generator and publisher"""
    
    def __init__(self):
        """Initialize weekly summary generator"""
        self.setup_logging()
        self.load_environment()
        self.alert_manager = AlertManager() if AlertManager else None
        self.git_helper = GitHelper() if GitHelper else None
        
        # Calculate week range (Sunday to Saturday)
        now = datetime.now(timezone.utc)
        days_since_sunday = now.weekday() + 1 if now.weekday() != 6 else 0
        self.week_start = (now - timedelta(days=days_since_sunday)).replace(hour=0, minute=0, second=0, microsecond=0)
        self.week_end = self.week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        self.logger.info(f"📅 Weekly Summary Generator Initialized")
        self.logger.info(f"   Week: {self.week_start.strftime('%Y-%m-%d')} to {self.week_end.strftime('%Y-%m-%d')}")
    
    def setup_logging(self):
        """Setup logging for summary generator"""
        os.makedirs("logs/active", exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger('weekly_summary')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/active/weekly_summary.log"
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
        
        self.logger.info("📋 Environment loaded for weekly summary")
    
    def collect_ops_events(self) -> Dict[str, Any]:
        """Collect operational events from logs"""
        self.logger.info("📈 Collecting operational events...")
        
        ops_events = {
            'health_checks': {'total': 0, 'passed': 0, 'failed': 0, 'incidents': []},
            'backups': {'total': 0, 'successful': 0, 'failed': 0, 'details': []},
            'restores': {'total': 0, 'successful': 0, 'failed': 0, 'details': []},
            'alerts': {'total': 0, 'critical': 0, 'warning': 0, 'info': 0},
            'config_changes': {'total': 0, 'files_versioned': 0, 'details': []},
            'schema_checks': {'total': 0, 'migrations': 0, 'issues': []}
        }
        
        try:
            # Analyze health check logs
            health_logs = self.parse_log_files('logs/active/system_health*.log')
            for entry in health_logs:
                if self.is_in_week_range(entry.get('timestamp')):
                    ops_events['health_checks']['total'] += 1
                    if 'healthy' in entry.get('message', '').lower():
                        ops_events['health_checks']['passed'] += 1
                    else:
                        ops_events['health_checks']['failed'] += 1
                        ops_events['health_checks']['incidents'].append({
                            'timestamp': entry.get('timestamp'),
                            'message': entry.get('message', '')[:200]
                        })
            
            # Analyze backup logs
            backup_logs = self.parse_log_files('logs/active/*backup*.log')
            for entry in backup_logs:
                if self.is_in_week_range(entry.get('timestamp')):
                    if 'backup' in entry.get('message', '').lower():
                        ops_events['backups']['total'] += 1
                        if any(word in entry.get('message', '').lower() for word in ['completed', 'success', 'saved']):
                            ops_events['backups']['successful'] += 1
                        elif any(word in entry.get('message', '').lower() for word in ['failed', 'error', 'exception']):
                            ops_events['backups']['failed'] += 1
                            ops_events['backups']['details'].append({
                                'timestamp': entry.get('timestamp'),
                                'error': entry.get('message', '')[:200]
                            })
            
            # Analyze restore logs
            restore_logs = self.parse_log_files('logs/active/restore*.log')
            for entry in restore_logs:
                if self.is_in_week_range(entry.get('timestamp')):
                    if 'restore' in entry.get('message', '').lower():
                        ops_events['restores']['total'] += 1
                        if 'completed' in entry.get('message', '').lower():
                            ops_events['restores']['successful'] += 1
                        elif 'failed' in entry.get('message', '').lower():
                            ops_events['restores']['failed'] += 1
                            ops_events['restores']['details'].append({
                                'timestamp': entry.get('timestamp'),
                                'error': entry.get('message', '')[:200]
                            })
            
            # Analyze alert logs
            alert_files = glob.glob('logs/alerts/alerts_*.json')
            for alert_file in alert_files:
                try:
                    with open(alert_file, 'r') as f:
                        alerts = json.load(f)
                        for alert in alerts:
                            if self.is_in_week_range(alert.get('timestamp')):
                                ops_events['alerts']['total'] += 1
                                severity = alert.get('severity', 'info')
                                if severity in ops_events['alerts']:
                                    ops_events['alerts'][severity] += 1
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to parse alert file {alert_file}: {e}")
            
            # Analyze config changes
            config_logs = self.parse_log_files('logs/active/*config*.log')
            for entry in config_logs:
                if self.is_in_week_range(entry.get('timestamp')):
                    if 'versioned' in entry.get('message', '').lower():
                        ops_events['config_changes']['files_versioned'] += 1
                    if 'config' in entry.get('message', '').lower():
                        ops_events['config_changes']['total'] += 1
            
            # Analyze schema guard logs
            schema_logs = self.parse_log_files('logs/active/schema_guard*.log')
            for entry in schema_logs:
                if self.is_in_week_range(entry.get('timestamp')):
                    if 'schema' in entry.get('message', '').lower():
                        ops_events['schema_checks']['total'] += 1
                        if 'migration' in entry.get('message', '').lower():
                            ops_events['schema_checks']['migrations'] += 1
        
        except Exception as e:
            self.logger.error(f"❌ Failed to collect ops events: {str(e)}")
        
        self.logger.info(f"✅ Collected ops events: {ops_events['health_checks']['total']} health checks, {ops_events['backups']['total']} backups")
        return ops_events
    
    def parse_log_files(self, pattern: str) -> List[Dict]:
        """Parse log files matching pattern"""
        entries = []
        log_files = glob.glob(pattern)
        
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        # Simple log parsing - assumes format: timestamp - level - message
                        parts = line.strip().split(' - ', 2)
                        if len(parts) >= 3:
                            try:
                                timestamp = datetime.fromisoformat(parts[0].replace('Z', '+00:00'))
                                entries.append({
                                    'timestamp': timestamp.isoformat(),
                                    'level': parts[1],
                                    'message': parts[2]
                                })
                            except:
                                # Skip malformed entries
                                continue
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to parse log file {log_file}: {e}")
        
        return entries
    
    def is_in_week_range(self, timestamp_str: str) -> bool:
        """Check if timestamp is in current week range"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return self.week_start <= timestamp <= self.week_end
        except:
            return False
    
    def collect_supabase_stats(self) -> Dict[str, Any]:
        """Collect Supabase database statistics"""
        self.logger.info("📊 Collecting Supabase statistics...")
        
        stats = {
            'decision_vault': {'total_rows': 0, 'added_this_week': 0, 'updated_this_week': 0},
            'ai_decision_log': {'total_rows': 0, 'added_this_week': 0, 'updated_this_week': 0},
            'connection_status': 'unknown',
            'response_time_ms': 0
        }
        
        if not self.env['supabase_url'] or not self.env['supabase_key']:
            stats['connection_status'] = 'no_credentials'
            return stats
        
        try:
            headers = {
                'apikey': self.env['supabase_key'],
                'Authorization': f"Bearer {self.env['supabase_key']}",
                'Content-Type': 'application/json'
            }
            
            start_time = datetime.now()
            
            # Check decision_vault
            url = f"{self.env['supabase_url']}/rest/v1/decision_vault"
            params = {'select': 'id,created_at,updated_at'}
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                stats['response_time_ms'] = int((datetime.now() - start_time).total_seconds() * 1000)
                stats['connection_status'] = 'connected'
                
                data = response.json()
                stats['decision_vault']['total_rows'] = len(data)
                
                # Count this week's activity
                for record in data:
                    created_at = record.get('created_at')
                    updated_at = record.get('updated_at')
                    
                    if created_at and self.is_in_week_range(created_at):
                        stats['decision_vault']['added_this_week'] += 1
                    
                    if updated_at and self.is_in_week_range(updated_at) and created_at != updated_at:
                        stats['decision_vault']['updated_this_week'] += 1
            
            # Check ai_decision_log if it exists
            url = f"{self.env['supabase_url']}/rest/v1/ai_decision_log"
            params = {'select': 'id,timestamp'}
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                stats['ai_decision_log']['total_rows'] = len(data)
                
                for record in data:
                    timestamp = record.get('timestamp')
                    if timestamp and self.is_in_week_range(timestamp):
                        stats['ai_decision_log']['added_this_week'] += 1
        
        except Exception as e:
            stats['connection_status'] = 'error'
            self.logger.error(f"❌ Failed to collect Supabase stats: {str(e)}")
        
        self.logger.info(f"✅ Supabase stats: {stats['decision_vault']['total_rows']} decisions, {stats['connection_status']} status")
        return stats
    
    def collect_notion_metrics(self) -> Dict[str, Any]:
        """Collect Notion API usage metrics"""
        self.logger.info("📝 Collecting Notion metrics...")
        
        metrics = {
            'pages_created': 0,
            'pages_updated': 0,
            'api_calls': 0,
            'connection_status': 'unknown',
            'database_accessible': False
        }
        
        if not self.env['notion_token'] or not self.env['notion_database_id']:
            metrics['connection_status'] = 'no_credentials'
            return metrics
        
        try:
            headers = {
                'Authorization': f"Bearer {self.env['notion_token']}",
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
            
            # Test API connectivity
            user_url = 'https://api.notion.com/v1/users/me'
            response = requests.get(user_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                metrics['connection_status'] = 'connected'
                metrics['api_calls'] += 1
                
                # Query database for recent activity
                query_url = f"https://api.notion.com/v1/databases/{self.env['notion_database_id']}/query"
                
                # Query for pages created this week
                week_filter = {
                    'filter': {
                        'property': 'Date',
                        'date': {
                            'on_or_after': self.week_start.isoformat()
                        }
                    }
                }
                
                response = requests.post(query_url, headers=headers, json=week_filter, timeout=15)
                
                if response.status_code == 200:
                    metrics['database_accessible'] = True
                    metrics['api_calls'] += 1
                    
                    data = response.json()
                    results = data.get('results', [])
                    
                    for page in results:
                        created_time = page.get('created_time')
                        last_edited_time = page.get('last_edited_time')
                        
                        if created_time and self.is_in_week_range(created_time):
                            metrics['pages_created'] += 1
                        
                        if (last_edited_time and self.is_in_week_range(last_edited_time) and 
                            created_time != last_edited_time):
                            metrics['pages_updated'] += 1
            
        except Exception as e:
            metrics['connection_status'] = 'error'
            self.logger.error(f"❌ Failed to collect Notion metrics: {str(e)}")
        
        self.logger.info(f"✅ Notion metrics: {metrics['pages_created']} pages created, {metrics['connection_status']} status")
        return metrics
    
    def collect_github_activity(self) -> Dict[str, Any]:
        """Collect GitHub backup/restore activity"""
        self.logger.info("🐙 Collecting GitHub activity...")
        
        activity = {
            'commits_this_week': 0,
            'backup_commits': 0,
            'restore_operations': 0,
            'repository_status': 'unknown',
            'last_backup': None,
            'repository_size_mb': 0
        }
        
        try:
            if self.git_helper:
                git_info = self.git_helper.get_git_info()
                activity['repository_status'] = 'available' if git_info['status']['is_repo'] else 'not_available'
                
                # Parse git logs for this week's activity
                success, stdout, stderr = self.git_helper.run_git_command([
                    'log', 
                    f'--since={self.week_start.isoformat()}',
                    '--oneline'
                ])
                
                if success:
                    commits = stdout.strip().split('\n') if stdout.strip() else []
                    activity['commits_this_week'] = len(commits)
                    
                    # Count backup-related commits
                    for commit in commits:
                        if any(word in commit.lower() for word in ['backup', 'export', 'snapshot']):
                            activity['backup_commits'] += 1
                
                # Get repository size
                success, stdout, stderr = self.git_helper.run_git_command(['count-objects', '-vH'])
                if success:
                    for line in stdout.split('\n'):
                        if 'size' in line and 'MB' in line:
                            try:
                                size_str = line.split()[1].replace('MB', '')
                                activity['repository_size_mb'] = float(size_str)
                            except:
                                pass
        
        except Exception as e:
            self.logger.error(f"❌ Failed to collect GitHub activity: {str(e)}")
        
        self.logger.info(f"✅ GitHub activity: {activity['commits_this_week']} commits, {activity['repository_status']} status")
        return activity
    
    def identify_top_incidents(self, ops_events: Dict) -> List[Dict[str, str]]:
        """Identify top incidents from the week"""
        incidents = []
        
        # Add health check failures
        for incident in ops_events['health_checks']['incidents'][:3]:
            incidents.append({
                'type': 'Health Check Failure',
                'timestamp': incident['timestamp'],
                'description': incident['message']
            })
        
        # Add backup failures
        for failure in ops_events['backups']['details'][:2]:
            incidents.append({
                'type': 'Backup Failure',
                'timestamp': failure['timestamp'],
                'description': failure['error']
            })
        
        # Add restore issues
        for failure in ops_events['restores']['details'][:2]:
            incidents.append({
                'type': 'Restore Issue',
                'timestamp': failure['timestamp'],
                'description': failure['error']
            })
        
        # Sort by timestamp (most recent first)
        incidents.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return incidents[:5]  # Top 5 incidents
    
    def generate_next_actions(self, ops_events: Dict, supabase_stats: Dict, notion_metrics: Dict) -> List[str]:
        """Generate next actions checklist"""
        actions = []
        
        # Health-related actions
        if ops_events['health_checks']['failed'] > 0:
            actions.append("Review health check failures and address root causes")
        
        # Backup-related actions
        if ops_events['backups']['failed'] > 0:
            actions.append("Investigate backup failures and ensure data protection")
        
        # Database-related actions
        if supabase_stats['connection_status'] != 'connected':
            actions.append("Restore Supabase connectivity and verify credentials")
        
        # Notion-related actions
        if notion_metrics['connection_status'] != 'connected':
            actions.append("Check Notion API integration and database permissions")
        
        # Schema-related actions
        if ops_events['schema_checks']['migrations'] > 0:
            actions.append("Apply pending schema migrations and verify database integrity")
        
        # General maintenance
        actions.append("Review log retention and archive old files")
        actions.append("Verify all automated schedules are running properly")
        actions.append("Test disaster recovery procedures")
        
        return actions[:7]  # Maximum 7 actions
    
    def generate_markdown_summary(self, ops_events: Dict, supabase_stats: Dict, 
                                notion_metrics: Dict, github_activity: Dict) -> str:
        """Generate markdown summary report"""
        incidents = self.identify_top_incidents(ops_events)
        next_actions = self.generate_next_actions(ops_events, supabase_stats, notion_metrics)
        
        week_str = f"{self.week_start.strftime('%Y-%m-%d')} to {self.week_end.strftime('%Y-%m-%d')}"
        
        markdown = f"""# Angles AI Universe™ Weekly Operations Summary

**Week:** {week_str}  
**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Status:** {'🟢 Healthy' if ops_events['health_checks']['failed'] == 0 else '🟡 Issues Detected'}

## 📊 Operational Overview

### Health Monitoring
- **Total Health Checks:** {ops_events['health_checks']['total']}
- **Passed:** {ops_events['health_checks']['passed']} ✅
- **Failed:** {ops_events['health_checks']['failed']} ❌
- **Success Rate:** {(ops_events['health_checks']['passed'] / max(ops_events['health_checks']['total'], 1) * 100):.1f}%

### Backup Operations
- **Total Backups:** {ops_events['backups']['total']}
- **Successful:** {ops_events['backups']['successful']} ✅
- **Failed:** {ops_events['backups']['failed']} ❌
- **Success Rate:** {(ops_events['backups']['successful'] / max(ops_events['backups']['total'], 1) * 100):.1f}%

### Data Recovery
- **Restore Operations:** {ops_events['restores']['total']}
- **Successful:** {ops_events['restores']['successful']} ✅
- **Failed:** {ops_events['restores']['failed']} ❌

### System Alerts
- **Total Alerts:** {ops_events['alerts']['total']}
- **Critical:** {ops_events['alerts']['critical']} 🔴
- **Warning:** {ops_events['alerts']['warning']} 🟡
- **Info:** {ops_events['alerts']['info']} 🔵

## 💾 Database Statistics

### Supabase (Status: {supabase_stats['connection_status']})
- **Decision Vault Records:** {supabase_stats['decision_vault']['total_rows']}
- **Added This Week:** {supabase_stats['decision_vault']['added_this_week']}
- **Updated This Week:** {supabase_stats['decision_vault']['updated_this_week']}
- **AI Decision Log:** {supabase_stats['ai_decision_log']['total_rows']} total, {supabase_stats['ai_decision_log']['added_this_week']} new
- **Response Time:** {supabase_stats['response_time_ms']}ms

### Notion Integration (Status: {notion_metrics['connection_status']})
- **Pages Created:** {notion_metrics['pages_created']}
- **Pages Updated:** {notion_metrics['pages_updated']}
- **API Calls:** {notion_metrics['api_calls']}
- **Database Accessible:** {'Yes' if notion_metrics['database_accessible'] else 'No'}

## 🐙 Repository Activity

- **Status:** {github_activity['repository_status']}
- **Commits This Week:** {github_activity['commits_this_week']}
- **Backup Commits:** {github_activity['backup_commits']}
- **Repository Size:** {github_activity['repository_size_mb']:.1f} MB

## 🔧 Configuration Management

- **Config Changes:** {ops_events['config_changes']['total']}
- **Files Versioned:** {ops_events['config_changes']['files_versioned']}
- **Schema Checks:** {ops_events['schema_checks']['total']}
- **Migrations Applied:** {ops_events['schema_checks']['migrations']}
"""
        
        # Add incidents section
        if incidents:
            markdown += "\n## 🚨 Top Incidents\n\n"
            for i, incident in enumerate(incidents, 1):
                timestamp = datetime.fromisoformat(incident['timestamp'].replace('Z', '+00:00')).strftime('%m/%d %H:%M')
                markdown += f"{i}. **{incident['type']}** ({timestamp})\n"
                markdown += f"   {incident['description'][:150]}...\n\n"
        
        # Add next actions
        markdown += "\n## ✅ Next Actions\n\n"
        for i, action in enumerate(next_actions, 1):
            markdown += f"{i}. [ ] {action}\n"
        
        # Add footer
        markdown += f"\n---\n\n*Generated by Angles AI Universe™ Automated Operations System*  \n*Week {self.week_start.strftime('%Y-W%V')} Summary*\n"
        
        return markdown
    
    def save_markdown_summary(self, markdown: str) -> str:
        """Save markdown summary to file"""
        os.makedirs("logs/summaries", exist_ok=True)
        
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f"logs/summaries/summary_{timestamp}.md"
        
        with open(filename, 'w') as f:
            f.write(markdown)
        
        self.logger.info(f"💾 Weekly summary saved: {filename}")
        return filename
    
    def create_notion_summary(self, markdown: str) -> Optional[str]:
        """Create Notion page with weekly summary"""
        if not self.env['notion_token'] or not self.env['notion_database_id']:
            self.logger.warning("⚠️ Notion credentials not configured - skipping Notion summary")
            return None
        
        try:
            headers = {
                'Authorization': f"Bearer {self.env['notion_token']}",
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
            
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            title = f"Weekly Summary {timestamp}"
            
            # Convert markdown to Notion blocks (simplified)
            content_blocks = self.markdown_to_notion_blocks(markdown)
            
            page_data = {
                'parent': {'database_id': self.env['notion_database_id']},
                'properties': {
                    'Name': {
                        'title': [{
                            'text': {'content': title}
                        }]
                    },
                    'Message': {
                        'rich_text': [{
                            'text': {'content': 'Weekly operational summary and metrics'}
                        }]
                    },
                    'Date': {
                        'date': {'start': datetime.now(timezone.utc).isoformat()}
                    },
                    'Tag': {
                        'multi_select': [{'name': 'summary'}, {'name': 'ops'}, {'name': 'weekly'}]
                    }
                },
                'children': content_blocks
            }
            
            url = 'https://api.notion.com/v1/pages'
            response = requests.post(url, headers=headers, json=page_data, timeout=30)
            
            if response.status_code == 200:
                page = response.json()
                page_url = page.get('url', 'unknown')
                self.logger.info(f"✅ Notion summary created: {title}")
                return page_url
            else:
                self.logger.error(f"❌ Failed to create Notion page: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Notion summary creation failed: {str(e)}")
            return None
    
    def markdown_to_notion_blocks(self, markdown: str) -> List[Dict]:
        """Convert markdown to Notion blocks (simplified)"""
        blocks = []
        lines = markdown.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('# '):
                # Heading 1
                blocks.append({
                    'object': 'block',
                    'type': 'heading_1',
                    'heading_1': {
                        'rich_text': [{'type': 'text', 'text': {'content': line[2:]}}]
                    }
                })
            elif line.startswith('## '):
                # Heading 2
                blocks.append({
                    'object': 'block',
                    'type': 'heading_2',
                    'heading_2': {
                        'rich_text': [{'type': 'text', 'text': {'content': line[3:]}}]
                    }
                })
            elif line.startswith('### '):
                # Heading 3
                blocks.append({
                    'object': 'block',
                    'type': 'heading_3',
                    'heading_3': {
                        'rich_text': [{'type': 'text', 'text': {'content': line[4:]}}]
                    }
                })
            elif line.startswith('- '):
                # Bullet list
                blocks.append({
                    'object': 'block',
                    'type': 'bulleted_list_item',
                    'bulleted_list_item': {
                        'rich_text': [{'type': 'text', 'text': {'content': line[2:]}}]
                    }
                })
            elif line.startswith(('1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ', '8. ', '9. ')):
                # Numbered list
                blocks.append({
                    'object': 'block',
                    'type': 'numbered_list_item',
                    'numbered_list_item': {
                        'rich_text': [{'type': 'text', 'text': {'content': line[3:]}}]
                    }
                })
            else:
                # Regular paragraph
                if len(line) > 0:
                    blocks.append({
                        'object': 'block',
                        'type': 'paragraph',
                        'paragraph': {
                            'rich_text': [{'type': 'text', 'text': {'content': line[:2000]}}]  # Notion limit
                        }
                    })
        
        return blocks[:100]  # Notion has a limit on children blocks
    
    def insert_decision_record(self, summary_data: Dict) -> bool:
        """Insert technical decision record about summary publication"""
        if not self.env['supabase_url'] or not self.env['supabase_key']:
            return False
        
        try:
            headers = {
                'apikey': self.env['supabase_key'],
                'Authorization': f"Bearer {self.env['supabase_key']}",
                'Content-Type': 'application/json'
            }
            
            decision_text = f"""Weekly operational summary generated and published for week {self.week_start.strftime('%Y-%m-%d')} to {self.week_end.strftime('%Y-%m-%d')}.

Key metrics:
- Health checks: {summary_data.get('health_checks', {}).get('total', 0)}
- Backups: {summary_data.get('backups', {}).get('total', 0)}
- Alerts: {summary_data.get('alerts', {}).get('total', 0)}

Summary published to GitHub and Notion for operational transparency and team coordination."""
            
            record = {
                'decision': decision_text,
                'type': 'operational',
                'date': datetime.now(timezone.utc).date().isoformat(),
                'active': True,
                'comment': 'Automated weekly summary publication'
            }
            
            url = f"{self.env['supabase_url']}/rest/v1/decision_vault"
            response = requests.post(url, headers=headers, json=record, timeout=15)
            
            if response.status_code in [200, 201]:
                self.logger.info("✅ Decision record inserted for weekly summary")
                return True
            else:
                self.logger.error(f"❌ Failed to insert decision record: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Decision record insertion failed: {str(e)}")
            return False
    
    def generate_and_publish_summary(self) -> Dict[str, Any]:
        """Generate and publish complete weekly summary"""
        self.logger.info("🚀 Starting Weekly Summary Generation")
        self.logger.info("=" * 60)
        
        start_time = datetime.now(timezone.utc)
        
        result = {
            'timestamp': start_time.isoformat(),
            'week_range': f"{self.week_start.strftime('%Y-%m-%d')} to {self.week_end.strftime('%Y-%m-%d')}",
            'markdown_file': None,
            'notion_url': None,
            'github_committed': False,
            'decision_recorded': False,
            'success': False,
            'errors': []
        }
        
        try:
            # Collect all data
            self.logger.info("📈 Collecting operational data...")
            ops_events = self.collect_ops_events()
            supabase_stats = self.collect_supabase_stats()
            notion_metrics = self.collect_notion_metrics()
            github_activity = self.collect_github_activity()
            
            # Generate markdown summary
            self.logger.info("📝 Generating markdown summary...")
            markdown = self.generate_markdown_summary(ops_events, supabase_stats, notion_metrics, github_activity)
            
            # Save markdown file
            markdown_file = self.save_markdown_summary(markdown)
            result['markdown_file'] = markdown_file
            
            # Create Notion summary
            self.logger.info("📝 Creating Notion summary...")
            notion_url = self.create_notion_summary(markdown)
            result['notion_url'] = notion_url
            
            # Commit to GitHub
            if self.git_helper:
                self.logger.info("🐙 Committing to GitHub...")
                commit_result = self.git_helper.safe_commit_and_push(
                    [markdown_file],
                    f"Weekly summary {self.week_start.strftime('%Y-W%V')}"
                )
                result['github_committed'] = commit_result['success']
                
                if not commit_result['success']:
                    result['errors'].extend(commit_result['errors'])
            
            # Record decision
            summary_data = {
                'health_checks': ops_events['health_checks'],
                'backups': ops_events['backups'],
                'alerts': ops_events['alerts']
            }
            
            decision_recorded = self.insert_decision_record(summary_data)
            result['decision_recorded'] = decision_recorded
            
            # Calculate duration
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            result['duration_seconds'] = duration
            
            # Determine success
            result['success'] = (markdown_file is not None and 
                               (notion_url is not None or result['github_committed']))
            
            # Log summary
            self.logger.info("=" * 60)
            status_icon = "🎉" if result['success'] else "⚠️"
            self.logger.info(f"{status_icon} Weekly Summary Generation Complete")
            self.logger.info(f"   Duration: {duration:.2f} seconds")
            self.logger.info(f"   Markdown: {'✅' if markdown_file else '❌'}")
            self.logger.info(f"   Notion: {'✅' if notion_url else '❌'}")
            self.logger.info(f"   GitHub: {'✅' if result['github_committed'] else '❌'}")
            self.logger.info(f"   Decision: {'✅' if decision_recorded else '❌'}")
            
            # Send alert if there were issues
            if not result['success'] and self.alert_manager:
                self.alert_manager.send_alert(
                    title="Weekly Summary Generation Issues",
                    message=f"Weekly summary generation completed with issues. Errors: {result['errors']}",
                    severity="warning",
                    tags=['weekly-summary', 'generation', 'issues']
                )
            
            return result
            
        except Exception as e:
            result['success'] = False
            result['errors'].append(f"Summary generation failed: {str(e)}")
            self.logger.error(f"💥 Weekly summary generation failed: {str(e)}")
            
            # Send critical alert
            if self.alert_manager:
                self.alert_manager.send_alert(
                    title="Weekly Summary Generation Critical Failure",
                    message=f"Critical failure during weekly summary generation: {str(e)}",
                    severity="critical",
                    tags=['weekly-summary', 'critical', 'failure']
                )
            
            return result

def main():
    """Main entry point for weekly summary generator"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate weekly operational summary')
    parser.add_argument('--generate', action='store_true', help='Generate and publish weekly summary')
    parser.add_argument('--test', action='store_true', help='Test data collection only')
    parser.add_argument('--week-offset', type=int, default=0, help='Generate for N weeks ago')
    
    args = parser.parse_args()
    
    try:
        generator = WeeklySummaryGenerator()
        
        if args.test:
            print("\n📈 Testing Data Collection:")
            
            ops_events = generator.collect_ops_events()
            print(f"  Ops Events: {ops_events['health_checks']['total']} health checks, {ops_events['backups']['total']} backups")
            
            supabase_stats = generator.collect_supabase_stats()
            print(f"  Supabase: {supabase_stats['connection_status']}, {supabase_stats['decision_vault']['total_rows']} records")
            
            notion_metrics = generator.collect_notion_metrics()
            print(f"  Notion: {notion_metrics['connection_status']}, {notion_metrics['pages_created']} pages created")
            
            github_activity = generator.collect_github_activity()
            print(f"  GitHub: {github_activity['repository_status']}, {github_activity['commits_this_week']} commits")
        
        elif args.generate:
            result = generator.generate_and_publish_summary()
            
            print("\n📅 Weekly Summary Results:")
            print(f"  Success: {result['success']}")
            print(f"  Week: {result['week_range']}")
            print(f"  Markdown: {result['markdown_file'] or 'Failed'}")
            print(f"  Notion: {result['notion_url'] or 'Failed'}")
            print(f"  GitHub: {'Committed' if result['github_committed'] else 'Failed'}")
            
            if result['errors']:
                print(f"  Errors: {result['errors']}")
            
            sys.exit(0 if result['success'] else 1)
        
        else:
            print("Weekly summary generator initialized. Use --help for available commands.")
    
    except KeyboardInterrupt:
        print("\n🛑 Weekly summary generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Weekly summary generation failed: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()