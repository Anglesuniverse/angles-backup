#!/usr/bin/env python3
"""
Git Helper Utilities for Angles AI Universe™ Memory System
Provides safe git operations with retry logic and token handling

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

logger = logging.getLogger('git_helpers')

class GitHelpers:
    """Safe git operations with retry logic and proper error handling"""
    
    def __init__(self, work_dir: Optional[Path] = None):
        """Initialize git helpers with working directory"""
        self.work_dir = work_dir or Path('.').resolve()
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.git_username = os.getenv('GIT_USERNAME', 'AI System')
        self.git_email = os.getenv('GIT_EMAIL', 'ai@anglesuniverse.com')
        self.repo_url = os.getenv('REPO_URL')
    
    def _run_command(self, command: List[str], timeout: int = 30, retries: int = 3) -> Dict[str, Any]:
        """Execute git command with retries and error handling"""
        for attempt in range(retries):
            try:
                logger.debug(f"Executing command (attempt {attempt + 1}): {' '.join(command)}")
                
                result = subprocess.run(
                    command,
                    cwd=self.work_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if result.returncode == 0:
                    logger.debug(f"Command succeeded: {result.stdout.strip()}")
                    return {
                        "success": True,
                        "stdout": result.stdout.strip(),
                        "stderr": result.stderr.strip(),
                        "returncode": result.returncode
                    }
                else:
                    logger.warning(f"Command failed (attempt {attempt + 1}): {result.stderr.strip()}")
                    
                    # Don't retry on certain errors
                    if "fatal: not a git repository" in result.stderr:
                        return {
                            "success": False,
                            "stdout": result.stdout.strip(),
                            "stderr": result.stderr.strip(),
                            "returncode": result.returncode,
                            "needs_init": True
                        }
                    
                    if attempt == retries - 1:  # Last attempt
                        return {
                            "success": False,
                            "stdout": result.stdout.strip(),
                            "stderr": result.stderr.strip(),
                            "returncode": result.returncode,
                            "error": f"Command failed after {retries} attempts"
                        }
                        
            except subprocess.TimeoutExpired:
                logger.error(f"Command timed out (attempt {attempt + 1})")
                if attempt == retries - 1:
                    return {
                        "success": False,
                        "error": f"Command timed out after {retries} attempts"
                    }
            except Exception as e:
                logger.error(f"Command execution error (attempt {attempt + 1}): {e}")
                if attempt == retries - 1:
                    return {
                        "success": False,
                        "error": f"Command execution failed: {e}"
                    }
        
        return {"success": False, "error": "Maximum retries exceeded"}
    
    def _prepare_repo_url_with_token(self) -> str:
        """Prepare repository URL with embedded token for HTTPS authentication"""
        if not self.repo_url or not self.repo_url.startswith('https://'):
            return self.repo_url or ''
        
        if not self.github_token:
            logger.warning("No GitHub token available for authentication")
            return self.repo_url
        
        # Parse URL and embed token
        parsed = urlparse(self.repo_url)
        authenticated_url = f"https://x-access-token:{self.github_token}@{parsed.netloc}{parsed.path}"
        
        return authenticated_url
    
    def ensure_repository(self) -> Dict[str, Any]:
        """
        Ensure git repository exists and is properly configured
        
        Returns:
            Dictionary with operation results
        """
        logger.info("Ensuring git repository is properly set up")
        
        # Check if already a git repository
        status_result = self._run_command(['git', 'status'])
        
        if status_result.get('needs_init', False) or not status_result['success']:
            logger.info("Initializing new git repository")
            
            # Initialize repository
            init_result = self._run_command(['git', 'init'])
            if not init_result['success']:
                return {
                    "success": False,
                    "error": f"Failed to initialize git repository: {init_result.get('error', 'Unknown error')}"
                }
            
            # Set user configuration
            config_commands = [
                ['git', 'config', 'user.name', self.git_username],
                ['git', 'config', 'user.email', self.git_email],
                ['git', 'config', 'pull.rebase', 'false']  # Use merge strategy
            ]
            
            for cmd in config_commands:
                result = self._run_command(cmd)
                if not result['success']:
                    logger.warning(f"Failed to set git config: {' '.join(cmd)}")
            
            # Add remote if repo_url is available
            if self.repo_url:
                repo_url_with_token = self._prepare_repo_url_with_token()
                add_remote_result = self._run_command(['git', 'remote', 'add', 'origin', repo_url_with_token])
                if not add_remote_result['success']:
                    logger.warning(f"Failed to add remote origin: {add_remote_result.get('error', 'Unknown error')}")
        else:
            logger.info("Git repository already exists")
        
        # Ensure remote origin is set correctly
        if self.repo_url:
            remote_result = self._run_command(['git', 'remote', 'get-url', 'origin'])
            if not remote_result['success']:
                # Add remote if missing
                repo_url_with_token = self._prepare_repo_url_with_token()
                add_remote_result = self._run_command(['git', 'remote', 'add', 'origin', repo_url_with_token])
                if not add_remote_result['success']:
                    logger.warning(f"Failed to add remote origin: {add_remote_result.get('error', 'Unknown error')}")
        
        logger.info("Git repository setup completed")
        return {"success": True, "message": "Git repository ready"}
    
    def safe_pull(self) -> Dict[str, Any]:
        """
        Safely pull latest changes from remote
        
        Returns:
            Dictionary with pull results
        """
        logger.info("Performing safe git pull")
        
        # First, fetch all refs
        fetch_result = self._run_command(['git', 'fetch', '--all'])
        if not fetch_result['success']:
            logger.warning(f"Fetch failed: {fetch_result.get('error', 'Unknown error')}")
        
        # Check if main branch exists locally
        branch_result = self._run_command(['git', 'branch', '--list', 'main'])
        
        if not branch_result['stdout'].strip():
            # No local main branch, create it from origin
            logger.info("Creating local main branch from origin")
            checkout_result = self._run_command(['git', 'checkout', '-B', 'main', 'origin/main'])
            if checkout_result['success']:
                return {"success": True, "message": "Created and checked out main branch"}
            else:
                # Try without origin reference
                checkout_result = self._run_command(['git', 'checkout', '-B', 'main'])
                if checkout_result['success']:
                    return {"success": True, "message": "Created main branch"}
                else:
                    return {
                        "success": False,
                        "error": f"Failed to create main branch: {checkout_result.get('error', 'Unknown error')}"
                    }
        
        # Pull latest changes
        pull_result = self._run_command(['git', 'pull', 'origin', 'main', '--no-edit'])
        
        if pull_result['success']:
            logger.info("Successfully pulled latest changes")
            return {"success": True, "message": "Successfully pulled latest changes"}
        else:
            # If pull fails, try to reset to origin/main
            logger.info("Pull failed, attempting to reset to origin/main")
            reset_result = self._run_command(['git', 'reset', '--hard', 'origin/main'])
            if reset_result['success']:
                logger.info("Successfully reset to origin/main")
                return {"success": True, "message": "Reset to origin/main"}
            else:
                return {
                    "success": False,
                    "error": f"Failed to pull or reset: {pull_result.get('error', 'Unknown error')}"
                }
    
    def get_commit_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get commit information for a specific file
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            Dictionary with commit information
        """
        log_result = self._run_command(['git', 'log', '-1', '--format=%H|%ai|%s', '--', file_path])
        
        if log_result['success'] and log_result['stdout']:
            parts = log_result['stdout'].split('|', 2)
            if len(parts) >= 3:
                return {
                    "success": True,
                    "commit_hash": parts[0],
                    "commit_date": parts[1],
                    "commit_message": parts[2],
                    "file_path": file_path
                }
        
        return {
            "success": False,
            "error": "No commit information found for file",
            "file_path": file_path
        }