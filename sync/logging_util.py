#!/usr/bin/env python3
"""
Logging utilities for Supabase-Notion sync service
Provides structured logging with rotation for Angles AI Universe™

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import json
import logging
import logging.handlers
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional


class SyncLogger:
    """Enhanced logger for sync operations"""
    
    def __init__(self, log_file: str = "logs/sync.log"):
        """Initialize sync logger with rotation"""
        
        # Ensure logs directory exists
        Path(log_file).parent.mkdir(exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger('sync_service')
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Rotating file handler (10MB max, 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional context"""
        if kwargs:
            message += f" | Context: {json.dumps(kwargs, default=str)}"
        self.logger.info(message)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional context"""
        if kwargs:
            message += f" | Context: {json.dumps(kwargs, default=str)}"
        self.logger.warning(message)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception and context"""
        if error:
            message += f" | Error: {error}"
        if kwargs:
            message += f" | Context: {json.dumps(kwargs, default=str)}"
        self.logger.error(message)
    
    def sync_start(self, sync_type: str = "bidirectional"):
        """Log sync operation start"""
        self.info(f"🔄 Starting {sync_type} sync operation")
    
    def sync_complete(self, stats: Dict[str, Any]):
        """Log sync operation completion with stats"""
        self.info(
            f"✅ Sync completed successfully",
            duration=stats.get('duration', 0),
            supabase_records=stats.get('supabase_count', 0),
            notion_records=stats.get('notion_count', 0),
            created=stats.get('created', 0),
            updated=stats.get('updated', 0),
            errors=stats.get('errors', 0)
        )
    
    def sync_error(self, error: Exception, operation: str = "sync"):
        """Log sync operation error"""
        self.error(f"❌ {operation.title()} operation failed", error=error)


def save_health_status(health_file: str, stats: Dict[str, Any]):
    """Save sync health status to JSON file"""
    
    # Ensure logs directory exists
    Path(health_file).parent.mkdir(exist_ok=True)
    
    health_data = {
        'last_run': datetime.now(timezone.utc).isoformat(),
        'status': 'success' if stats.get('errors', 0) == 0 else 'error',
        'duration_seconds': stats.get('duration', 0),
        'statistics': {
            'supabase_records': stats.get('supabase_count', 0),
            'notion_records': stats.get('notion_count', 0),
            'created': stats.get('created', 0),
            'updated': stats.get('updated', 0),
            'deleted': stats.get('deleted', 0),
            'errors': stats.get('errors', 0)
        },
        'error_details': stats.get('error_details', [])
    }
    
    try:
        with open(health_file, 'w') as f:
            json.dump(health_data, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save health status: {e}")


def load_health_status(health_file: str) -> Optional[Dict[str, Any]]:
    """Load sync health status from JSON file"""
    
    try:
        if Path(health_file).exists():
            with open(health_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load health status: {e}")
    
    return None


# Global logger instance
_logger: Optional[SyncLogger] = None


def get_logger(log_file: str = "logs/sync.log") -> SyncLogger:
    """Get global logger instance"""
    global _logger
    if _logger is None:
        _logger = SyncLogger(log_file)
    return _logger