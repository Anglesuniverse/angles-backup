#!/usr/bin/env python3
"""
Configuration module for Supabase-Notion bidirectional sync
Handles environment variables and constants for Angles AI Universe™

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class SyncConfig:
    """Configuration settings for bidirectional sync"""
    
    # Supabase configuration
    supabase_url: str
    supabase_service_key: str
    
    # Notion configuration  
    notion_api_key: str
    notion_database_id: str
    
    # Sync settings
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_delay: float = 0.5
    
    # Logging
    log_file: str = "logs/sync.log"
    health_file: str = "logs/last_success.json"
    
    # Sync frequency (minutes)
    sync_interval: int = 15


def load_config() -> SyncConfig:
    """Load configuration from environment variables"""
    
    # Required environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    notion_api_key = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
    notion_database_id = os.getenv('NOTION_DATABASE_ID')
    
    # Validate required variables
    missing_vars = []
    if not supabase_url:
        missing_vars.append('SUPABASE_URL')
    if not supabase_service_key:
        missing_vars.append('SUPABASE_SERVICE_ROLE_KEY')
    if not notion_api_key:
        missing_vars.append('NOTION_API_KEY or NOTION_TOKEN')
    if not notion_database_id:
        missing_vars.append('NOTION_DATABASE_ID')
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return SyncConfig(
        supabase_url=supabase_url,
        supabase_service_key=supabase_service_key,
        notion_api_key=notion_api_key,
        notion_database_id=notion_database_id,
        batch_size=int(os.getenv('SYNC_BATCH_SIZE', '100')),
        max_retries=int(os.getenv('SYNC_MAX_RETRIES', '3')),
        sync_interval=int(os.getenv('SYNC_INTERVAL_MINUTES', '15'))
    )


# Global config instance
_config: Optional[SyncConfig] = None


def get_config() -> SyncConfig:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


# Constants
SUPABASE_TABLE = 'decision_vault'
NOTION_PROPERTY_MAPPING = {
    'decision': 'Decision',      # Title
    'type': 'Type',             # Multi-select
    'date': 'Date',             # Date
    'checksum': 'Checksum',     # Rich text
    'synced': 'Synced'          # Checkbox (optional)
}

# Supported decision types
DECISION_TYPES = ['Policy', 'Architecture', 'Ops', 'UX', 'Other']