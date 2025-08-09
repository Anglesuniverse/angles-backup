"""
Angles OS™ FastAPI Application
Main application with scheduled agents and comprehensive routing
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import schedule
import threading
import time

# Import routes
from api.routes.health import router as health_router
from api.routes.ui import router as ui_router
from api.routes.vault import router as vault_router
from api.routes.decisions import router as decisions_router

# Import agents
from api.agents.memory_sync_agent import MemorySyncAgent
from api.agents.strategy_agent import StrategyAgent
from api.agents.verifier_agent import VerifierAgent

# Import utilities
from api.utils.logging import logger
from api.config import settings

# Global agent instances
memory_sync_agent = MemorySyncAgent()
strategy_agent = StrategyAgent()
verifier_agent = VerifierAgent()

def run_scheduled_jobs():
    """Background thread for running scheduled jobs"""
    logger.info("Starting scheduled jobs thread")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Scheduled jobs error: {e}")
            time.sleep(60)  # Wait longer on error

def schedule_agents():
    """Schedule agent execution"""
    try:
        # Schedule MemorySyncAgent every 6 hours
        schedule.every(6).hours.do(lambda: memory_sync_agent.run())
        
        # Schedule StrategyAgent hourly
        schedule.every().hour.do(lambda: strategy_agent.run())
        
        # Schedule VerifierAgent daily
        schedule.every().day.at("02:00").do(lambda: verifier_agent.run())
        
        logger.info("Agent scheduling configured:")
        logger.info("  - Memory Sync Agent: Every 6 hours")
        logger.info("  - Strategy Agent: Every hour")
        logger.info("  - Verifier Agent: Daily at 02:00 UTC")
        
        # Start scheduler thread
        scheduler_thread = threading.Thread(target=run_scheduled_jobs, daemon=True)
        scheduler_thread.start()
        
    except Exception as e:
        logger.error(f"Agent scheduling failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting Angles OS™ FastAPI Application")
    logger.info(f"Environment: {settings.env}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Schedule agents
    schedule_agents()
    
    # Run initial agent checks
    try:
        logger.info("Running initial agent health checks...")
        verifier_agent.run()
        logger.info("Initial health check completed")
    except Exception as e:
        logger.warning(f"Initial health check failed: {e}")
    
    logger.info("✅ Angles OS™ startup complete")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Angles OS™")

# Create FastAPI app
app = FastAPI(
    title="Angles OS™",
    description="Production-ready FastAPI backend with TokenVault, Decisions, and Agent systems",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(ui_router)
app.include_router(vault_router)
app.include_router(decisions_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🚀 Angles OS™ Ready",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "TokenVault persistent memory",
            "AI-powered decision management",
            "Automated agents (memory sync, strategy, verifier)",
            "External service connectors (Supabase, Notion, OpenAI)",
            "Background job processing",
            "Comprehensive health monitoring"
        ],
        "endpoints": {
            "health": "/health",
            "vault": "/vault",
            "decisions": "/decisions",
            "ui": "/ui",
            "docs": "/docs"
        }
    }

@app.get("/agents/status")
async def get_agent_status():
    """Get status of all agents"""
    try:
        return {
            "memory_sync_agent": memory_sync_agent.get_status(),
            "strategy_agent": strategy_agent.get_status(),
            "verifier_agent": verifier_agent.get_status(),
            "scheduler_active": len(schedule.jobs) > 0,
            "scheduled_jobs": len(schedule.jobs)
        }
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        return {"error": str(e)}

@app.post("/agents/{agent_name}/run")
async def run_agent(agent_name: str):
    """Manually trigger agent execution"""
    try:
        if agent_name == "memory_sync":
            memory_sync_agent.run()
            return {"message": f"Memory sync agent executed", "agent": agent_name}
        elif agent_name == "strategy":
            strategy_agent.run()
            return {"message": f"Strategy agent executed", "agent": agent_name}
        elif agent_name == "verifier":
            verifier_agent.run()
            return {"message": f"Verifier agent executed", "agent": agent_name}
        else:
            return {"error": f"Unknown agent: {agent_name}"}, 404
            
    except Exception as e:
        logger.error(f"Failed to run agent {agent_name}: {e}")
        return {"error": str(e)}, 500

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}")
    return Response(
        content=f"Internal server error: {str(exc)}",
        status_code=500,
        media_type="text/plain"
    )

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )