#!/usr/bin/env python3
"""
Git Backup Agent for Angles AI Universe™
Handles safe GitHub backups of sanitized exports and logs

This module provides functionality to:
- Initialize git repository if needed
- Commit sanitized data exports
- Push to GitHub with proper authentication
- Handle first-push scenarios and idempotence

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import subprocess
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger('git_backup')

class GitBackupAgent:
    """
    Handles GitHub backups of sanitized data exports
    Never exposes secrets, always uses environment variables
    """
    
    def __init__(self):
        """Initialize the Git Backup Agent with environment configuration"""
        logger.info("Initializing Git Backup Agent")
        
        # Load environment variables
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.git_username = os.getenv('GIT_USERNAME')
        self.git_email = os.getenv('GIT_EMAIL') 
        self.repo_url = os.getenv('REPO_URL')
        
        # Validate required environment variables
        self._validate_environment()
        
        # Set working directory
        self.work_dir = Path('.').resolve()
        
        logger.info("Git Backup Agent initialized successfully")
    
    def _validate_environment(self) -> None:
        """Validate that all required environment variables are present"""
        required_vars = {
            'GITHUB_TOKEN': self.github_token,
            'GIT_USERNAME': self.git_username,
            'GIT_EMAIL': self.git_email,
            'REPO_URL': self.repo_url
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("All required Git environment variables validated")
    
    def _run_command(self, command: List[str], timeout: int = 30, retries: int = 3) -> Dict[str, Any]:
        """
        Execute a git command with retries and error handling
        
        Args:
            command: Git command as list of strings
            timeout: Command timeout in seconds
            retries: Number of retry attempts
            
        Returns:
            Dictionary with command results
        """
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
                    if "fatal: not a git repository" not in result.stderr:
                        if attempt == retries - 1:  # Last attempt
                            return {
                                "success": False,
                                "stdout": result.stdout.strip(),
                                "stderr": result.stderr.strip(), 
                                "returncode": result.returncode,
                                "error": f"Command failed after {retries} attempts"
                            }
                    else:
                        # Git repo doesn't exist, this is expected for first run
                        return {
                            "success": False,
                            "stdout": result.stdout.strip(),
                            "stderr": result.stderr.strip(),
                            "returncode": result.returncode,
                            "needs_init": True
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
        """
        Prepare repository URL with embedded token for HTTPS authentication
        Never logs or exposes the token
        """
        if not self.repo_url or not self.repo_url.startswith('https://'):
            return self.repo_url or ''  # SSH or other protocols
        
        # Parse URL and embed token
        parsed = urlparse(self.repo_url)
        
        # Construct URL with embedded token
        authenticated_url = f"https://{self.github_token}@{parsed.netloc}{parsed.path}"
        
        return authenticated_url
    
    def _push_with_conflict_resolution(self) -> Dict[str, Any]:
        """
        Push changes with proper conflict resolution
        Handles cases where remote has changes we don't have locally
        """
        logger.info("Attempting to push changes")
        
        # First, try a regular push
        push_result = self._run_command(['git', 'push', 'origin', 'main'])
        
        if push_result['success']:
            logger.info("Push successful")
            return {"success": True, "message": "Successfully pushed to GitHub"}
        
        # Check if it's a "no upstream branch" error
        if "no upstream branch" in push_result['stderr']:
            logger.info("Setting upstream branch and pushing")
            upstream_result = self._run_command(['git', 'push', '--set-upstream', 'origin', 'main'])
            if upstream_result['success']:
                return {"success": True, "message": "Successfully pushed with upstream"}
            else:
                # If upstream push also fails, continue to conflict resolution
                push_result = upstream_result
        
        # Check if it's a conflict that needs pull
        if "fetch first" in push_result['stderr'] or "Updates were rejected" in push_result['stderr']:
            logger.info("Remote has changes - attempting to pull and merge")
            
            # Try to pull remote changes
            pull_result = self._run_command(['git', 'pull', 'origin', 'main', '--no-edit'])
            
            if pull_result['success']:
                logger.info("Successfully pulled remote changes")
                # Now try pushing again
                retry_push = self._run_command(['git', 'push', 'origin', 'main'])
                if retry_push['success']:
                    logger.info("Successfully pushed after pull")
                    return {"success": True, "message": "Successfully pushed after resolving conflicts"}
                else:
                    logger.warning(f"Push failed even after pull: {retry_push.get('stderr', '')}")
            else:
                logger.warning(f"Pull failed: {pull_result.get('stderr', '')}")
                # If pull fails, try force-with-lease as safe fallback
                logger.info("Attempting force push with lease (safe)")
                force_result = self._run_command(['git', 'push', '--force-with-lease', 'origin', 'main'])
                if force_result['success']:
                    logger.info("Successfully force-pushed with lease")
                    return {"success": True, "message": "Successfully force-pushed (safe)"}
                else:
                    logger.error(f"Force push with lease also failed: {force_result.get('stderr', '')}")
        
        # If all else fails, return the original error
        return {
            "success": False,
            "error": f"Failed to push changes: {push_result.get('stderr', push_result.get('error', 'Unknown error'))}"
        }
    
    def initialize_repository(self) -> Dict[str, Any]:
        """
        Initialize git repository if needed and set up user configuration
        
        Returns:
            Dictionary with initialization results
        """
        logger.info("Initializing git repository")
        
        # Check if already a git repository
        status_result = self._run_command(['git', 'status'])
        
        if not status_result.get('needs_init', False) and status_result['success']:
            logger.info("Git repository already initialized")
        else:
            # Initialize new repository
            logger.info("Creating new git repository")
            init_result = self._run_command(['git', 'init'])
            if not init_result['success']:
                return {
                    "success": False,
                    "error": f"Failed to initialize git repository: {init_result.get('error', 'Unknown error')}"
                }
        
        # Set user configuration
        config_commands = [
            ['git', 'config', 'user.name', self.git_username],
            ['git', 'config', 'user.email', self.git_email]
        ]
        
        for cmd in config_commands:
            result = self._run_command(cmd)
            if not result['success']:
                logger.warning(f"Failed to set git config: {' '.join(cmd)}")
        
        # Add remote if it doesn't exist
        remote_result = self._run_command(['git', 'remote', 'get-url', 'origin'])
        if not remote_result['success']:
            logger.info("Adding remote origin")
            repo_url_with_token = self._prepare_repo_url_with_token()
            add_remote_result = self._run_command(['git', 'remote', 'add', 'origin', repo_url_with_token])
            if not add_remote_result['success']:
                return {
                    "success": False,
                    "error": f"Failed to add remote origin: {add_remote_result.get('error', 'Unknown error')}"
                }
        
        logger.info("Git repository initialized successfully")
        return {"success": True, "message": "Git repository ready"}
    
    def commit_and_push(self, files_to_add: List[str], commit_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Add, commit, and push specified files to GitHub
        
        Args:
            files_to_add: List of file patterns to add
            commit_message: Custom commit message (auto-generated if None)
            
        Returns:
            Dictionary with operation results
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if commit_message is None:
            commit_message = f"[auto] memory sync {timestamp}"
        
        logger.info(f"Committing and pushing files: {files_to_add}")
        
        try:
            # Add files
            for file_pattern in files_to_add:
                add_result = self._run_command(['git', 'add', file_pattern])
                if not add_result['success']:
                    logger.warning(f"Failed to add {file_pattern}: {add_result.get('error', 'Unknown error')}")
            
            # Check if there are changes to commit
            status_result = self._run_command(['git', 'status', '--porcelain'])
            if not status_result['success']:
                return {
                    "success": False,
                    "error": f"Failed to check git status: {status_result.get('error', 'Unknown error')}"
                }
            
            if not status_result['stdout'].strip():
                logger.info("No changes to commit")
                return {
                    "success": True,
                    "message": "No changes to commit",
                    "skipped": True
                }
            
            # Commit changes
            commit_result = self._run_command(['git', 'commit', '-m', commit_message])
            if not commit_result['success']:
                return {
                    "success": False,
                    "error": f"Failed to commit changes: {commit_result.get('error', 'Unknown error')}"
                }
            
            # Push changes - with proper conflict resolution
            push_success = self._push_with_conflict_resolution()
            if not push_success['success']:
                return push_success
            
            logger.info("Successfully committed and pushed to GitHub")
            return {
                "success": True,
                "message": f"Committed and pushed: {commit_message}",
                "commit_message": commit_message,
                "files_added": files_to_add
            }
            
        except Exception as e:
            error_msg = f"Error during commit and push: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def backup_files(self, export_files: List[str], log_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Main backup function - commits and pushes export and log files
        
        Args:
            export_files: List of export files to backup
            log_files: List of log files to backup (optional)
            
        Returns:
            Dictionary with backup results
        """
        logger.info("Starting GitHub backup process")
        
        try:
            # Initialize repository
            init_result = self.initialize_repository()
            if not init_result['success']:
                return init_result
            
            # Prepare files to add
            files_to_add = []
            
            # Add export files
            for export_file in export_files:
                export_path = Path(export_file)
                if export_path.exists():
                    files_to_add.append(str(export_file))
                    logger.info(f"Added export file: {export_file}")
                else:
                    logger.warning(f"Export file not found: {export_file}")
            
            # Add log files if specified
            if log_files:
                for log_file in log_files:
                    log_path = Path(log_file)
                    if log_path.exists():
                        files_to_add.append(str(log_file))
                        logger.info(f"Added log file: {log_file}")
                    else:
                        logger.warning(f"Log file not found: {log_file}")
            
            if not files_to_add:
                return {
                    "success": True,
                    "message": "No files to backup",
                    "skipped": True
                }
            
            # Commit and push
            commit_result = self.commit_and_push(files_to_add)
            
            if commit_result['success']:
                logger.info("GitHub backup completed successfully")
                return {
                    "success": True,
                    "message": "GitHub backup completed",
                    "files_backed_up": len(files_to_add),
                    "commit_message": commit_result.get('commit_message', ''),
                    "details": commit_result
                }
            else:
                return commit_result
                
        except Exception as e:
            error_msg = f"GitHub backup failed: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

def main():
    """Main entry point for git backup agent"""
    try:
        logger.info("Starting Git Backup Agent")
        
        # Create backup agent
        backup_agent = GitBackupAgent()
        
        # Look for files to backup
        export_files = list(Path('export').glob('*.json'))
        log_files = list(Path('logs').glob('*.log'))
        
        if not export_files and not log_files:
            logger.info("No files found to backup")
            print("No files to backup")
            return
        
        # Run backup
        result = backup_agent.backup_files([str(f) for f in export_files], [str(f) for f in log_files])
        
        if result['success']:
            logger.info(f"Backup successful: {result['message']}")
            print(f"✓ Backup completed: {result.get('files_backed_up', 0)} files")
        else:
            logger.error(f"Backup failed: {result.get('error', 'Unknown error')}")
            print(f"✗ Backup failed: {result.get('error', 'Unknown error')}")
            exit(1)
            
    except Exception as e:
        logger.error(f"Git backup agent failed: {e}")
        print(f"✗ Git backup agent failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()