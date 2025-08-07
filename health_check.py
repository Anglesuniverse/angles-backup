#!/usr/bin/env python3
"""
Angles AI Universe™ Automated Health Check System
Comprehensive health verification for Supabase, Notion API, and GitHub repository

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import json
import requests
import logging
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

class SystemHealthChecker:
    """Comprehensive system health checker for all external services"""
    
    def __init__(self):
        """Initialize health checker"""
        self.setup_logging()
        self.load_environment()
        self.results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'supabase': {'status': 'unknown', 'details': {}},
            'notion': {'status': 'unknown', 'details': {}},
            'github': {'status': 'unknown', 'details': {}},
            'overall_status': 'unknown'
        }
        
        self.logger.info("🔍 Angles AI Universe™ Health Checker Initialized")
    
    def setup_logging(self):
        """Setup logging to system_health.log"""
        os.makedirs("logs/active", exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger('system_health')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler for system_health.log
        log_file = "logs/active/system_health.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter with timestamp
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def load_environment(self):
        """Load all required environment variables"""
        self.env = {
            'supabase_url': os.getenv('SUPABASE_URL'),
            'supabase_key': os.getenv('SUPABASE_KEY'),
            'notion_token': os.getenv('NOTION_TOKEN'),
            'notion_database_id': os.getenv('NOTION_DATABASE_ID'),
            'github_token': os.getenv('GITHUB_TOKEN'),
            'github_username': os.getenv('GITHUB_USERNAME', 'angles-ai'),
            'github_repo': 'angles-backup'
        }
        
        # Log environment status (without exposing secrets)
        self.logger.info("📋 Environment Variables Status:")
        for key, value in self.env.items():
            status = "✅ Set" if value else "❌ Missing"
            self.logger.info(f"   {key}: {status}")
    
    def check_supabase_health(self) -> bool:
        """Check Supabase connection and table integrity"""
        self.logger.info("🔍 Checking Supabase health...")
        
        try:
            if not self.env['supabase_url'] or not self.env['supabase_key']:
                raise Exception("Missing Supabase credentials")
            
            headers = {
                'apikey': self.env['supabase_key'],
                'Authorization': f"Bearer {self.env['supabase_key']}",
                'Content-Type': 'application/json'
            }
            
            # Test basic connectivity
            health_url = f"{self.env['supabase_url']}/rest/v1/"
            response = requests.get(health_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                raise Exception(f"API connectivity failed: HTTP {response.status_code}")
            
            # Test decision_vault table access
            table_url = f"{self.env['supabase_url']}/rest/v1/decision_vault"
            params = {'select': 'id,decision,type,date', 'limit': '5'}
            
            response = requests.get(table_url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                record_count = len(data)
                
                self.results['supabase'] = {
                    'status': 'healthy',
                    'details': {
                        'api_responsive': True,
                        'table_accessible': True,
                        'sample_record_count': record_count,
                        'response_time_ms': int(response.elapsed.total_seconds() * 1000)
                    }
                }
                
                self.logger.info(f"✅ Supabase healthy - {record_count} records accessible")
                return True
            else:
                raise Exception(f"Table access failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.results['supabase'] = {
                'status': 'unhealthy',
                'details': {'error': str(e)}
            }
            self.logger.error(f"❌ Supabase health check failed: {str(e)}")
            return False
    
    def check_notion_health(self) -> bool:
        """Check Notion API connection and database access"""
        self.logger.info("🔍 Checking Notion API health...")
        
        try:
            if not self.env['notion_token']:
                raise Exception("Missing Notion API token")
            
            headers = {
                'Authorization': f"Bearer {self.env['notion_token']}",
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
            
            # Test API connectivity
            user_url = 'https://api.notion.com/v1/users/me'
            response = requests.get(user_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                raise Exception(f"API connectivity failed: HTTP {response.status_code}")
            
            user_data = response.json()
            
            # Test database access if database ID is provided
            if self.env['notion_database_id']:
                db_url = f"https://api.notion.com/v1/databases/{self.env['notion_database_id']}"
                response = requests.get(db_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    db_data = response.json()
                    database_title = db_data.get('title', [{}])[0].get('plain_text', 'Unknown')
                    
                    self.results['notion'] = {
                        'status': 'healthy',
                        'details': {
                            'api_responsive': True,
                            'user_name': user_data.get('name', 'Unknown'),
                            'database_accessible': True,
                            'database_title': database_title,
                            'response_time_ms': int(response.elapsed.total_seconds() * 1000)
                        }
                    }
                    
                    self.logger.info(f"✅ Notion healthy - Database '{database_title}' accessible")
                    return True
                else:
                    raise Exception(f"Database access failed: HTTP {response.status_code}")
            else:
                self.results['notion'] = {
                    'status': 'healthy',
                    'details': {
                        'api_responsive': True,
                        'user_name': user_data.get('name', 'Unknown'),
                        'database_accessible': False,
                        'note': 'No database ID configured'
                    }
                }
                
                self.logger.info("✅ Notion API healthy - No database configured")
                return True
                
        except Exception as e:
            self.results['notion'] = {
                'status': 'unhealthy',
                'details': {'error': str(e)}
            }
            self.logger.error(f"❌ Notion health check failed: {str(e)}")
            return False
    
    def check_github_health(self) -> bool:
        """Check GitHub repository access and permissions"""
        self.logger.info("🔍 Checking GitHub repository health...")
        
        try:
            if not self.env['github_token']:
                raise Exception("Missing GitHub token")
            
            headers = {
                'Authorization': f"token {self.env['github_token']}",
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Test API connectivity
            user_url = 'https://api.github.com/user'
            response = requests.get(user_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                raise Exception(f"GitHub API failed: HTTP {response.status_code}")
            
            user_data = response.json()
            username = user_data.get('login', 'unknown')
            
            # Test repository access
            repo_url = f"https://api.github.com/repos/{self.env['github_username']}/{self.env['github_repo']}"
            response = requests.get(repo_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                repo_data = response.json()
                
                # Check permissions
                permissions = repo_data.get('permissions', {})
                can_push = permissions.get('push', False)
                can_pull = permissions.get('pull', False)
                
                # Test actual repository content access
                contents_url = f"{repo_url}/contents"
                response = requests.get(contents_url, headers=headers, timeout=10)
                
                contents_accessible = response.status_code == 200
                file_count = len(response.json()) if contents_accessible else 0
                
                self.results['github'] = {
                    'status': 'healthy' if can_push and can_pull else 'limited',
                    'details': {
                        'api_responsive': True,
                        'authenticated_user': username,
                        'repository_accessible': True,
                        'push_permission': can_push,
                        'pull_permission': can_pull,
                        'contents_accessible': contents_accessible,
                        'file_count': file_count,
                        'repository_name': repo_data.get('full_name', 'unknown')
                    }
                }
                
                status_icon = "✅" if can_push and can_pull else "⚠️"
                self.logger.info(f"{status_icon} GitHub repository accessible - Push: {can_push}, Pull: {can_pull}")
                return True
                
            elif response.status_code == 404:
                raise Exception(f"Repository '{self.env['github_username']}/{self.env['github_repo']}' not found")
            else:
                raise Exception(f"Repository access failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.results['github'] = {
                'status': 'unhealthy',
                'details': {'error': str(e)}
            }
            self.logger.error(f"❌ GitHub health check failed: {str(e)}")
            return False
    
    def run_comprehensive_health_check(self) -> bool:
        """Run all health checks and determine overall system status"""
        self.logger.info("🚀 Starting Comprehensive System Health Check")
        self.logger.info("=" * 70)
        
        start_time = datetime.now(timezone.utc)
        
        # Run all health checks
        supabase_healthy = self.check_supabase_health()
        notion_healthy = self.check_notion_health()
        github_healthy = self.check_github_health()
        
        # Calculate overall status
        all_healthy = supabase_healthy and notion_healthy and github_healthy
        critical_failure = not supabase_healthy  # Supabase is critical
        
        if all_healthy:
            overall_status = 'healthy'
            status_icon = "✅"
        elif critical_failure:
            overall_status = 'critical'
            status_icon = "🚨"
        else:
            overall_status = 'degraded'
            status_icon = "⚠️"
        
        # Calculate duration
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # Update results
        self.results['overall_status'] = overall_status
        self.results['duration_seconds'] = duration
        self.results['checks_completed'] = {
            'supabase': supabase_healthy,
            'notion': notion_healthy,
            'github': github_healthy
        }
        
        # Log summary
        self.logger.info("=" * 70)
        self.logger.info(f"{status_icon} System Health Check Complete")
        self.logger.info(f"   Overall Status: {overall_status.upper()}")
        self.logger.info(f"   Duration: {duration:.2f} seconds")
        self.logger.info(f"   Supabase: {'✅' if supabase_healthy else '❌'}")
        self.logger.info(f"   Notion: {'✅' if notion_healthy else '❌'}")
        self.logger.info(f"   GitHub: {'✅' if github_healthy else '❌'}")
        
        # Write detailed results to JSON
        self.write_health_report()
        
        return all_healthy
    
    def write_health_report(self):
        """Write detailed health report to JSON file"""
        try:
            report_file = f"logs/active/health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            self.logger.info(f"📄 Detailed health report saved: {report_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to write health report: {str(e)}")

def main():
    """Main entry point for health check"""
    try:
        checker = SystemHealthChecker()
        is_healthy = checker.run_comprehensive_health_check()
        
        # Exit with appropriate code
        if is_healthy:
            print("\n🎉 All systems healthy!")
            sys.exit(0)
        else:
            print("\n⚠️ System health issues detected - check logs for details")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Health check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Health check failed with exception: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()