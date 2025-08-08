"""
Supabase client wrapper for Angles AI Universe™
Handles database operations with upsert logic and error handling
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import hashlib
import requests

from .config import SUPABASE_URL, SUPABASE_KEY
from .utils import safe_json_dumps, retry_with_backoff


logger = logging.getLogger(__name__)


class SupabaseClient:
    """Thin wrapper for Supabase operations"""
    
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY")
        
        self.base_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            response = requests.get(
                f"{self.base_url}/decision_vault?select=id&limit=1",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    @retry_with_backoff(max_retries=3)
    def insert_decision(self, category: str, content: str, tags: List[str] = None, 
                       source: str = "system") -> Optional[str]:
        """Insert decision into decision_vault table"""
        data = {
            'category': category,
            'status': 'active',
            'content': content,
            'date_added': datetime.now(timezone.utc).isoformat(),
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'tags': tags or [],
            'source': source,
            'checksum': hashlib.sha256(content.encode()).hexdigest()
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/decision_vault",
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                return result[0]['id'] if result else None
            else:
                logger.error(f"Failed to insert decision: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error inserting decision: {e}")
            raise
    
    @retry_with_backoff(max_retries=3)
    def upsert_file_snapshot(self, path: str, content: str, checksum: str) -> bool:
        """Upsert file snapshot (insert or update based on path+checksum)"""
        data = {
            'path': path,
            'checksum': checksum,
            'content': content,
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Try upsert (insert with conflict resolution)
            response = requests.post(
                f"{self.base_url}/file_snapshots",
                headers={**self.headers, 'Prefer': 'resolution=merge-duplicates'},
                json=data,
                timeout=30
            )
            
            return response.status_code in [201, 200]
            
        except Exception as e:
            logger.error(f"Error upserting file snapshot: {e}")
            return False
    
    @retry_with_backoff(max_retries=3)  
    def log_system_event(self, level: str, component: str, message: str, meta: Dict = None) -> bool:
        """Log system event to system_logs table"""
        data = {
            'ts': datetime.now(timezone.utc).isoformat(),
            'level': level.upper(),
            'component': component,
            'message': message,
            'meta': meta or {}
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/system_logs",
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            return response.status_code == 201
            
        except Exception as e:
            logger.error(f"Error logging system event: {e}")
            return False
    
    @retry_with_backoff(max_retries=3)
    def store_run_artifact(self, kind: str, ref: str, notes: str, blob: Any = None) -> bool:
        """Store run artifact"""
        data = {
            'ts': datetime.now(timezone.utc).isoformat(),
            'kind': kind,
            'ref': ref,
            'notes': notes,
            'blob': safe_json_dumps(blob) if blob else None
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/run_artifacts",
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            return response.status_code == 201
            
        except Exception as e:
            logger.error(f"Error storing run artifact: {e}")
            return False
    
    def get_recent_logs(self, hours: int = 24, level: str = None) -> List[Dict]:
        """Get recent system logs"""
        try:
            from_time = (datetime.now(timezone.utc) - 
                        datetime.timedelta(hours=hours)).isoformat()
            
            query = f"ts=gte.{from_time}&order=ts.desc&limit=1000"
            if level:
                query += f"&level=eq.{level.upper()}"
                
            response = requests.get(
                f"{self.base_url}/system_logs?{query}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            return []
            
        except Exception as e:
            logger.error(f"Error getting recent logs: {e}")
            return []