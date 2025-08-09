"""
Angles OS™ Vault Routes
TokenVault memory storage and retrieval endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from api.services.token_vault import TokenVault
from api.utils.logging import logger

router = APIRouter(prefix="/vault", tags=["vault"])

# Request models
class IngestRequest(BaseModel):
    source: str
    chunk: str
    summary: Optional[str] = None
    links: Optional[List[str]] = None

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

# Initialize vault service
vault = TokenVault()

@router.post("/ingest")
async def ingest_chunk(request: IngestRequest):
    """Ingest a knowledge chunk into the vault"""
    try:
        chunk_id = vault.ingest(
            source=request.source,
            chunk=request.chunk,
            summary=request.summary,
            links=request.links
        )
        
        logger.info(f"Ingested chunk {chunk_id} from {request.source}")
        return {
            "status": "success",
            "chunk_id": chunk_id,
            "message": "Chunk ingested successfully"
        }
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
async def query_vault(request: QueryRequest):
    """Search the vault for relevant chunks"""
    try:
        results = vault.naive_search(request.query, request.top_k)
        
        logger.info(f"Vault query '{request.query}' returned {len(results)} results")
        return {
            "query": request.query,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/source/{source}")
async def get_by_source(source: str, limit: int = Query(10, le=100)):
    """Get chunks by source"""
    try:
        results = vault.get_by_source(source, limit)
        
        logger.info(f"Retrieved {len(results)} chunks from source '{source}'")
        return {
            "source": source,
            "chunks": results,
            "total": len(results)
        }
        
    except Exception as e:
        logger.error(f"Source query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_vault_stats():
    """Get vault statistics"""
    try:
        stats = vault.get_stats()
        logger.info("Retrieved vault statistics")
        return stats
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))