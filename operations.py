"""
Database operations for architect decisions
Contains functions for storing and retrieving architect decisions
"""

from datetime import datetime
from config import supabase

def store_architect_decision(content: str) -> dict:
    """
    Store an architect decision in the database
    
    Args:
        content (str): The architect decision content to store
    
    Returns:
        dict: The inserted record with id and timestamp, or error information
        
    Raises:
        ValueError: If content is empty or invalid
        Exception: If database operation fails
    """
    
    if not content or not content.strip():
        raise ValueError("Content cannot be empty")
    
    try:
        # Prepare the data to insert
        decision_data = {
            "content": content.strip(),
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        # Insert into architect_decisions table
        result = supabase.table("architect_decisions").insert(decision_data).execute()
        
        if result.data:
            return {
                "success": True,
                "data": result.data[0],
                "message": "Architect decision stored successfully"
            }
        else:
            return {
                "success": False,
                "error": "No data returned from insert operation",
                "message": "Failed to store architect decision"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Database operation failed: {str(e)}"
        }

def get_architect_decisions(limit: int = 10) -> dict:
    """
    Retrieve recent architect decisions from the database
    
    Args:
        limit (int): Maximum number of decisions to retrieve
        
    Returns:
        dict: List of decisions or error information
    """
    
    try:
        result = supabase.table("architect_decisions")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return {
            "success": True,
            "data": result.data,
            "count": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to retrieve architect decisions: {str(e)}"
        }