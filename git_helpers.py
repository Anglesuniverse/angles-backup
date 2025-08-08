#!/usr/bin/env python3
"""
Angles AI Universe™ Safe Git Operations Helper
Standardized Git operations with conflict resolution and security

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import subprocess
import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Import alert manager
try:
    from alerts.notify import AlertManager
except ImportError:
    AlertManager = None

class GitHelper:
    """Safe Git operations with conflict resolution and security"""
    
    def __init__(self, repo_path: str = "."):
        """Initialize Git helper"""
        self.repo_path = Path(repo_path).resolve()
        self.setup_logging()
        self.load_environment()
        self.alert_manager = AlertManager() if AlertManager else None
        
        # Security patterns - never commit these
        self.security_patterns = [
            r'.*\.env$',
            r'.*\.env\..*$',
            r'.*secret.*',
            r'.*token.*',
            r'.*key.*',
            r'.*password.*',
            r'.*credential.*',
            r'.*api[_-]?key.*'
        ]
        
        self.logger.info(f"🔐 Git Helper initialized for {self.repo_path}")
    
    def setup_logging(self):
        """Setup logging for Git helper"""
        os.makedirs("logs/active", exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger('git_helper')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/active/git_operations.log"
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
        """Load Git-related environment variables"""
        self.env = {
            'github_token': os.getenv('GITHUB_TOKEN'),
            'repo_url': os.getenv('REPO_URL', ''),
            'github_username': os.getenv('GITHUB_USERNAME', 'angles-ai')
        }
        
        # Parse repo info
        if self.env['repo_url']:
            parts = self.env['repo_url'].rstrip('/').split('/')
            if len(parts) >= 2:
                self.github_owner = parts[-2]
                self.github_repo = parts[-1].replace('.git', '')
            else:
                self.github_owner = self.env['github_username']
                self.github_repo = 'angles-backup'
        else:
            self.github_owner = self.env['github_username']
            self.github_repo = 'angles-backup'
        
        self.logger.info(f"📋 Git config: {self.github_owner}/{self.github_repo}")
    
    def run_git_command(self, args: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
        """Run Git command safely with proper error handling"""
        try:
            # Ensure we're in the right directory
            cmd = ['git'] + args
            self.logger.debug(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            error_msg = f"Git command timed out: {' '.join(args)}"
            self.logger.error(f"❌ {error_msg}")
            return False, "", error_msg
        except Exception as e:
            error_msg = f"Git command failed: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return False, "", error_msg
    
    def check_git_status(self) -> Dict[str, Any]:
        """Check current Git repository status"""
        status_info = {
            'is_repo': False,
            'has_remote': False,
            'branch': 'unknown',
            'uncommitted_changes': False,
            'untracked_files': [],
            'modified_files': [],
            'ahead_behind': {'ahead': 0, 'behind': 0}
        }
        
        # Check if this is a Git repo
        success, stdout, stderr = self.run_git_command(['status', '--porcelain'])
        if not success:
            self.logger.warning("⚠️ Not a Git repository or Git not available")
            return status_info
        
        status_info['is_repo'] = True
        
        # Parse status output
        status_lines = stdout.strip().split('\n') if stdout.strip() else []
        for line in status_lines:
            if line.startswith('??'):
                status_info['untracked_files'].append(line[3:])
            elif line.startswith(' M') or line.startswith('M '):
                status_info['modified_files'].append(line[3:])
        
        status_info['uncommitted_changes'] = len(status_lines) > 0
        
        # Get current branch
        success, stdout, stderr = self.run_git_command(['branch', '--show-current'])
        if success:
            status_info['branch'] = stdout.strip()
        
        # Check remote
        success, stdout, stderr = self.run_git_command(['remote', 'get-url', 'origin'])
        status_info['has_remote'] = success
        
        # Check ahead/behind status
        if status_info['has_remote']:
            success, stdout, stderr = self.run_git_command(['rev-list', '--left-right', '--count', 'HEAD...origin/main'])
            if success and stdout.strip():
                try:
                    ahead, behind = map(int, stdout.strip().split())
                    status_info['ahead_behind'] = {'ahead': ahead, 'behind': behind}
                except:
                    pass
        
        return status_info
    
    def validate_security(self, files: List[str]) -> Tuple[bool, List[str]]:
        """Validate files against security patterns"""
        violations = []
        
        for file_path in files:
            file_lower = file_path.lower()
            
            # Check against security patterns
            for pattern in self.security_patterns:
                if re.match(pattern, file_lower, re.IGNORECASE):
                    violations.append(file_path)
                    break
            
            # Check file content for secrets (basic check)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Look for common secret patterns
                        secret_indicators = [
                            r'api[_-]?key\s*[=:]\s*["\'][^"\'
]{10,}["\']',
                            r'secret\s*[=:]\s*["\'][^"\'
]{10,}["\']',
                            r'token\s*[=:]\s*["\'][^"\'
]{10,}["\']',
                            r'password\s*[=:]\s*["\'][^"\'
]{3,}["\']'
                        ]
                        
                        for pattern in secret_indicators:
                            if re.search(pattern, content, re.IGNORECASE):
                                if file_path not in violations:
                                    violations.append(file_path)
                                break
                except:
                    # Skip files that can't be read
                    pass
        
        is_safe = len(violations) == 0
        
        if violations:
            self.logger.warning(f"⚠️ Security violations detected: {violations}")
        
        return is_safe, violations
    
    def ensure_gitignore(self):
        """Ensure .gitignore has security patterns"""
        gitignore_path = self.repo_path / '.gitignore'
        
        required_patterns = [
            '# Environment and secrets',
            '.env',
            '.env.*',
            '*.key',
            '*.pem',
            '*secret*',
            '*token*',
            '*credential*',
            '',
            '# Logs with potential secrets',
            'logs/active/',
            '*.log',
            '',
            '# Temporary files',
            '*.tmp',
            '*.temp',
            '__pycache__/',
            '*.pyc'
        ]
        
        try:
            # Read existing .gitignore
            existing_content = ""
            if gitignore_path.exists():
                with open(gitignore_path, 'r') as f:
                    existing_content = f.read()
            
            # Add missing patterns
            lines_to_add = []
            for pattern in required_patterns:
                if pattern not in existing_content:
                    lines_to_add.append(pattern)
            
            if lines_to_add:
                with open(gitignore_path, 'a') as f:
                    f.write('\n' + '\n'.join(lines_to_add))
                
                self.logger.info(f"✅ Updated .gitignore with {len(lines_to_add)} security patterns")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update .gitignore: {str(e)}")
            return False
    
    def preflight_checks(self) -> Dict[str, Any]:
        """Run preflight checks before Git operations"""
        self.logger.info("🚀 Running preflight checks...")
        
        checks = {
            'git_repo': False,
            'remote_configured': False,
            'fetch_success': False,
            'merge_needed': False,
            'conflicts_detected': False,
            'security_violations': [],
            'status': 'unknown'
        }
        
        # Check Git status
        git_status = self.check_git_status()
        checks['git_repo'] = git_status['is_repo']
        checks['remote_configured'] = git_status['has_remote']
        
        if not checks['git_repo']:
            checks['status'] = 'no_repo'
            return checks
        
        # Ensure .gitignore is secure
        self.ensure_gitignore()
        
        # Fetch latest changes
        if checks['remote_configured']:
            self.logger.info("📥 Fetching latest changes...")
            success, stdout, stderr = self.run_git_command(['fetch', '--prune', 'origin'])
            checks['fetch_success'] = success
            
            if not success:
                self.logger.error(f"❌ Fetch failed: {stderr}")
            
            # Check if merge is needed
            if git_status['ahead_behind']['behind'] > 0:
                checks['merge_needed'] = True
                self.logger.info(f"🔄 {git_status['ahead_behind']['behind']} commits behind origin")
        
        # Check for uncommitted changes
        if git_status['uncommitted_changes']:
            all_files = git_status['untracked_files'] + git_status['modified_files']
            is_safe, violations = self.validate_security(all_files)
            checks['security_violations'] = violations
            
            if not is_safe:
                checks['status'] = 'security_violation'
            elif checks['merge_needed']:
                checks['status'] = 'merge_needed'
            else:
                checks['status'] = 'ready'
        else:
            checks['status'] = 'clean'
        
        self.logger.info(f"📋 Preflight status: {checks['status']}")
        return checks
    
    def create_backup_branch(self) -> Optional[str]:
        """Create backup branch with timestamp"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        branch_name = f"backup/{timestamp}"
        
        self.logger.info(f"🔀 Creating backup branch: {branch_name}")
        
        success, stdout, stderr = self.run_git_command(['checkout', '-b', branch_name])
        
        if success:
            # Push backup branch
            success_push, stdout_push, stderr_push = self.run_git_command(['push', 'origin', branch_name])
            if success_push:
                self.logger.info(f"✅ Backup branch created and pushed: {branch_name}")
                return branch_name
            else:
                self.logger.error(f"❌ Failed to push backup branch: {stderr_push}")
        else:
            self.logger.error(f"❌ Failed to create backup branch: {stderr}")
        
        return None
    
    def create_pull_request(self, branch_name: str, title: str, description: str) -> Optional[str]:
        """Create pull request using GitHub API"""
        if not self.env['github_token']:
            self.logger.warning("⚠️ GitHub token not available - cannot create PR")
            return None
        
        try:
            import requests
            
            headers = {
                'Authorization': f"token {self.env['github_token']}",
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            }
            
            pr_data = {
                'title': title,
                'body': description,
                'head': branch_name,
                'base': 'main'
            }
            
            url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/pulls"
            response = requests.post(url, headers=headers, json=pr_data, timeout=15)
            
            if response.status_code == 201:
                pr = response.json()
                pr_url = pr['html_url']
                self.logger.info(f"✅ Pull request created: {pr_url}")
                return pr_url
            else:
                self.logger.error(f"❌ Failed to create PR: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ PR creation failed: {str(e)}")
            return None
    
    def safe_commit_and_push(self, files: List[str], message: str, 
                           force_push: bool = False) -> Dict[str, Any]:
        """Safely commit and push changes with conflict resolution"""
        self.logger.info(f"💾 Safe commit and push: {message}")
        
        result = {
            'success': False,
            'commit_hash': None,
            'push_success': False,
            'backup_branch': None,
            'pull_request': None,
            'conflicts_resolved': False,
            'security_violations': [],
            'errors': []
        }
        
        try:
            # Run preflight checks
            preflight = self.preflight_checks()
            
            if preflight['status'] == 'security_violation':
                result['security_violations'] = preflight['security_violations']
                result['errors'].append(f"Security violations: {preflight['security_violations']}")
                return result
            
            # Validate specific files for security
            is_safe, violations = self.validate_security(files)
            if not is_safe:
                result['security_violations'] = violations
                result['errors'].append(f"Security violations in files: {violations}")
                return result
            
            # Add files
            for file_path in files:
                success, stdout, stderr = self.run_git_command(['add', file_path])
                if not success:
                    result['errors'].append(f"Failed to add {file_path}: {stderr}")
                    return result
            
            # Commit changes
            commit_msg = f"{message} - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
            success, stdout, stderr = self.run_git_command(['commit', '-m', commit_msg])
            
            if not success:
                if 'nothing to commit' in stderr:
                    self.logger.info("✅ No changes to commit")
                    result['success'] = True
                    return result
                else:
                    result['errors'].append(f"Commit failed: {stderr}")
                    return result
            
            # Get commit hash
            success, stdout, stderr = self.run_git_command(['rev-parse', 'HEAD'])
            if success:
                result['commit_hash'] = stdout.strip()
            
            # Handle conflicts and push
            if preflight['merge_needed'] and not force_push:
                # Create backup branch first
                backup_branch = self.create_backup_branch()
                result['backup_branch'] = backup_branch
                
                # Switch back to main and try merge
                self.run_git_command(['checkout', 'main'])
                
                # Try to pull and merge
                success, stdout, stderr = self.run_git_command(['pull', 'origin', 'main'])
                
                if not success and 'conflict' in stderr.lower():
                    # Create PR instead of forcing
                    if backup_branch:
                        pr_title = f"Auto-merge conflict resolution - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
                        pr_description = f"Automated commit with conflict resolution needed.\n\nOriginal commit: {commit_msg}\n\nConflict details:\n{stderr}"
                        
                        pr_url = self.create_pull_request(backup_branch, pr_title, pr_description)
                        result['pull_request'] = pr_url
                        
                        if self.alert_manager:
                            self.alert_manager.send_alert(
                                title="Git Conflict Detected - PR Created",
                                message=f"Merge conflict detected during commit. Created PR for manual resolution: {pr_url}",
                                severity="warning",
                                tags=['git', 'conflict', 'pr']
                            )
                        
                        result['conflicts_resolved'] = True
                        result['success'] = True
                        return result
            
            # Push changes
            push_args = ['push', 'origin', 'main']
            if force_push:
                push_args.insert(1, '--force-with-lease')
            
            success, stdout, stderr = self.run_git_command(push_args)
            
            if success:
                result['push_success'] = True
                result['success'] = True
                self.logger.info(f"✅ Successfully pushed commit {result['commit_hash'][:8]}")
            else:
                result['errors'].append(f"Push failed: {stderr}")
                self.logger.error(f"❌ Push failed: {stderr}")
            
            return result
            
        except Exception as e:
            error_msg = f"Commit and push failed: {str(e)}"
            result['errors'].append(error_msg)
            self.logger.error(f"❌ {error_msg}")
            
            # Send alert for critical failure
            if self.alert_manager:
                self.alert_manager.send_alert(
                    title="Git Operation Critical Failure",
                    message=f"Critical failure during commit and push: {str(e)}",
                    severity="critical",
                    tags=['git', 'critical', 'failure']
                )
            
            return result
    
    def quick_commit(self, files: List[str], message: str) -> bool:
        """Quick commit for automated operations"""
        result = self.safe_commit_and_push(files, message)
        return result['success']
    
    def get_git_info(self) -> Dict[str, Any]:
        """Get comprehensive Git repository information"""
        info = {
            'repo_path': str(self.repo_path),
            'status': self.check_git_status(),
            'last_commit': None,
            'remote_url': None,
            'branch_list': []
        }
        
        # Get last commit info
        success, stdout, stderr = self.run_git_command(['log', '-1', '--format=%H|%an|%ad|%s'])
        if success and stdout.strip():
            parts = stdout.strip().split('|')
            if len(parts) >= 4:
                info['last_commit'] = {
                    'hash': parts[0],
                    'author': parts[1],
                    'date': parts[2],
                    'message': parts[3]
                }
        
        # Get remote URL
        success, stdout, stderr = self.run_git_command(['remote', 'get-url', 'origin'])
        if success:
            info['remote_url'] = stdout.strip()
        
        # Get branch list
        success, stdout, stderr = self.run_git_command(['branch', '-a'])
        if success:
            info['branch_list'] = [line.strip().replace('* ', '') for line in stdout.split('\n') if line.strip()]
        
        return info

