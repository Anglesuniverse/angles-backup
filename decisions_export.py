# decisions_export.py

from operations import get_architect_decisions

def export_all_decisions():
    """Export and display all architect decisions"""
    result = get_architect_decisions(limit=100)  # Get more decisions
    
    if result["success"]:
        decisions = result["data"]
        count = result["count"]
        
        print(f"Found {count} architect decisions:")
        print("=" * 50)
        
        for idx, decision in enumerate(decisions, 1):
            content = decision.get('content', 'No content')
            status = decision.get('status', 'unknown')
            created_at = decision.get('created_at', 'unknown')
            
            print(f"{idx}. {content}")
            print(f"   Status: {status} | Created: {created_at}")
            print()
    else:
        print(f"Failed to export decisions: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    export_all_decisions()