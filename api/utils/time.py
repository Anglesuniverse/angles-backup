"""
Angles OS™ Time Utilities
Consistent timestamp handling across the platform
"""
from datetime import datetime, timezone
from typing import Optional

def utc_now() -> datetime:
    """Get current UTC timestamp"""
    return datetime.now(timezone.utc)

def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format timestamp for API responses"""
    if dt is None:
        dt = utc_now()
    return dt.isoformat()

def parse_timestamp(ts_str: str) -> datetime:
    """Parse ISO timestamp string"""
    return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))