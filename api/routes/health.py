"""
Angles OS™ Health Check Routes
System health monitoring and diagnostics
"""
from fastapi import APIRouter, HTTPException
from api.deps import get_db_connection, get_redis_connection
from api.services.supabase_connector import SupabaseConnector
from api.services.notion_connector import NotionConnector
from api.utils.logging import logger
from api.config import settings
import psutil
import platform

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health_check():
    """Comprehensive system health check"""
    health_data = {
        "status": "ok",
        "version": "1.0.0",
        "system": {
            "platform": platform.system(),
            "python": platform.python_version(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        },
        "services": {},
        "external": {}
    }
    
    # Database health
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        health_data["services"]["database"] = {"status": "healthy", "type": "postgresql"}
    except Exception as e:
        health_data["services"]["database"] = {"status": "error", "error": str(e)}
        health_data["status"] = "degraded"
    
    # Redis health
    try:
        redis_conn = get_redis_connection()
        if redis_conn:
            redis_conn.ping()
            health_data["services"]["redis"] = {"status": "healthy", "type": "redis"}
        else:
            health_data["services"]["redis"] = {"status": "unavailable"}
    except Exception as e:
        health_data["services"]["redis"] = {"status": "error", "error": str(e)}
    
    # External services
    # Supabase
    try:
        supabase = SupabaseConnector()
        health_data["external"]["supabase"] = supabase.health_check()
    except Exception as e:
        health_data["external"]["supabase"] = {"status": "error", "error": str(e)}
    
    # Notion
    try:
        notion = NotionConnector()
        health_data["external"]["notion"] = notion.test_connection()
    except Exception as e:
        health_data["external"]["notion"] = {"status": "error", "error": str(e)}
    
    # OpenAI
    health_data["external"]["openai"] = {
        "status": "configured" if settings.has_openai() else "not_configured"
    }
    
    # Overall status determination
    service_issues = sum(1 for service in health_data["services"].values() 
                        if service.get("status") != "healthy")
    
    if service_issues > 0:
        health_data["status"] = "degraded"
    
    logger.info(f"Health check completed: {health_data['status']}")
    return health_data

@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong", "timestamp": "now"}

@router.get("/ready")
async def readiness_check():
    """Kubernetes-style readiness check"""
    try:
        # Check critical services
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")

@router.get("/live")
async def liveness_check():
    """Kubernetes-style liveness check"""
    return {"status": "alive"}