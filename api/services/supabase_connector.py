"""
Angles OS™ Supabase Integration
Client and server-level access to Supabase with proper key separation
"""
from typing import Optional, Dict, Any, List
from api.config import settings
from api.utils.logging import logger

try:
    from supabase import create_client, Client
    _supabase_available = True
except ImportError:
    _supabase_available = False
    logger.warning("Supabase library not available")

class SupabaseConnector:
    """Supabase client with proper key management"""
    
    def __init__(self):
        self.client_conn: Optional[Client] = None
        self.server_conn: Optional[Client] = None
        
        if _supabase_available and settings.has_supabase():
            self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize client and server connections"""
        try:
            # Client connection (anon key for user operations)
            self.client_conn = create_client(
                settings.supabase_url,
                settings.supabase_anon_key
            )
            logger.info("Supabase client connection initialized")
            
            # Server connection (service key for admin operations)
            if settings.supabase_service_key:
                self.server_conn = create_client(
                    settings.supabase_url,
                    settings.supabase_service_key
                )
                logger.info("Supabase server connection initialized")
            
        except Exception as e:
            logger.error(f"Supabase initialization failed: {e}")
    
    def is_available(self, server_only: bool = False) -> bool:
        """Check if Supabase is available"""
        if server_only:
            return self.server_conn is not None
        return self.client_conn is not None
    
    def get_connection(self, server_only: bool = False) -> Optional[Client]:
        """Get appropriate Supabase connection"""
        if server_only:
            if not self.server_conn:
                logger.warning("Server-only operation requested but no service key available")
                return None
            return self.server_conn
        return self.client_conn
    
    def sync_vault_chunk(self, chunk_data: Dict[str, Any], server_only: bool = False) -> bool:
        """Sync vault chunk to Supabase"""
        conn = self.get_connection(server_only)
        if not conn:
            logger.warning("Supabase not available for vault sync")
            return False
        
        try:
            result = conn.table('vault_chunks').insert(chunk_data).execute()
            logger.info(f"Synced vault chunk: {chunk_data.get('source', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync vault chunk: {e}")
            return False
    
    def sync_decision(self, decision_data: Dict[str, Any], server_only: bool = False) -> bool:
        """Sync decision to Supabase"""
        conn = self.get_connection(server_only)
        if not conn:
            logger.warning("Supabase not available for decision sync")
            return False
        
        try:
            result = conn.table('decisions').insert(decision_data).execute()
            logger.info(f"Synced decision: {decision_data.get('topic', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync decision: {e}")
            return False
    
    def log_agent_activity(self, agent: str, level: str, message: str, 
                          meta: Optional[Dict[str, Any]] = None, 
                          server_only: bool = True) -> bool:
        """Log agent activity to Supabase"""
        conn = self.get_connection(server_only)
        if not conn:
            return False
        
        try:
            log_data = {
                'agent': agent,
                'level': level,
                'message': message,
                'meta': meta or {},
                'created_at': 'now()'
            }
            
            result = conn.table('agent_logs').insert(log_data).execute()
            return True
            
        except Exception as e:
            logger.error(f"Failed to log agent activity: {e}")
            return False
    
    def get_recent_activity(self, table: str, limit: int = 10, 
                           server_only: bool = False) -> List[Dict[str, Any]]:
        """Get recent activity from specified table"""
        conn = self.get_connection(server_only)
        if not conn:
            return []
        
        try:
            result = conn.table(table).select("*").order('created_at', desc=True).limit(limit).execute()
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to get recent activity from {table}: {e}")
            return []
    
    def backup_data(self, tables: List[str], server_only: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """Backup data from multiple tables"""
        conn = self.get_connection(server_only)
        if not conn:
            return {}
        
        backup_data = {}
        
        for table in tables:
            try:
                result = conn.table(table).select("*").execute()
                backup_data[table] = result.data
                logger.info(f"Backed up {len(result.data)} records from {table}")
                
            except Exception as e:
                logger.error(f"Failed to backup {table}: {e}")
                backup_data[table] = []
        
        return backup_data
    
    def health_check(self) -> Dict[str, Any]:
        """Check Supabase connection health"""
        if not self.client_conn:
            return {'status': 'unavailable', 'error': 'Not configured'}
        
        try:
            # Try a simple query
            result = self.client_conn.table('vault_chunks').select('id').limit(1).execute()
            return {
                'status': 'healthy',
                'connection': 'client' if self.client_conn else 'none',
                'server_connection': 'available' if self.server_conn else 'none'
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}