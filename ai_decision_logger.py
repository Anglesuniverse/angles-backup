"""
AI Decision Logger for Supabase
Logs AI decisions to the ai_decision_log table with environment variable configuration
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any, Union
from supabase import create_client, Client

class AIDecisionLogger:
    """Logger for AI decisions with Supabase backend"""
    
    def __init__(self):
        """Initialize Supabase client using environment variables"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Missing required environment variables: SUPABASE_URL and SUPABASE_KEY"
            )
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    def log_decision(self, 
                    decision_text: str,
                    decision_type: str = "general",
                    context: Optional[str] = None,
                    confidence: Optional[float] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Log an AI decision to the ai_decision_log table
        
        Args:
            decision_text: The AI decision or reasoning
            decision_type: Type of decision (e.g., 'technical', 'strategy', 'recommendation')
            context: Optional context or prompt that led to the decision
            confidence: Optional confidence score (0.0 to 1.0)
            metadata: Optional additional data as JSON
        
        Returns:
            dict: Result with success/error information and logged data
        """
        
        if not decision_text or not decision_text.strip():
            return {
                "success": False,
                "error": "Decision text cannot be empty",
                "message": "Invalid decision text provided"
            }
        
        try:
            # Prepare log entry
            log_entry = {
                "decision_text": decision_text.strip(),
                "decision_type": decision_type.lower(),
                "timestamp": datetime.utcnow().isoformat(),
                "context": context.strip() if context else None,
                "confidence": confidence if confidence is not None else None,
                "metadata": metadata if metadata else None
            }
            
            # Insert into Supabase
            result = self.supabase.table("ai_decision_log").insert(log_entry).execute()
            
            if result.data:
                return {
                    "success": True,
                    "data": result.data[0],
                    "message": "AI decision logged successfully",
                    "id": result.data[0].get("id")
                }
            else:
                return {
                    "success": False,
                    "error": "No data returned from insert operation",
                    "message": "Failed to log AI decision"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Database operation failed: {str(e)}"
            }
    
    def get_recent_decisions(self, 
                           limit: int = 20,
                           decision_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve recent AI decisions from the log
        
        Args:
            limit: Maximum number of decisions to retrieve
            decision_type: Optional filter by decision type
        
        Returns:
            dict: List of recent decisions or error information
        """
        
        try:
            query = self.supabase.table("ai_decision_log").select("*")
            
            # Filter by type if specified
            if decision_type:
                query = query.eq("decision_type", decision_type.lower())
            
            # Order by timestamp and limit
            result = query.order("timestamp", desc=True).limit(limit).execute()
            
            return {
                "success": True,
                "data": result.data,
                "count": len(result.data) if result.data else 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to retrieve decisions: {str(e)}"
            }
    
    def get_decision_stats(self) -> Dict[str, Any]:
        """
        Get statistics about logged AI decisions
        
        Returns:
            dict: Statistics about decision types and counts
        """
        
        try:
            # Get all decisions for statistics
            result = self.supabase.table("ai_decision_log").select("decision_type, confidence").execute()
            
            if not result.data:
                return {
                    "success": True,
                    "total_decisions": 0,
                    "by_type": {},
                    "avg_confidence": None
                }
            
            decisions = result.data
            total = len(decisions)
            
            # Count by type
            by_type = {}
            confidences = []
            
            for decision in decisions:
                decision_type = decision.get("decision_type", "unknown")
                confidence = decision.get("confidence")
                
                # Count by type
                by_type[decision_type] = by_type.get(decision_type, 0) + 1
                
                # Collect confidence scores
                if confidence is not None:
                    confidences.append(confidence)
            
            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else None
            
            return {
                "success": True,
                "total_decisions": total,
                "by_type": by_type,
                "avg_confidence": round(avg_confidence, 3) if avg_confidence else None,
                "confidence_samples": len(confidences)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get statistics: {str(e)}"
            }


# Convenience functions for direct usage
def log_ai_decision(decision_text: str, 
                   decision_type: str = "general",
                   context: Optional[str] = None,
                   confidence: Optional[float] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to log an AI decision
    
    Args:
        decision_text: The AI decision or reasoning
        decision_type: Type of decision
        context: Optional context
        confidence: Optional confidence score (0.0 to 1.0)
        metadata: Optional additional data
    
    Returns:
        dict: Result of the logging operation
    """
    logger = AIDecisionLogger()
    return logger.log_decision(decision_text, decision_type, context, confidence, metadata)


def get_recent_ai_decisions(limit: int = 20, 
                          decision_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to get recent AI decisions
    
    Args:
        limit: Maximum number of decisions to retrieve
        decision_type: Optional filter by decision type
    
    Returns:
        dict: List of recent decisions
    """
    logger = AIDecisionLogger()
    return logger.get_recent_decisions(limit, decision_type)


def get_ai_decision_stats() -> Dict[str, Any]:
    """
    Convenience function to get AI decision statistics
    
    Returns:
        dict: Statistics about logged decisions
    """
    logger = AIDecisionLogger()
    return logger.get_decision_stats()