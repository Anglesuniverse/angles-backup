#!/usr/bin/env python3
"""
Angles AI Universe™ Health Monitoring System
Comprehensive health checks for Supabase-Notion sync with automated notifications

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import argparse
import logging
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Email functionality (simplified for Replit compatibility)
try:
    import smtplib
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    print("⚠️ Email functionality not available in this environment")

# Exit codes
EXIT_OK = 0
EXIT_WARNINGS = 1
EXIT_ERRORS = 2

class HealthMonitor:
    """Comprehensive health monitoring for Angles AI Universe™"""
    
    def __init__(self, test_mode: bool = False):
        """Initialize health monitor"""
        self.test_mode = test_mode
        self.warnings = []
        self.errors = []
        self.results = {}
        
        # Load configuration
        self.config = self._load_config()
        
        # Setup logging
        self._setup_logging()
        
        # Load environment secrets
        self._load_secrets()
        
        self.logger.info("🔍 Health Monitor initialized")
        if self.test_mode:
            self.logger.info("⚠️ Running in TEST MODE")
    
    def _load_config(self) -> Dict:
        """Load configuration from config.json"""
        try:
            config_path = Path("config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                return self._default_config()
        except Exception as e:
            print(f"❌ Failed to load config.json: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """Return default configuration"""
        return {
            "health_check": {
                "timeout_seconds": 30,
                "max_unsynced_warning": 10,
                "max_unsynced_error": 50
            },
            "notifications": {
                "method": "slack",
                "slack_enabled": True,
                "email_enabled": False
            }
        }
    
    def _setup_logging(self):
        """Setup logging to both file and console"""
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger('health_monitor')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        log_file = f"logs/health_check.log"
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
    
    def _load_secrets(self):
        """Load secrets from environment variables"""
        self.secrets = {
            'supabase_url': os.getenv('SUPABASE_URL'),
            'supabase_key': os.getenv('SUPABASE_KEY'),
            'notion_api_key': os.getenv('NOTION_API_KEY'),
            'notion_database_id': os.getenv('NOTION_DATABASE_ID'),
            'slack_webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
            'github_token': os.getenv('GITHUB_TOKEN'),
            'smtp_server': os.getenv('SMTP_SERVER'),
            'smtp_port': os.getenv('SMTP_PORT'),
            'smtp_username': os.getenv('SMTP_USERNAME'),
            'smtp_password': os.getenv('SMTP_PASSWORD'),
            'email_recipient': os.getenv('EMAIL_RECIPIENT')
        }
    
    def check_supabase_connection(self) -> bool:
        """Check Supabase connection and access"""
        self.logger.info("🔍 Checking Supabase connection...")
        
        if self.test_mode:
            self.logger.warning("⚠️ TEST MODE: Simulating Supabase connection failure")
            self.errors.append("TEST: Supabase connection failed")
            return False
        
        try:
            if not self.secrets['supabase_url'] or not self.secrets['supabase_key']:
                self.errors.append("Missing Supabase credentials (SUPABASE_URL or SUPABASE_KEY)")
                return False
            
            # Test connection with health check
            url = f"{self.secrets['supabase_url']}/rest/v1/decision_vault"
            headers = {
                'apikey': self.secrets['supabase_key'],
                'Authorization': f"Bearer {self.secrets['supabase_key']}",
                'Content-Type': 'application/json'
            }
            
            params = {'select': 'id', 'limit': '1'}
            response = requests.get(
                url, 
                headers=headers, 
                params=params,
                timeout=self.config['health_check']['timeout_seconds']
            )
            
            if response.status_code == 200:
                self.logger.info("✅ Supabase connection successful")
                self.results['supabase'] = {'status': 'OK', 'response_time': response.elapsed.total_seconds()}
                return True
            else:
                self.errors.append(f"Supabase health check failed: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            self.errors.append("Supabase connection timeout")
            return False
        except Exception as e:
            self.errors.append(f"Supabase connection error: {str(e)}")
            return False
    
    def check_notion_connection(self) -> bool:
        """Check Notion API connection"""
        self.logger.info("🔍 Checking Notion API connection...")
        
        if self.test_mode:
            self.logger.warning("⚠️ TEST MODE: Simulating Notion API failure")
            self.errors.append("TEST: Notion API connection failed")
            return False
        
        try:
            if not self.secrets['notion_api_key']:
                self.warnings.append("Missing Notion API key (NOTION_API_KEY)")
                return False
            
            # Test Notion API connection
            url = 'https://api.notion.com/v1/users/me'
            headers = {
                'Authorization': f"Bearer {self.secrets['notion_api_key']}",
                'Notion-Version': '2022-06-28'
            }
            
            response = requests.get(
                url, 
                headers=headers,
                timeout=self.config['health_check']['timeout_seconds']
            )
            
            if response.status_code == 200:
                self.logger.info("✅ Notion API connection successful")
                self.results['notion'] = {'status': 'OK', 'response_time': response.elapsed.total_seconds()}
                return True
            else:
                self.errors.append(f"Notion API health check failed: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            self.errors.append("Notion API connection timeout")
            return False
        except Exception as e:
            self.errors.append(f"Notion API connection error: {str(e)}")
            return False
    
    def check_unsynced_records(self) -> bool:
        """Check for unsynced records in decision_vault"""
        self.logger.info("🔍 Checking for unsynced records...")
        
        if self.test_mode:
            unsynced_count = 25  # Simulate unsynced records
            self.logger.warning(f"⚠️ TEST MODE: Simulating {unsynced_count} unsynced records")
            self.warnings.append(f"TEST: {unsynced_count} unsynced records detected")
            return False
        
        try:
            if not self.secrets['supabase_url'] or not self.secrets['supabase_key']:
                self.errors.append("Cannot check unsynced records: Missing Supabase credentials")
                return False
            
            # Query for unsynced records
            url = f"{self.secrets['supabase_url']}/rest/v1/decision_vault"
            headers = {
                'apikey': self.secrets['supabase_key'],
                'Authorization': f"Bearer {self.secrets['supabase_key']}",
                'Content-Type': 'application/json'
            }
            
            params = {
                'select': 'id',
                'notion_synced': 'eq.false'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                unsynced_records = response.json()
                unsynced_count = len(unsynced_records)
                
                max_warning = self.config['health_check']['max_unsynced_warning']
                max_error = self.config['health_check']['max_unsynced_error']
                
                if unsynced_count == 0:
                    self.logger.info("✅ No unsynced records found")
                    self.results['unsynced_records'] = {'count': 0, 'status': 'OK'}
                    return True
                elif unsynced_count <= max_warning:
                    self.warnings.append(f"{unsynced_count} unsynced records detected (threshold: {max_warning})")
                    self.results['unsynced_records'] = {'count': unsynced_count, 'status': 'WARNING'}
                    return False
                elif unsynced_count <= max_error:
                    self.errors.append(f"{unsynced_count} unsynced records detected (error threshold: {max_error})")
                    self.results['unsynced_records'] = {'count': unsynced_count, 'status': 'ERROR'}
                    return False
                else:
                    self.errors.append(f"CRITICAL: {unsynced_count} unsynced records (exceeds error threshold: {max_error})")
                    self.results['unsynced_records'] = {'count': unsynced_count, 'status': 'CRITICAL'}
                    return False
            else:
                self.errors.append(f"Failed to query unsynced records: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.errors.append(f"Error checking unsynced records: {str(e)}")
            return False
    
    def send_slack_notification(self, message: str) -> bool:
        """Send Slack notification"""
        try:
            if not self.secrets['slack_webhook_url']:
                self.logger.warning("⚠️ Slack webhook URL not configured")
                return False
            
            payload = {
                'text': f"🚨 Angles AI Universe™ Health Alert",
                'attachments': [{
                    'color': 'danger',
                    'title': 'Health Check Failed',
                    'text': message,
                    'ts': int(datetime.now(timezone.utc).timestamp())
                }]
            }
            
            response = requests.post(
                self.secrets['slack_webhook_url'],
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("✅ Slack notification sent successfully")
                return True
            else:
                self.logger.error(f"❌ Slack notification failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Slack notification error: {str(e)}")
            return False
    
    def send_email_notification(self, message: str) -> bool:
        """Send email notification"""
        if not EMAIL_AVAILABLE:
            self.logger.warning("⚠️ Email functionality not available")
            return False
            
        try:
            if not all([self.secrets['smtp_server'], self.secrets['smtp_username'], 
                       self.secrets['smtp_password'], self.secrets['email_recipient']]):
                self.logger.warning("⚠️ Email configuration incomplete")
                return False
            
            # Validate required fields are not None
            smtp_server = self.secrets['smtp_server']
            smtp_port = int(self.secrets['smtp_port'] or 587)
            smtp_username = self.secrets['smtp_username']
            smtp_password = self.secrets['smtp_password']
            email_recipient = self.secrets['email_recipient']
            
            if not all([smtp_server, smtp_username, smtp_password, email_recipient]):
                self.logger.warning("⚠️ Email credentials missing")
                return False
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = smtp_username
            msg['To'] = email_recipient
            msg['Subject'] = "🚨 Angles AI Universe™ Health Alert"
            
            msg.attach(MimeText(message, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            
            self.logger.info("✅ Email notification sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Email notification error: {str(e)}")
            return False
    
    def send_notification(self, message: str):
        """Send notification via configured method"""
        if not self.errors and not self.warnings:
            return  # No notifications needed for successful health checks
        
        notification_method = self.config['notifications']['method']
        
        if notification_method == 'slack' and self.config['notifications']['slack_enabled']:
            self.send_slack_notification(message)
        elif notification_method == 'email' and self.config['notifications']['email_enabled']:
            self.send_email_notification(message)
        else:
            self.logger.warning("⚠️ No notification method configured or enabled")
    
    def run_health_checks(self) -> int:
        """Run all health checks and return exit code"""
        self.logger.info("🚀 Starting Angles AI Universe™ Health Checks")
        self.logger.info("=" * 60)
        
        start_time = datetime.now(timezone.utc)
        
        # Run checks
        checks = [
            ("Supabase Connection", self.check_supabase_connection),
            ("Notion API Connection", self.check_notion_connection),
            ("Unsynced Records", self.check_unsynced_records)
        ]
        
        for check_name, check_func in checks:
            try:
                self.logger.info(f"Running {check_name}...")
                check_func()
            except Exception as e:
                self.errors.append(f"{check_name} failed with exception: {str(e)}")
                self.logger.error(f"❌ {check_name} failed: {str(e)}")
        
        # Calculate duration
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # Determine exit code
        if self.errors:
            exit_code = EXIT_ERRORS
            status = "ERRORS"
        elif self.warnings:
            exit_code = EXIT_WARNINGS
            status = "WARNINGS"
        else:
            exit_code = EXIT_OK
            status = "OK"
        
        # Log summary
        self.logger.info("=" * 60)
        self.logger.info(f"🏁 Health Check Complete - Status: {status}")
        self.logger.info(f"   Duration: {duration:.2f} seconds")
        self.logger.info(f"   Warnings: {len(self.warnings)}")
        self.logger.info(f"   Errors: {len(self.errors)}")
        
        if self.warnings:
            self.logger.warning("⚠️ Warnings:")
            for warning in self.warnings:
                self.logger.warning(f"   - {warning}")
        
        if self.errors:
            self.logger.error("❌ Errors:")
            for error in self.errors:
                self.logger.error(f"   - {error}")
        
        # Send notifications if needed
        if self.errors or self.warnings:
            notification_message = self._build_notification_message(status, duration)
            self.send_notification(notification_message)
        
        self.logger.info(f"Exit Code: {exit_code}")
        return exit_code
    
    def _build_notification_message(self, status: str, duration: float) -> str:
        """Build notification message"""
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        message = f"""
Angles AI Universe™ Health Check Failed

Status: {status}
Timestamp: {timestamp}
Duration: {duration:.2f} seconds

"""
        
        if self.warnings:
            message += f"Warnings ({len(self.warnings)}):\n"
            for warning in self.warnings:
                message += f"  • {warning}\n"
            message += "\n"
        
        if self.errors:
            message += f"Errors ({len(self.errors)}):\n"
            for error in self.errors:
                message += f"  • {error}\n"
            message += "\n"
        
        message += "Please check the system and resolve issues."
        
        return message

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Angles AI Universe™ Health Monitor')
    parser.add_argument('--test', action='store_true', help='Run in test mode (simulate failures)')
    
    args = parser.parse_args()
    
    try:
        monitor = HealthMonitor(test_mode=args.test)
        exit_code = monitor.run_health_checks()
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n🛑 Health check interrupted by user")
        sys.exit(EXIT_ERRORS)
    except Exception as e:
        print(f"💥 Health check failed with exception: {str(e)}")
        sys.exit(EXIT_ERRORS)

if __name__ == "__main__":
    main()