#!/usr/bin/env python3
"""
Angles AI Universe™ Alert & Incident Handling System
Provides GitHub issue alerts and Notion notifications for operational incidents

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

class AlertManager:
    """Centralized alert and incident management system"""
    
    def __init__(self):
        """Initialize alert manager"""
        self.setup_logging()
        self.load_environment()
        
        self.logger.info("🚨 Angles AI Universe™ Alert Manager Initialized")
    
    def setup_logging(self):
        """Setup logging for alert manager"""
        os.makedirs("logs/active", exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger('alert_manager')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/active/alerts.log"
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
            'github_token': os.getenv('GITHUB_TOKEN'),
            'repo_url': os.getenv('REPO_URL', ''),
            'notion_token': os.getenv('NOTION_TOKEN') or os.getenv('NOTION_API_KEY'),
            'notion_database_id': os.getenv('NOTION_DATABASE_ID')
        }
        
        # Parse repo info from URL
        if self.env['repo_url']:
            # Extract owner/repo from URL like https://github.com/owner/repo
            parts = self.env['repo_url'].rstrip('/').split('/')
            if len(parts) >= 2:
                self.github_owner = parts[-2]
                self.github_repo = parts[-1].replace('.git', '')
            else:
                self.github_owner = 'angles-ai'
                self.github_repo = 'angles-backup'
        else:
            self.github_owner = 'angles-ai'
            self.github_repo = 'angles-backup'
        
        self.logger.info(f"📋 Alert targets configured: GitHub ({self.github_owner}/{self.github_repo}), Notion DB")
    
    def create_github_issue(self, title: str, body: str, labels: List[str] = None, 
                          priority: str = "normal") -> Optional[str]:
        """Create or update GitHub issue for alerts"""
        if not self.env['github_token']:
            self.logger.warning("⚠️ GitHub token not configured - skipping GitHub alert")
            return None
        
        try:
            headers = {
                'Authorization': f"token {self.env['github_token']}",
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            }
            
            # Default labels
            issue_labels = (labels or []).copy()
            issue_labels.extend(['ops-alert', f'priority-{priority}'])
            
            # Check for existing open issue with same title
            search_url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/issues"
            search_params = {
                'state': 'open',
                'labels': 'ops-alert',
                'per_page': 100
            }
            
            response = requests.get(search_url, headers=headers, params=search_params, timeout=15)
            existing_issue = None
            
            if response.status_code == 200:
                issues = response.json()
                for issue in issues:
                    if issue['title'] == title:
                        existing_issue = issue
                        break
            
            if existing_issue:
                # Update existing issue
                issue_url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/issues/{existing_issue['number']}/comments"
                
                comment_data = {
                    'body': f"**Alert Update - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}**\n\n{body}"
                }
                
                response = requests.post(issue_url, headers=headers, json=comment_data, timeout=15)
                
                if response.status_code == 201:
                    self.logger.info(f"✅ Updated existing GitHub issue #{existing_issue['number']}: {title}")
                    return f"https://github.com/{self.github_owner}/{self.github_repo}/issues/{existing_issue['number']}"
                else:
                    raise Exception(f"Failed to update issue: HTTP {response.status_code}")
            else:
                # Create new issue
                issue_data = {
                    'title': title,
                    'body': f"**Automated Alert - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}**\n\n{body}",
                    'labels': issue_labels
                }
                
                response = requests.post(search_url, headers=headers, json=issue_data, timeout=15)
                
                if response.status_code == 201:
                    issue = response.json()
                    self.logger.info(f"✅ Created GitHub issue #{issue['number']}: {title}")
                    return issue['html_url']
                else:
                    raise Exception(f"Failed to create issue: HTTP {response.status_code}")
                    
        except Exception as e:
            self.logger.error(f"❌ GitHub alert failed: {str(e)}")
            return None
    
    def create_notion_alert(self, title: str, content: str, tags: List[str] = None, 
                          severity: str = "warning") -> Optional[str]:
        """Create Notion alert page"""
        if not self.env['notion_token'] or not self.env['notion_database_id']:
            self.logger.warning("⚠️ Notion credentials not configured - skipping Notion alert")
            return None
        
        try:
            headers = {
                'Authorization': f"Bearer {self.env['notion_token']}",
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
            
            # Default tags
            alert_tags = (tags or []).copy()
            alert_tags.extend(['alert', severity])
            
            # Create page data
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
                            'text': {'content': content[:2000]}  # Notion has limits
                        }]
                    },
                    'Date': {
                        'date': {'start': datetime.now(timezone.utc).isoformat()}
                    },
                    'Tag': {
                        'multi_select': [{'name': tag} for tag in alert_tags[:10]]  # Limit tags
                    }
                }
            }
            
            url = 'https://api.notion.com/v1/pages'
            response = requests.post(url, headers=headers, json=page_data, timeout=15)
            
            if response.status_code == 200:
                page = response.json()
                page_url = page.get('url', 'unknown')
                self.logger.info(f"✅ Created Notion alert page: {title}")
                return page_url
            else:
                raise Exception(f"Failed to create Notion page: HTTP {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"❌ Notion alert failed: {str(e)}")
            return None
    
    def send_alert(self, title: str, message: str, severity: str = "warning", 
                  tags: List[str] = None, github_labels: List[str] = None) -> Dict[str, Optional[str]]:
        """Send alert to all configured channels"""
        self.logger.info(f"🚨 Sending {severity} alert: {title}")
        
        results = {
            'github_url': None,
            'notion_url': None,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Map severity to priority
        priority_map = {
            'critical': 'high',
            'warning': 'normal',
            'info': 'low'
        }
        priority = priority_map.get(severity, 'normal')
        
        # Send GitHub alert
        try:
            github_url = self.create_github_issue(
                title=title,
                body=message,
                labels=github_labels or [],
                priority=priority
            )
            results['github_url'] = github_url
        except Exception as e:
            self.logger.error(f"❌ GitHub alert failed: {str(e)}")
        
        # Send Notion alert
        try:
            notion_url = self.create_notion_alert(
                title=title,
                content=message,
                tags=tags or [],
                severity=severity
            )
            results['notion_url'] = notion_url
        except Exception as e:
            self.logger.error(f"❌ Notion alert failed: {str(e)}")
        
        # Log alert summary
        success_count = sum(1 for url in [results['github_url'], results['notion_url']] if url)
        self.logger.info(f"📊 Alert sent to {success_count}/2 channels")
        
        # Save alert record
        self.save_alert_record(title, message, severity, results)
        
        return results
    
    def save_alert_record(self, title: str, message: str, severity: str, results: Dict):
        """Save alert record to local file"""
        try:
            os.makedirs("logs/alerts", exist_ok=True)
            
            alert_record = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'title': title,
                'message': message,
                'severity': severity,
                'results': results
            }
            
            # Save to daily alert log
            date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            alert_file = f"logs/alerts/alerts_{date_str}.json"
            
            # Append to file
            alerts = []
            if os.path.exists(alert_file):
                try:
                    with open(alert_file, 'r') as f:
                        alerts = json.load(f)
                except:
                    alerts = []
            
            alerts.append(alert_record)
            
            with open(alert_file, 'w') as f:
                json.dump(alerts, f, indent=2, default=str)
            
            self.logger.info(f"💾 Alert record saved to {alert_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save alert record: {str(e)}")
    
    def send_health_alert(self, system: str, status: str, details: Dict):
        """Send system health alert"""
        severity = 'critical' if status == 'critical' else 'warning'
        
        title = f"System Health Alert: {system} {status.upper()}"
        
        message = f"**System:** {system}\n"
        message += f"**Status:** {status.upper()}\n"
        message += f"**Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        
        if 'error' in details:
            message += f"**Error:** {details['error']}\n\n"
        
        message += "**Details:**\n"
        for key, value in details.items():
            if key != 'error':
                message += f"- {key}: {value}\n"
        
        message += "\n**Next Actions:**\n"
        message += "1. Check system logs in `logs/active/`\n"
        message += "2. Run manual health check: `python health_check.py`\n"
        message += "3. If Supabase is down, run restore: `python restore_from_github.py`\n"
        
        return self.send_alert(
            title=title,
            message=message,
            severity=severity,
            tags=['health', system, status],
            github_labels=['health-check', system]
        )
    
    def send_backup_alert(self, operation: str, status: str, details: Dict):
        """Send backup operation alert"""
        severity = 'critical' if status == 'failed' else 'warning'
        
        title = f"Backup Alert: {operation} {status.upper()}"
        
        message = f"**Operation:** {operation}\n"
        message += f"**Status:** {status.upper()}\n"
        message += f"**Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        
        if 'error' in details:
            message += f"**Error:** {details['error']}\n\n"
        
        message += "**Details:**\n"
        for key, value in details.items():
            if key != 'error':
                message += f"- {key}: {value}\n"
        
        message += "\n**Next Actions:**\n"
        message += "1. Check backup logs: `tail -f logs/active/backup.log`\n"
        message += "2. Verify environment variables are set\n"
        message += "3. Test manual backup: `python run_backup_manual.py --tag emergency`\n"
        
        return self.send_alert(
            title=title,
            message=message,
            severity=severity,
            tags=['backup', operation, status],
            github_labels=['backup', operation]
        )
    
    def send_restore_alert(self, operation: str, status: str, details: Dict):
        """Send restore operation alert"""
        severity = 'critical' if status == 'failed' else 'info'
        
        title = f"Restore Alert: {operation} {status.upper()}"
        
        message = f"**Operation:** {operation}\n"
        message += f"**Status:** {status.upper()}\n"
        message += f"**Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        
        if 'records_restored' in details:
            message += f"**Records Restored:** {details['records_restored']}\n"
        
        if 'error' in details:
            message += f"**Error:** {details['error']}\n\n"
        
        message += "**Details:**\n"
        for key, value in details.items():
            if key not in ['error', 'records_restored']:
                message += f"- {key}: {value}\n"
        
        if status == 'failed':
            message += "\n**Next Actions:**\n"
            message += "1. Check restore logs: `tail -f logs/active/restore.log`\n"
            message += "2. Verify GitHub repository accessibility\n"
            message += "3. Run manual restore: `python run_restore_now.py --dry-run`\n"
        
        return self.send_alert(
            title=title,
            message=message,
            severity=severity,
            tags=['restore', operation, status],
            github_labels=['restore', operation]
        )

def main():
    """Main entry point for testing alerts"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test alert system')
    parser.add_argument('--test', action='store_true', help='Send test alert')
    parser.add_argument('--title', default='Test Alert', help='Alert title')
    parser.add_argument('--message', default='This is a test alert from the automation system', help='Alert message')
    parser.add_argument('--severity', choices=['info', 'warning', 'critical'], default='info', help='Alert severity')
    
    args = parser.parse_args()
    
    if args.test:
        alert_manager = AlertManager()
        result = alert_manager.send_alert(
            title=args.title,
            message=args.message,
            severity=args.severity,
            tags=['test', 'automation']
        )
        
        print("\n🚨 Test Alert Results:")
        print(f"GitHub: {result['github_url'] or 'Failed'}")
        print(f"Notion: {result['notion_url'] or 'Failed'}")
    else:
        print("Alert manager initialized. Use --test to send a test alert.")

if __name__ == "__main__":
    main()