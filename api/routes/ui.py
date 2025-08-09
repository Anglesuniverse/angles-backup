"""
Angles OS™ UI Data Routes
Provides summary data for dashboard and UI components
"""
from fastapi import APIRouter
from api.services.token_vault import TokenVault
from api.services.decisions import DecisionService
from api.deps import get_db_cursor
from api.utils.logging import logger
import json

router = APIRouter(prefix="/ui", tags=["ui"])

@router.get("/summary")
async def get_ui_summary():
    """Get summary data for UI dashboard"""
    summary = {
        "vault": {},
        "decisions": {},
        "agents": {},
        "recent": {}
    }
    
    try:
        # Vault statistics
        vault = TokenVault()
        summary["vault"] = vault.get_stats()
        
        # Decision statistics
        decision_service = DecisionService()
        summary["decisions"] = decision_service.get_stats()
        
        # Agent activity summary
        with get_db_cursor() as cursor:
            # Agent activity counts
            cursor.execute("""
                SELECT agent, level, COUNT(*) 
                FROM agent_logs 
                WHERE created_at > NOW() - INTERVAL '24 hours'
                GROUP BY agent, level 
                ORDER BY agent, level
            """)
            
            agent_activity = {}
            for agent, level, count in cursor.fetchall():
                if agent not in agent_activity:
                    agent_activity[agent] = {}
                agent_activity[agent][level] = count
            
            summary["agents"] = {
                "activity_24h": agent_activity,
                "total_agents": len(agent_activity)
            }
            
            # Recent activity across all systems
            cursor.execute("""
                SELECT 'vault' as type, source as title, created_at 
                FROM vault_chunks 
                ORDER BY created_at DESC LIMIT 3
            """)
            recent_vault = [
                {"type": row[0], "title": row[1], "timestamp": row[2].isoformat()}
                for row in cursor.fetchall()
            ]
            
            cursor.execute("""
                SELECT 'decision' as type, topic as title, created_at 
                FROM decisions 
                ORDER BY created_at DESC LIMIT 3
            """)
            recent_decisions = [
                {"type": row[0], "title": row[1], "timestamp": row[2].isoformat()}
                for row in cursor.fetchall()
            ]
            
            cursor.execute("""
                SELECT 'agent' as type, 
                       CONCAT(agent, ': ', message) as title, 
                       created_at 
                FROM agent_logs 
                WHERE level IN ('INFO', 'WARNING', 'ERROR')
                ORDER BY created_at DESC LIMIT 3
            """)
            recent_agents = [
                {"type": row[0], "title": row[1], "timestamp": row[2].isoformat()}
                for row in cursor.fetchall()
            ]
            
            # Combine and sort recent activity
            all_recent = recent_vault + recent_decisions + recent_agents
            all_recent.sort(key=lambda x: x['timestamp'], reverse=True)
            
            summary["recent"] = {
                "activities": all_recent[:10],
                "vault_count": len(recent_vault),
                "decision_count": len(recent_decisions),
                "agent_count": len(recent_agents)
            }
        
        logger.info("Generated UI summary")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to generate UI summary: {e}")
        return {
            "vault": {"total_chunks": 0, "top_sources": []},
            "decisions": {"total_decisions": 0, "by_status": {}},
            "agents": {"activity_24h": {}, "total_agents": 0},
            "recent": {"activities": [], "vault_count": 0, "decision_count": 0, "agent_count": 0},
            "error": "Failed to load summary data"
        }

@router.get("/metrics")
async def get_metrics():
    """Get detailed metrics for monitoring"""
    metrics = {}
    
    try:
        with get_db_cursor() as cursor:
            # Table sizes
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples
                FROM pg_stat_user_tables 
                WHERE schemaname = 'public'
            """)
            
            table_stats = []
            for row in cursor.fetchall():
                table_stats.append({
                    "schema": row[0],
                    "table": row[1],
                    "inserts": row[2],
                    "updates": row[3],
                    "deletes": row[4],
                    "live_tuples": row[5]
                })
            
            metrics["tables"] = table_stats
            
            # Activity trends (last 7 days)
            cursor.execute("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as count,
                    'vault_chunks' as table_name
                FROM vault_chunks 
                WHERE created_at > NOW() - INTERVAL '7 days'
                GROUP BY DATE(created_at)
                
                UNION ALL
                
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as count,
                    'decisions' as table_name
                FROM decisions 
                WHERE created_at > NOW() - INTERVAL '7 days'
                GROUP BY DATE(created_at)
                
                ORDER BY date DESC
            """)
            
            trends = []
            for row in cursor.fetchall():
                trends.append({
                    "date": row[0].isoformat(),
                    "count": row[1],
                    "table": row[2]
                })
            
            metrics["trends"] = trends
            
        logger.info("Generated metrics data")
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return {"error": "Failed to load metrics", "tables": [], "trends": []}

@router.get("/status")
async def get_status():
    """Get current system status"""
    try:
        with get_db_cursor() as cursor:
            # Count recent activities
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM vault_chunks WHERE created_at > NOW() - INTERVAL '1 hour') as vault_1h,
                    (SELECT COUNT(*) FROM decisions WHERE created_at > NOW() - INTERVAL '1 hour') as decisions_1h,
                    (SELECT COUNT(*) FROM agent_logs WHERE created_at > NOW() - INTERVAL '1 hour' AND level = 'ERROR') as errors_1h,
                    (SELECT COUNT(*) FROM agent_logs WHERE created_at > NOW() - INTERVAL '1 hour' AND level = 'WARNING') as warnings_1h
            """)
            
            row = cursor.fetchone()
            
            return {
                "timestamp": "now",
                "activity": {
                    "vault_chunks_1h": row[0],
                    "decisions_1h": row[1],
                    "errors_1h": row[2],
                    "warnings_1h": row[3]
                },
                "health": "operational" if row[2] == 0 else "warning" if row[2] < 5 else "critical"
            }
            
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        return {
            "timestamp": "now",
            "activity": {"vault_chunks_1h": 0, "decisions_1h": 0, "errors_1h": 0, "warnings_1h": 0},
            "health": "unknown",
            "error": str(e)
        }