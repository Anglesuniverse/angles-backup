"""
Angles OS™ TokenVault
Persistent memory storage system for knowledge chunks
"""
import json
import uuid
from typing import List, Dict, Any, Optional
from api.deps import get_db_cursor
from api.utils.logging import logger
from api.utils.time import utc_now

class TokenVault:
    """Persistent memory storage with semantic search capabilities"""
    
    def __init__(self):
        self.table = 'vault_chunks'
    
    def ingest(self, source: str, chunk: str, summary: Optional[str] = None, 
               links: Optional[List[str]] = None) -> str:
        """Store a knowledge chunk in the vault"""
        chunk_id = str(uuid.uuid4())
        links = links or []
        
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO vault_chunks (id, source, chunk, summary, links, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (chunk_id, source, chunk, summary, links, utc_now()))
                
            logger.info(f"Ingested chunk from {source}: {chunk[:50]}...")
            return chunk_id
            
        except Exception as e:
            logger.error(f"Failed to ingest chunk: {e}")
            raise
    
    def naive_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Simple text-based search (placeholder for semantic search)"""
        try:
            with get_db_cursor() as cursor:
                # Simple ILIKE search on chunk and summary
                cursor.execute("""
                    SELECT id, source, chunk, summary, links, created_at
                    FROM vault_chunks 
                    WHERE chunk ILIKE %s OR summary ILIKE %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (f'%{query}%', f'%{query}%', top_k))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'id': str(row[0]),
                        'source': row[1],
                        'chunk': row[2],
                        'summary': row[3],
                        'links': row[4] if isinstance(row[4], list) else [],
                        'created_at': row[5].isoformat()
                    })
                
                logger.info(f"Search for '{query}' returned {len(results)} results")
                return results
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_by_source(self, source: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get chunks by source"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT id, source, chunk, summary, links, created_at
                    FROM vault_chunks 
                    WHERE source = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (source, limit))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'id': str(row[0]),
                        'source': row[1],
                        'chunk': row[2],
                        'summary': row[3],
                        'links': row[4] if isinstance(row[4], list) else [],
                        'created_at': row[5].isoformat()
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to get chunks by source: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vault statistics"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM vault_chunks")
                total_chunks = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT source, COUNT(*) 
                    FROM vault_chunks 
                    GROUP BY source 
                    ORDER BY COUNT(*) DESC 
                    LIMIT 10
                """)
                top_sources = [{'source': row[0], 'count': row[1]} for row in cursor.fetchall()]
                
                return {
                    'total_chunks': total_chunks,
                    'top_sources': top_sources
                }
                
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'total_chunks': 0, 'top_sources': []}