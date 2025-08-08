"""
Utility functions for Angles AI Universe™
Common helpers for timestamps, checksums, JSON handling, and retries
"""

import json
import hashlib
import time
import logging
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable


logger = logging.getLogger(__name__)


def safe_json_dumps(obj: Any, default=str) -> str:
    """Safely serialize object to JSON"""
    try:
        return json.dumps(obj, default=default, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"JSON serialization failed: {e}")
        return json.dumps({'error': 'serialization_failed', 'type': str(type(obj))})


def get_checksum(content: str) -> str:
    """Generate SHA256 checksum for content"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def get_timestamp() -> str:
    """Get current UTC timestamp in ISO format"""
    return datetime.now(timezone.utc).isoformat()


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retry logic with exponential backoff"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            
            # Re-raise the last exception if all attempts failed
            raise last_exception
        return wrapper
    return decorator


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. ')
    # Ensure not empty
    return sanitized if sanitized else 'unnamed'


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length with optional suffix"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix