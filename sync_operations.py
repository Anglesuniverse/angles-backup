"""
Unified operations for architect decisions
Manages both Supabase and Notion storage with sync capabilities
"""

from operations import store_architect_decision, get_architect_decisions
from notion_integration import notion_client

def store_decision_everywhere(content: str, sync_to_notion: bool = True) -> dict:
    """
    Store architect decision in both Supabase and Notion
    
    Args:
        content: The decision content
        sync_to_notion: Whether to also store in Notion
    
    Returns:
        dict: Combined results from both operations
    """
    results = {
        "supabase": {"success": False},
        "notion": {"success": False, "skipped": not sync_to_notion}
    }
    
    # Store in Supabase first
    try:
        supabase_result = store_architect_decision(content)
        results["supabase"] = supabase_result
    except Exception as e:
        results["supabase"] = {"success": False, "error": str(e)}
    
    # Store in Notion if requested and Supabase succeeded
    if sync_to_notion and results["supabase"]["success"]:
        try:
            notion_result = notion_client.add_decision_to_notion(content)
            results["notion"] = notion_result
        except Exception as e:
            results["notion"] = {"success": False, "error": str(e)}
    
    # Overall success
    overall_success = results["supabase"]["success"]
    if sync_to_notion:
        overall_success = overall_success and results["notion"]["success"]
    
    return {
        "success": overall_success,
        "results": results,
        "message": f"Stored in Supabase: {results['supabase']['success']}, Notion: {results['notion']['success']}"
    }

def get_all_decisions() -> dict:
    """Get decisions from both Supabase and Notion"""
    results = {
        "supabase": {"success": False, "data": []},
        "notion": {"success": False, "data": []}
    }
    
    # Get from Supabase
    try:
        supabase_result = get_architect_decisions(limit=50)
        results["supabase"] = supabase_result
    except Exception as e:
        results["supabase"] = {"success": False, "error": str(e), "data": []}
    
    # Get from Notion
    try:
        notion_result = notion_client.get_decisions_from_notion(limit=50)
        results["notion"] = notion_result
    except Exception as e:
        results["notion"] = {"success": False, "error": str(e), "data": []}
    
    return {
        "success": results["supabase"]["success"] or results["notion"]["success"],
        "supabase_count": len(results["supabase"].get("data", [])),
        "notion_count": len(results["notion"].get("data", [])),
        "results": results
    }

def sync_status() -> dict:
    """Check sync status between Supabase and Notion"""
    all_decisions = get_all_decisions()
    
    return {
        "supabase": {
            "available": all_decisions["results"]["supabase"]["success"],
            "count": all_decisions["supabase_count"]
        },
        "notion": {
            "available": all_decisions["results"]["notion"]["success"],
            "count": all_decisions["notion_count"]
        },
        "total_sources": sum([
            all_decisions["results"]["supabase"]["success"],
            all_decisions["results"]["notion"]["success"]
        ])
    }