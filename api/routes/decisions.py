"""
Angles OS™ Decision Routes
Decision management and recommendation endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from api.services.decisions import DecisionService
from api.services.openai_client import OpenAIClient
from api.utils.logging import logger

router = APIRouter(prefix="/decisions", tags=["decisions"])

# Request models
class OptionModel(BaseModel):
    option: str
    pros: List[str] = []
    cons: List[str] = []

class CreateDecisionRequest(BaseModel):
    topic: str
    options: List[OptionModel]

class RecommendRequest(BaseModel):
    rationale: Optional[str] = None

class DeclineRequest(BaseModel):
    rationale: Optional[str] = None

# Initialize services
decision_service = DecisionService()
openai_client = OpenAIClient()

@router.post("")
async def create_decision(request: CreateDecisionRequest):
    """Create a new decision"""
    try:
        options_data = [opt.model_dump() for opt in request.options]
        decision_id = decision_service.create_decision(request.topic, options_data)
        
        logger.info(f"Created decision: {request.topic}")
        return {
            "status": "success",
            "decision_id": decision_id,
            "topic": request.topic,
            "options_count": len(request.options)
        }
        
    except Exception as e:
        logger.error(f"Decision creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
async def list_decisions(status: Optional[str] = None, limit: int = Query(50, le=200)):
    """List decisions with optional status filter"""
    try:
        decisions = decision_service.list_decisions(status, limit)
        
        logger.info(f"Listed {len(decisions)} decisions" + (f" with status '{status}'" if status else ""))
        return {
            "decisions": decisions,
            "total": len(decisions),
            "filter": {"status": status, "limit": limit}
        }
        
    except Exception as e:
        logger.error(f"Decision listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{decision_id}")
async def get_decision(decision_id: str):
    """Get a specific decision by ID"""
    try:
        decision = decision_service.get_decision(decision_id)
        
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        
        logger.info(f"Retrieved decision {decision_id}")
        return decision
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Decision retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{decision_id}/recommend")
async def recommend_decision(decision_id: str, request: RecommendRequest = RecommendRequest()):
    """Generate AI recommendation for a decision"""
    try:
        decision = decision_service.get_decision(decision_id)
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        
        # Try OpenAI first, fallback to service method
        if openai_client.is_available():
            try:
                ai_recommendation = openai_client.decide(decision['topic'], decision['options'])
                recommendation = decision_service.recommend(
                    decision_id, 
                    request.rationale or ai_recommendation['rationale']
                )
                recommendation['method'] = ai_recommendation.get('method', 'gpt-5')
            except Exception as e:
                logger.warning(f"OpenAI recommendation failed, using fallback: {e}")
                recommendation = decision_service.recommend(decision_id, request.rationale)
                recommendation['method'] = 'heuristic'
        else:
            recommendation = decision_service.recommend(decision_id, request.rationale)
            recommendation['method'] = 'heuristic'
        
        logger.info(f"Generated recommendation for decision {decision_id}")
        return recommendation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{decision_id}/approve")
async def approve_decision(decision_id: str):
    """Approve a decision"""
    try:
        result = decision_service.approve(decision_id)
        
        logger.info(f"Approved decision {decision_id}")
        return {
            "status": "success",
            "message": "Decision approved",
            **result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Decision approval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{decision_id}/decline")
async def decline_decision(decision_id: str, request: DeclineRequest = DeclineRequest()):
    """Decline a decision"""
    try:
        result = decision_service.decline(decision_id, request.rationale)
        
        logger.info(f"Declined decision {decision_id}")
        return {
            "status": "success",
            "message": "Decision declined",
            **result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Decision decline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_decision_stats():
    """Get decision statistics"""
    try:
        stats = decision_service.get_stats()
        logger.info("Retrieved decision statistics")
        return stats
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))