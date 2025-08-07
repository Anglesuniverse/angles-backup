#!/usr/bin/env python3
"""
Notion Backup & Restore Logger for Angles AI Universe™
Logs backup and restore operations to Notion database

This module provides:
- Notion API integration for backup/restore logging
- Structured logging entries with timestamps, status, and links
- Integration with existing Notion database
- Support for backup, restore, and post-restore push operations

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

try:
    from notion_client import Client as NotionClient
except ImportError:
    NotionClient = None

@dataclass
class BackupRestoreLogEntry:
    """Data structure for backup/restore log entries"""
    timestamp: str
    action_type: str  # "Backup", "Restore", "Post-Restore Push"
    items_processed: int
    status: str  # "Success" or "Failure"
    github_commit_link: Optional[str] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    details: Optional[str] = None

class NotionBackupLogger:
    """Handles logging backup and restore operations to Notion"""
    
    def __init__(self):
        """Initialize Notion backup logger"""
        self.logger = logging.getLogger('notion_backup_logger')
        
        # Load environment variables
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.notion_database_id = os.getenv('NOTION_DATABASE_ID')
        
        # Initialize Notion client
        self.notion = None
        if self.notion_token and self.notion_database_id and NotionClient:
            try:
                self.notion = NotionClient(auth=self.notion_token)
                self.logger.info("✅ Notion backup logger initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Notion client: {e}")
        else:
            missing = []
            if not self.notion_token:
                missing.append("NOTION_TOKEN")
            if not self.notion_database_id:
                missing.append("NOTION_DATABASE_ID")
            if not NotionClient:
                missing.append("notion-client library")
            
            self.logger.warning(f"Notion logging disabled - missing: {', '.join(missing)}")
    
    def _create_notion_page_data(self, entry: BackupRestoreLogEntry) -> Dict[str, Any]:
        """Create Notion page data structure"""
        
        # Create title with action type and status
        title = f"{entry.action_type} - {entry.status}"
        
        # Create message content
        message_parts = [
            f"Action: {entry.action_type}",
            f"Status: {entry.status}",
            f"Items Processed: {entry.items_processed}",
            f"Timestamp: {entry.timestamp}"
        ]
        
        if entry.duration_seconds:
            message_parts.append(f"Duration: {entry.duration_seconds:.2f} seconds")
        
        if entry.github_commit_link:
            message_parts.append(f"GitHub Link: {entry.github_commit_link}")
        
        if entry.error_message:
            message_parts.append(f"Error: {entry.error_message}")
        
        if entry.details:
            message_parts.append(f"Details: {entry.details}")
        
        message_content = "\n".join(message_parts)
        
        # Create tags based on action type and status
        tags = [entry.action_type.lower(), entry.status.lower()]
        if "backup" in entry.action_type.lower():
            tags.append("backup")
        if "restore" in entry.action_type.lower():
            tags.append("restore")
        
        # Create Notion page data
        page_data = {
            "parent": {"database_id": self.notion_database_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": title}}]
                },
                "Message": {
                    "rich_text": [{"text": {"content": message_content}}]
                },
                "Date": {
                    "date": {"start": entry.timestamp[:10]}  # YYYY-MM-DD format
                },
                "Tag": {
                    "multi_select": [{"name": tag} for tag in tags]
                }
            }
        }
        
        return page_data
    
    def log_operation(self, entry: BackupRestoreLogEntry) -> bool:
        """Log a backup/restore operation to Notion"""
        if not self.notion:
            self.logger.warning("Notion client not available - skipping log entry")
            return True  # Don't fail the operation
        
        try:
            self.logger.info(f"📝 Logging {entry.action_type} operation to Notion...")
            
            # Create page data
            page_data = self._create_notion_page_data(entry)
            
            # Send to Notion
            result = self.notion.pages.create(**page_data)
            
            if result:
                self.logger.info(f"✅ Successfully logged to Notion: {entry.action_type} - {entry.status}")
                return True
            else:
                self.logger.error("❌ Failed to create Notion page")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error logging to Notion: {e}")
            return False
    
    def log_backup(self, success: bool, items_processed: int, commit_link: Optional[str] = None, 
                   duration: Optional[float] = None, error: Optional[str] = None, 
                   details: Optional[str] = None) -> bool:
        """Log a backup operation"""
        entry = BackupRestoreLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action_type="Backup",
            items_processed=items_processed,
            status="Success" if success else "Failure",
            github_commit_link=commit_link,
            duration_seconds=duration,
            error_message=error,
            details=details
        )
        
        return self.log_operation(entry)
    
    def log_restore(self, success: bool, items_processed: int, source_commit_link: Optional[str] = None,
                    duration: Optional[float] = None, error: Optional[str] = None,
                    details: Optional[str] = None) -> bool:
        """Log a restore operation"""
        entry = BackupRestoreLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action_type="Restore",
            items_processed=items_processed,
            status="Success" if success else "Failure",
            github_commit_link=source_commit_link,
            duration_seconds=duration,
            error_message=error,
            details=details
        )
        
        return self.log_operation(entry)
    
    def log_post_restore_push(self, success: bool, changes_count: int, commit_link: Optional[str] = None,
                              duration: Optional[float] = None, error: Optional[str] = None,
                              details: Optional[str] = None) -> bool:
        """Log a post-restore push operation"""
        entry = BackupRestoreLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action_type="Post-Restore Push",
            items_processed=changes_count,
            status="Success" if success else "Failure",
            github_commit_link=commit_link,
            duration_seconds=duration,
            error_message=error,
            details=details
        )
        
        return self.log_operation(entry)
    
    def log_sanity_check(self, success: bool, files_checked: int, errors_found: int = 0,
                         warnings_found: int = 0, duration: Optional[float] = None,
                         error: Optional[str] = None, details: Optional[str] = None) -> bool:
        """Log a sanity check operation"""
        entry = BackupRestoreLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action_type="Sanity Check",
            items_processed=files_checked,
            status="Success" if success else "Failure",
            github_commit_link=None,
            duration_seconds=duration,
            error_message=error,
            details=details
        )
        
        return self.log_operation(entry)
    
    def log_restore_sanity_check(self, success: bool, files_checked: int, restore_files_count: int = 0,
                                 errors_found: int = 0, warnings_found: int = 0, duration: Optional[float] = None,
                                 error: Optional[str] = None, details: Optional[str] = None) -> bool:
        """Log a restore sanity check operation"""
        entry = BackupRestoreLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action_type="Restore Sanity Check",
            items_processed=files_checked,
            status="Success" if success else "Failure",
            github_commit_link=None,
            duration_seconds=duration,
            error_message=error,
            details=details
        )
        
        return self.log_operation(entry)
    
    def log_memory_change(self, file_changed: str, action: str, timestamp: str, 
                          git_commit_id: str, file_type: str, encrypted: bool = False,
                          details: Optional[str] = None) -> bool:
        """Log a memory state change operation"""
        entry = BackupRestoreLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action_type=f"Memory {action}",
            items_processed=1,
            status="Success",
            github_commit_link=f"Commit: {git_commit_id}",
            duration_seconds=None,
            error_message=None,
            details=details or f"{action} {file_type} file: {file_changed} {'(encrypted)' if encrypted else ''}"
        )
        
        return self.log_operation(entry)

# Convenience function for easy import
def create_notion_logger() -> NotionBackupLogger:
    """Create a Notion backup logger instance"""
    return NotionBackupLogger()