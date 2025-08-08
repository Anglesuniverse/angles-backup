#!/usr/bin/env python3
"""
Angles AI Universe™ Git Helpers
Safe Git operations for backup and restore functionality

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import subprocess
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

def setup_logging():
    """Setup logging for git helpers"""
    logger = logging.getLogger('git_helpers')
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

class GitHelpers:
    """Safe Git operations wrapper"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.logger = setup_logging()
    
    def run_git_command(self, args: List[str], timeout: int = 30) -> Dict[str, Any]:
        """Run git command safely with error handling"""
        cmd = ['git'] + args
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
                'command': ' '.join(cmd)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': f'Command timed out after {timeout}s',
                'command': ' '.join(cmd)
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'command': ' '.join(cmd)
            }
    
    def init_repo_if_needed(self) -> bool:
        """Initialize git repository if not already initialized"""
        if (self.repo_path / '.git').exists():
            self.logger.info("✅ Git repository already initialized")
            return True
        
        self.logger.info("🔄 Initializing git repository...")
        result = self.run_git_command(['init'])
        
        if result['success']:
            self.logger.info("✅ Git repository initialized")
            return True
        else:
            self.logger.error(f"❌ Failed to initialize git repository: {result['stderr']}")
            return False
    
    def set_identity(self, username: str, email: str) -> bool:
        """Set git user identity"""
        self.logger.info(f"👤 Setting git identity: {username} <{email}>")
        
        # Set username
        result_user = self.run_git_command(['config', 'user.name', username])
        result_email = self.run_git_command(['config', 'user.email', email])
        
        if result_user['success'] and result_email['success']:
            self.logger.info("✅ Git identity configured")
            return True
        else:
            errors = []
            if not result_user['success']:
                errors.append(f"username: {result_user['stderr']}")
            if not result_email['success']:
                errors.append(f"email: {result_email['stderr']}")
            
            self.logger.error(f"❌ Failed to set git identity: {'; '.join(errors)}")
            return False
    
    def add_files(self, file_paths: List[str]) -> bool:
        """Add files to git staging area"""
        if not file_paths:
            return True
        
        self.logger.info(f"📂 Adding {len(file_paths)} files to git...")
        
        # Add files one by one for better error handling
        failed_files = []
        for file_path in file_paths:
            if not os.path.exists(file_path):
                self.logger.warning(f"⚠️ File not found, skipping: {file_path}")
                continue
            
            result = self.run_git_command(['add', file_path])
            if not result['success']:
                failed_files.append(f"{file_path}: {result['stderr']}")
                self.logger.warning(f"⚠️ Failed to add {file_path}: {result['stderr']}")
        
        if failed_files:
            self.logger.warning(f"⚠️ Some files failed to add: {len(failed_files)} errors")
            # Don't fail completely if some files couldn't be added
        
        success_count = len(file_paths) - len(failed_files)
        self.logger.info(f"✅ Added {success_count}/{len(file_paths)} files to git")
        return True
    
    def commit_changes(self, message: str) -> bool:
        """Commit staged changes"""
        self.logger.info(f"💾 Committing changes: {message}")
        
        # Check if there are changes to commit
        status_result = self.run_git_command(['status', '--porcelain'])
        if not status_result['success']:
            self.logger.error(f"❌ Failed to check git status: {status_result['stderr']}")
            return False
        
        if not status_result['stdout'].strip():
            self.logger.info("ℹ️ No changes to commit")
            return True
        
        # Commit changes
        result = self.run_git_command(['commit', '-m', message])
        
        if result['success']:
            # Extract commit hash if available
            commit_hash = ""
            if 'commit' in result['stdout']:
                commit_hash = result['stdout'].split()[1][:8]
            
            self.logger.info(f"✅ Changes committed successfully {commit_hash}")
            return True
        else:
            self.logger.error(f"❌ Failed to commit changes: {result['stderr']}")
            return False
    
    def push_changes(self, remote: str = "origin", branch: str = "main") -> bool:
        """Push changes to remote repository"""
        self.logger.info(f"🚀 Pushing changes to {remote}/{branch}...")
        
        result = self.run_git_command(['push', remote, branch], timeout=60)
        
        if result['success']:
            self.logger.info("✅ Changes pushed successfully")
            return True
        else:
            # Check if it's an authentication issue
            if 'authentication' in result['stderr'].lower() or 'permission denied' in result['stderr'].lower():
                self.logger.error("❌ Push failed: Authentication error - check GITHUB_TOKEN")
            else:
                self.logger.error(f"❌ Failed to push changes: {result['stderr']}")
            return False
    
    def safe_pull_with_rebase(self, remote: str = "origin", branch: str = "main") -> bool:
        """Safely pull changes with rebase strategy"""
        self.logger.info(f"⬇️ Pulling changes from {remote}/{branch} with rebase...")
        
        # Fetch first
        fetch_result = self.run_git_command(['fetch', remote])
        if not fetch_result['success']:
            self.logger.error(f"❌ Failed to fetch from remote: {fetch_result['stderr']}")
            return False
        
        # Check if remote branch exists
        branch_check = self.run_git_command(['rev-parse', '--verify', f'{remote}/{branch}'])
        if not branch_check['success']:
            self.logger.warning(f"⚠️ Remote branch {remote}/{branch} not found, skipping pull")
            return True
        
        # Check for local changes
        status_result = self.run_git_command(['status', '--porcelain'])
        if status_result['success'] and status_result['stdout'].strip():
            self.logger.info("📦 Stashing local changes before pull...")
            stash_result = self.run_git_command(['stash', 'push', '-m', 'Auto-stash before pull'])
            if not stash_result['success']:
                self.logger.error(f"❌ Failed to stash changes: {stash_result['stderr']}")
                return False
            
            stashed = True
        else:
            stashed = False
        
        # Pull with rebase
        pull_result = self.run_git_command(['pull', '--rebase', remote, branch])
        
        if pull_result['success']:
            self.logger.info("✅ Pull with rebase successful")
            
            # Restore stashed changes if any
            if stashed:
                self.logger.info("📦 Restoring stashed changes...")
                stash_pop_result = self.run_git_command(['stash', 'pop'])
                if not stash_pop_result['success']:
                    self.logger.warning(f"⚠️ Failed to restore stashed changes: {stash_pop_result['stderr']}")
                    self.logger.info("💡 You may need to manually resolve: git stash pop")
            
            return True
        else:
            self.logger.error(f"❌ Pull with rebase failed: {pull_result['stderr']}")
            
            # Try to restore stashed changes on failure
            if stashed:
                self.logger.info("📦 Attempting to restore stashed changes after failed pull...")
                self.run_git_command(['stash', 'pop'])
            
            return False
    
    def commit_and_push(self, file_paths: List[str], message: str, 
                       remote: str = "origin", branch: str = "main") -> Dict[str, Any]:
        """Complete commit and push workflow"""
        self.logger.info("🔄 Starting commit and push workflow...")
        
        result = {
            'success': False,
            'steps': [],
            'errors': []
        }
        
        # Step 1: Add files
        if self.add_files(file_paths):
            result['steps'].append('add_files')
        else:
            result['errors'].append('Failed to add files')
            return result
        
        # Step 2: Commit changes
        if self.commit_changes(message):
            result['steps'].append('commit')
        else:
            result['errors'].append('Failed to commit changes')
            return result
        
        # Step 3: Push changes
        if self.push_changes(remote, branch):
            result['steps'].append('push')
            result['success'] = True
        else:
            result['errors'].append('Failed to push changes')
            return result
        
        self.logger.info("✅ Commit and push workflow completed successfully")
        return result
    
    def get_repo_status(self) -> Dict[str, Any]:
        """Get current repository status"""
        status = {
            'is_repo': False,
            'has_remote': False,
            'branch': None,
            'uncommitted_changes': False,
            'remote_url': None
        }
        
        # Check if it's a git repo
        if not (self.repo_path / '.git').exists():
            return status
        
        status['is_repo'] = True
        
        # Get current branch
        branch_result = self.run_git_command(['branch', '--show-current'])
        if branch_result['success']:
            status['branch'] = branch_result['stdout']
        
        # Check for uncommitted changes
        status_result = self.run_git_command(['status', '--porcelain'])
        if status_result['success']:
            status['uncommitted_changes'] = bool(status_result['stdout'].strip())
        
        # Get remote URL
        remote_result = self.run_git_command(['remote', 'get-url', 'origin'])
        if remote_result['success']:
            status['has_remote'] = True
            status['remote_url'] = remote_result['stdout']
        
        return status

# Convenience functions for backward compatibility
def init_repo_if_needed(repo_path: str = ".") -> bool:
    """Initialize git repository if needed"""
    git_helper = GitHelpers(repo_path)
    return git_helper.init_repo_if_needed()

def set_identity(username: str, email: str, repo_path: str = ".") -> bool:
    """Set git user identity"""
    git_helper = GitHelpers(repo_path)
    return git_helper.set_identity(username, email)

def commit_and_push(file_paths: List[str], message: str, repo_path: str = ".") -> Dict[str, Any]:
    """Commit and push files"""
    git_helper = GitHelpers(repo_path)
    return git_helper.commit_and_push(file_paths, message)

def safe_pull_with_rebase(repo_path: str = ".", remote: str = "origin", branch: str = "main") -> bool:
    """Safely pull with rebase"""
    git_helper = GitHelpers(repo_path)
    return git_helper.safe_pull_with_rebase(remote, branch)