def main():
    """Main entry point for Git helper testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Safe Git operations helper')
    parser.add_argument('--status', action='store_true', help='Show Git status')
    parser.add_argument('--preflight', action='store_true', help='Run preflight checks')
    parser.add_argument('--commit', help='Commit message for test commit')
    parser.add_argument('--files', nargs='+', help='Files to commit')
    parser.add_argument('--info', action='store_true', help='Show Git repository info')
    
    args = parser.parse_args()
    
    try:
        git_helper = GitHelper()
        
        if args.status:
            status = git_helper.check_git_status()
            print("\n📋 Git Status:")
            for key, value in status.items():
                print(f"  {key}: {value}")
        
        elif args.preflight:
            preflight = git_helper.preflight_checks()
            print("\n🚀 Preflight Checks:")
            for key, value in preflight.items():
                print(f"  {key}: {value}")
        
        elif args.commit and args.files:
            result = git_helper.safe_commit_and_push(args.files, args.commit)
            print("\n💾 Commit Results:")
            for key, value in result.items():
                print(f"  {key}: {value}")
        
        elif args.info:
            info = git_helper.get_git_info()
            print("\n📊 Git Repository Info:")
            for key, value in info.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for sub_key, sub_value in value.items():
                        print(f"    {sub_key}: {sub_value}")
                else:
                    print(f"  {key}: {value}")
        
        else:
            print("Git helper initialized. Use --help for available commands.")
    
    except Exception as e:
        print(f"💥 Git helper failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()