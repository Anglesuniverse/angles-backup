"""
Operations for decision_vault table
Handles decision documentation in Supabase
"""

import os
from datetime import date, datetime
from config import supabase
from typing import Optional, List, Dict, Any

def store_decision(decision: str, decision_type: str, decision_date: Optional[date] = None, 
                  active: bool = True, comment: Optional[str] = None) -> Dict[str, Any]:
    """
    Store a decision in the decision_vault table
    
    Args:
        decision: The decision content
        decision_type: Type of decision (strategy, technical, ethical, etc.)
        decision_date: Date of the decision (default: today)
        active: Whether the decision is active (default: True)
        comment: Optional comment
    
    Returns:
        dict: Result with success/error information
    """
    
    if not decision or not decision.strip():
        raise ValueError("Decision cannot be empty")
    
    if not decision_type or not decision_type.strip():
        raise ValueError("Decision type cannot be empty")
    
    # Validate type
    valid_types = ['strategy', 'technical', 'ethical', 'architecture', 'process', 'security', 'other']
    if decision_type.lower() not in valid_types:
        raise ValueError(f"Type must be one of: {', '.join(valid_types)}")
    
    try:
        # Prepare data
        decision_data = {
            "decision": decision.strip(),
            "type": decision_type.lower(),
            "date": (decision_date or date.today()).isoformat(),
            "active": active
        }
        
        if comment:
            decision_data["comment"] = comment.strip()
        
        # Store in Supabase
        result = supabase.table("decision_vault").insert(decision_data).execute()
        
        if result.data:
            return {
                "success": True,
                "data": result.data[0],
                "message": "Decision stored successfully"
            }
        else:
            return {
                "success": False,
                "error": "No data returned from insert operation",
                "message": "Failed to store decision"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Database operation failed: {str(e)}"
        }

def get_decisions(limit: int = 20, decision_type: Optional[str] = None, 
                 active_only: bool = True) -> Dict[str, Any]:
    """
    Retrieve decisions from decision_vault table
    
    Args:
        limit: Max number of decisions to retrieve
        decision_type: Filter by type (optional)
        active_only: Show only active decisions
    
    Returns:
        dict: List of decisions or error information
    """
    
    try:
        query = supabase.table("decision_vault").select("*")
        
        # Filter active decisions
        if active_only:
            query = query.eq("active", True)
        
        # Filter by type
        if decision_type:
            query = query.eq("type", decision_type.lower())
        
        # Order and limit
        result = query.order("date", desc=True).limit(limit).execute()
        
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

def update_decision_status(decision_id: str, active: bool) -> Dict[str, Any]:
    """
    Update decision status (active/inactive)
    
    Args:
        decision_id: UUID of the decision
        active: New status
    
    Returns:
        dict: Result of the update
    """
    
    try:
        result = supabase.table("decision_vault").update(
            {"active": active}
        ).eq("id", decision_id).execute()
        
        if result.data:
            return {
                "success": True,
                "data": result.data[0],
                "message": f"Decision status updated to {'active' if active else 'inactive'}"
            }
        else:
            return {
                "success": False,
                "message": "No decision found with that ID"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to update status: {str(e)}"
        }

def get_decision_statistics() -> Dict[str, Any]:
    """
    Get statistics about decisions in the database
    
    Returns:
        dict: Statistics about decisions by type and status
    """
    
    try:
        # Get all decisions for statistics
        result = supabase.table("decision_vault").select("type, active").execute()
        
        if not result.data:
            return {
                "success": True,
                "total": 0,
                "active": 0,
                "inactive": 0,
                "by_type": {}
            }
        
        decisions = result.data
        total = len(decisions)
        active = len([d for d in decisions if d["active"]])
        inactive = total - active
        
        # Statistics by type
        by_type = {}
        for decision in decisions:
            decision_type = decision["type"]
            if decision_type not in by_type:
                by_type[decision_type] = {"total": 0, "active": 0}
            by_type[decision_type]["total"] += 1
            if decision["active"]:
                by_type[decision_type]["active"] += 1
        
        return {
            "success": True,
            "total": total,
            "active": active,
            "inactive": inactive,
            "by_type": by_type
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to get statistics: {str(e)}"
        }