#!/usr/bin/env python3
"""
Post-Restore GitHub Push for Angles AI Universe™ Memory System
Checks for file changes after restore and pushes updates to GitHub

This script:
1. Checks for file changes after restore process
2. Commits changes with "Post-restore sync update" message if any exist
3. Pushes to the angles-backup repository
4. Logs all actions to logs/post_restore_push.log

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from logging.handlers import RotatingFileHandler

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from notion_backup_logger import create_notion_logger

def setup_logging() -> logging.Logger:
    """Setup post-restore push logging"""
    # Ensure logs directory exists
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger('post_restore_push')
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Rotating file handler
    file_handler = RotatingFileHandler(
        'logs/post_restore_push.log',
        maxBytes=1024*1024,  # 1MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class PostRestorePush:
    """Handles post-restore Git operations"""
    
    def __init__(self):
        """Initialize post-restore push handler"""
        self.logger = setup_logging()
        self.start_time = datetime.now()
        
        # Load Git environment variables
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.git_username = os.getenv('GIT_USERNAME', 'AI System')
        self.git_email = os.getenv('GIT_EMAIL', 'ai@anglesuniverse.com')
        self.repo_url = os.getenv('REPO_URL')
        self.notion_logger = create_notion_logger()
        
        self.logger.info("🔄 POST-RESTORE GITHUB PUSH INITIALIZED")
        self.logger.info("=" * 50)
    
    def _run_git_command(self, command: List[str], timeout: int = 60) -> Dict[str, Any]:
        """Execute git command with error handling"""
        try:
            self.logger.debug(f"Executing: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_git_status(self) -> Dict[str, Any]:
        """Check git status for changes"""
        self.logger.info("🔍 Checking git status for changes...")
        
        try:
            # Check git status
            status_result = self._run_git_command(['git', 'status', '--porcelain'])
            
            if not status_result['success']:
                return {
                    "success": False,
                    "error": f"Git status failed: {status_result.get('error', 'Unknown error')}"
                }
            
            changes = status_result['stdout']
            
            if not changes.strip():
                self.logger.info("✅ No changes detected")
                return {
                    "success": True,
                    "has_changes": False,
                    "changes": []
                }
            
            # Parse changes
            change_lines = [line.strip() for line in changes.split('\n') if line.strip()]
            self.logger.info(f"📋 Detected {len(change_lines)} changes:")
            
            for line in change_lines:
                self.logger.info(f"  {line}")
            
            return {
                "success": True,
                "has_changes": True,
                "changes": change_lines,
                "raw_status": changes
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def stage_changes(self) -> Dict[str, Any]:
        """Stage all changes for commit"""
        self.logger.info("📥 Staging changes...")
        
        try:
            # Add all changes
            add_result = self._run_git_command(['git', 'add', '.'])
            
            if not add_result['success']:
                return {
                    "success": False,
                    "error": f"Failed to stage changes: {add_result.get('stderr', 'Unknown error')}"
                }
            
            # Verify staged changes
            staged_result = self._run_git_command(['git', 'status', '--porcelain', '--cached'])
            
            if staged_result['success']:
                staged_files = staged_result['stdout'].strip()
                if staged_files:
                    staged_lines = [line.strip() for line in staged_files.split('\n') if line.strip()]
                    self.logger.info(f"✅ Staged {len(staged_lines)} changes")
                    for line in staged_lines[:10]:  # Show first 10
                        self.logger.info(f"  {line}")
                    if len(staged_lines) > 10:
                        self.logger.info(f"  ... and {len(staged_lines) - 10} more")
                else:
                    return {
                        "success": False,
                        "error": "No changes staged after git add"
                    }
            
            return {"success": True}
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def commit_changes(self) -> Dict[str, Any]:
        """Commit staged changes with post-restore message"""
        self.logger.info("💾 Committing changes...")
        
        try:
            commit_message = "Post-restore sync update"
            timestamp = self.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')
            
            # Extended commit message
            full_message = f"{commit_message}\n\nAutomatic post-restore synchronization\nTimestamp: {timestamp}\nSource: post_restore_push.py"
            
            # Configure git user (in case not set)
            config_commands = [
                ['git', 'config', 'user.name', self.git_username],
                ['git', 'config', 'user.email', self.git_email]
            ]
            
            for cmd in config_commands:
                config_result = self._run_git_command(cmd)
                if not config_result['success']:
                    self.logger.warning(f"Failed to set git config: {' '.join(cmd)}")
            
            # Commit changes
            commit_result = self._run_git_command(['git', 'commit', '-m', full_message])
            
            if not commit_result['success']:
                return {
                    "success": False,
                    "error": f"Commit failed: {commit_result.get('stderr', 'Unknown error')}"
                }
            
            # Get commit hash
            hash_result = self._run_git_command(['git', 'rev-parse', 'HEAD'])
            commit_hash = hash_result['stdout'][:8] if hash_result['success'] else 'unknown'
            
            self.logger.info(f"✅ Committed changes: {commit_hash}")
            self.logger.info(f"📝 Message: {commit_message}")
            
            return {
                "success": True,
                "commit_hash": commit_hash,
                "commit_message": commit_message
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def push_to_repository(self) -> Dict[str, Any]:
        """Push committed changes to GitHub repository"""
        self.logger.info("🚀 Pushing to GitHub repository...")
        
        try:
            # First, try a regular push
            push_result = self._run_git_command(['git', 'push', 'origin', 'main'], timeout=120)
            
            if push_result['success']:
                self.logger.info("✅ Push successful")
                return {"success": True}
            
            # If push fails, check for specific errors and handle them
            error_msg = push_result.get('stderr', '')
            
            if "fetch first" in error_msg or "Updates were rejected" in error_msg:
                self.logger.info("🔄 Remote has changes - attempting pull and merge...")
                
                # Pull with merge strategy
                pull_result = self._run_git_command(['git', 'pull', 'origin', 'main', '--no-edit'])
                
                if pull_result['success']:
                    self.logger.info("✅ Successfully pulled remote changes")
                    
                    # Try push again
                    retry_push = self._run_git_command(['git', 'push', 'origin', 'main'])
                    if retry_push['success']:
                        self.logger.info("✅ Push successful after merge")
                        return {"success": True}
                    else:
                        return {
                            "success": False,
                            "error": f"Push failed after merge: {retry_push.get('stderr', 'Unknown error')}"
                        }
                else:
                    self.logger.warning("Pull failed, attempting safe force push...")
                    
                    # Use force-with-lease as safe fallback
                    force_result = self._run_git_command(['git', 'push', '--force-with-lease', 'origin', 'main'])
                    if force_result['success']:
                        self.logger.info("✅ Safe force push successful")
                        return {"success": True}
                    else:
                        return {
                            "success": False,
                            "error": f"Force push failed: {force_result.get('stderr', 'Unknown error')}"
                        }
            else:
                return {
                    "success": False,
                    "error": f"Push failed: {error_msg}"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_commit_link(self) -> Optional[str]:
        """Generate GitHub commit link"""
        try:
            # Get current commit hash
            hash_result = self._run_git_command(['git', 'rev-parse', 'HEAD'])
            if not hash_result['success']:
                return None
            
            commit_hash = hash_result['stdout']
            
            # Get repository URL
            if not self.repo_url:
                return None
            
            # Convert to GitHub URL format
            if 'github.com' in self.repo_url:
                # Remove .git extension and authentication
                repo_url = self.repo_url.replace('.git', '')
                if '@' in repo_url:
                    repo_url = 'https://github.com/' + repo_url.split('@github.com/')[-1]
                
                return f"{repo_url}/commit/{commit_hash}"
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Could not generate commit link: {e}")
            return None
    
    def run_post_restore_push(self) -> Dict[str, Any]:
        """Run complete post-restore push process"""
        self.logger.info("🚀 STARTING POST-RESTORE PUSH PROCESS")
        
        try:
            # Step 1: Check for changes
            status_result = self.check_git_status()
            if not status_result['success']:
                return {
                    "success": False,
                    "error": status_result['error'],
                    "stage": "status_check"
                }
            
            # If no changes, return early
            if not status_result['has_changes']:
                duration = (datetime.now() - self.start_time).total_seconds()
                self.logger.info("✅ No changes to push - system is up to date")
                
                # Log to Notion
                self.notion_logger.log_post_restore_push(
                    success=True,
                    changes_count=0,
                    duration=duration,
                    details="No changes to push - system is up to date"
                )
                
                return {
                    "success": True,
                    "no_changes": True,
                    "message": "No changes to push",
                    "duration": duration
                }
            
            # Step 2: Stage changes
            stage_result = self.stage_changes()
            if not stage_result['success']:
                return {
                    "success": False,
                    "error": stage_result['error'],
                    "stage": "staging"
                }
            
            # Step 3: Commit changes
            commit_result = self.commit_changes()
            if not commit_result['success']:
                return {
                    "success": False,
                    "error": commit_result['error'],
                    "stage": "commit"
                }
            
            # Step 4: Push to repository
            push_result = self.push_to_repository()
            if not push_result['success']:
                return {
                    "success": False,
                    "error": push_result['error'],
                    "stage": "push"
                }
            
            # Step 5: Generate results
            duration = (datetime.now() - self.start_time).total_seconds()
            commit_link = self.get_commit_link()
            
            self.logger.info("=" * 50)
            self.logger.info("✅ POST-RESTORE PUSH COMPLETED SUCCESSFULLY")
            self.logger.info(f"Duration: {duration:.2f} seconds")
            self.logger.info(f"Changes: {len(status_result['changes'])}")
            self.logger.info(f"Commit: {commit_result.get('commit_hash', 'unknown')}")
            if commit_link:
                self.logger.info(f"Link: {commit_link}")
            self.logger.info("=" * 50)
            
            # Log to Notion
            push_details = f"Committed and pushed {len(status_result['changes'])} changes"
            if commit_result.get('commit_hash'):
                push_details += f" (Commit: {commit_result['commit_hash']})"
            
            self.notion_logger.log_post_restore_push(
                success=True,
                changes_count=len(status_result['changes']),
                commit_link=commit_link,
                duration=duration,
                details=push_details
            )
            
            return {
                "success": True,
                "changes_count": len(status_result['changes']),
                "commit_hash": commit_result.get('commit_hash'),
                "commit_message": commit_result.get('commit_message'),
                "commit_link": commit_link,
                "duration": duration,
                "changes": status_result['changes']
            }
            
        except Exception as e:
            duration = (datetime.now() - self.start_time).total_seconds()
            self.logger.error(f"💥 Post-restore push failed: {e}")
            
            # Log failure to Notion
            self.notion_logger.log_post_restore_push(
                success=False,
                changes_count=0,
                duration=duration,
                error=str(e),
                details="Post-restore push failed with exception"
            )
            
            return {
                "success": False,
                "error": str(e),
                "stage": "unknown",
                "duration": duration
            }

def main():
    """Main entry point for post-restore push"""
    try:
        print()
        print("🔄 ANGLES AI UNIVERSE™ POST-RESTORE PUSH")
        print("=" * 45)
        print("Checking for changes after restore...")
        print()
        
        # Run post-restore push
        push_handler = PostRestorePush()
        result = push_handler.run_post_restore_push()
        
        # Print results
        print()
        print("🏁 POST-RESTORE PUSH RESULTS:")
        print("=" * 35)
        
        if result['success']:
            if result.get('no_changes'):
                print("✅ Status: No changes to push")
                print("📝 Result: System is up to date")
            else:
                print("✅ Status: Changes pushed successfully")
                print(f"📊 Changes: {result.get('changes_count', 0)}")
                print(f"💾 Commit: {result.get('commit_hash', 'unknown')}")
                if result.get('commit_link'):
                    print(f"🔗 Link: {result['commit_link']}")
        else:
            print("❌ Status: Push failed")
            print(f"🚫 Error: {result.get('error', 'Unknown error')}")
            print(f"📍 Stage: {result.get('stage', 'unknown')}")
        
        print(f"⏱️ Duration: {result.get('duration', 0):.1f}s")
        print(f"📝 Logs: logs/post_restore_push.log")
        print()
        
        # Exit with appropriate code
        sys.exit(0 if result['success'] else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Push interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Push failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()