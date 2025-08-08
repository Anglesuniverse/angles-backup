#!/usr/bin/env python3
"""
Sync Supabase decision_vault data to Notion
Reads decisions from Supabase and logs them to Notion database
"""

from decision_vault_operations import get_decisions
from log_to_notion import log_to_notion, test_notion_connection
from typing import Dict, Any

def sync_decision_to_notion(decision: Dict[str, Any]) -> bool:
    """
    Sync a single decision from Supabase to Notion
    
    Args:
        decision: Decision data from Supabase
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Extract data from Supabase decision
        message = decision.get('decision', '')
        decision_type = decision.get('type', 'general')
        comment = decision.get('comment', '')
        date_str = decision.get('date', '')
        
        # Create tags from type and comment
        tags = [decision_type]
        
        # Parse tags from comment if it contains "Tags:"
        if comment and 'Tags:' in comment:
            comment_tags = comment.replace('Tags:', '').strip().split(',')
            tags.extend([tag.strip() for tag in comment_tags if tag.strip()])
        
        # Remove duplicates while preserving order
        unique_tags = []
        for tag in tags:
            if tag and tag not in unique_tags:
                unique_tags.append(tag)
        
        # Log to Notion
        success = log_to_notion(message, unique_tags)
        
        if success:
            print(f"✅ Synced: {message[:50]}...")
            return True
        else:
            print(f"❌ Failed to sync: {message[:50]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error syncing decision: {e}")
        return False

def sync_all_decisions(limit: int = 50, only_active: bool = True) -> Dict[str, Any]:
    """
    Sync all decisions from Supabase to Notion
    
    Args:
        limit: Maximum number of decisions to sync
        only_active: Only sync active decisions
        
    Returns:
        dict: Sync results and statistics
    """
    
    print("Supabase to Notion Sync")
    print("=" * 40)
    
    # Test Notion connection first
    print("Testing Notion connection...")
    if not test_notion_connection():
        return {
            "success": False,
            "error": "Failed to connect to Notion",
            "synced": 0,
            "failed": 0
        }
    
    print("\nFetching decisions from Supabase...")
    
    # Get decisions from Supabase
    result = get_decisions(limit=limit, endast_aktiva=only_active)
    
    if not result["success"]:
        return {
            "success": False,
            "error": f"Failed to fetch from Supabase: {result.get('error', 'Unknown error')}",
            "synced": 0,
            "failed": 0
        }
    
    decisions = result.get("data", [])
    total_decisions = len(decisions)
    
    if total_decisions == 0:
        print("No decisions found in Supabase")
        return {
            "success": True,
            "message": "No decisions to sync",
            "synced": 0,
            "failed": 0
        }
    
    print(f"Found {total_decisions} decisions to sync")
    print("-" * 40)
    
    # Sync each decision
    synced_count = 0
    failed_count = 0
    
    for i, decision in enumerate(decisions, 1):
        print(f"Syncing {i}/{total_decisions}: ", end="")
        
        if sync_decision_to_notion(decision):
            synced_count += 1
        else:
            failed_count += 1
    
    # Summary
    print("-" * 40)
    print(f"Sync completed!")
    print(f"✅ Successfully synced: {synced_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📊 Total processed: {total_decisions}")
    
    return {
        "success": True,
        "synced": synced_count,
        "failed": failed_count,
        "total": total_decisions,
        "success_rate": f"{(synced_count/total_decisions)*100:.1f}%" if total_decisions > 0 else "0%"
    }

def sync_recent_decisions(days_back: int = 7) -> Dict[str, Any]:
    """
    Sync only recent decisions from the last N days
    
    Args:
        days_back: Number of days to look back
        
    Returns:
        dict: Sync results
    """
    
    print(f"Syncing decisions from last {days_back} days...")
    
    # For now, just sync all active decisions
    # Could be enhanced to filter by date in the future
    return sync_all_decisions(limit=20, only_active=True)

def main():
    """Main sync function"""
    
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--recent":
            result = sync_recent_decisions(7)
        elif sys.argv[1] == "--all":
            result = sync_all_decisions(limit=100, only_active=False)
        elif sys.argv[1] == "--test":
            # Just test the connection
            if test_notion_connection():
                print("✅ Connection test successful")
                return
            else:
                print("❌ Connection test failed")
                return
        else:
            print("Usage: python sync_supabase_to_notion.py [--recent|--all|--test]")
            return
    else:
        # Default: sync active decisions
        result = sync_all_decisions()
    
    # Final status
    if result.get("success"):
        if result.get("synced", 0) > 0:
            print(f"\n🎉 Sync successful! {result['synced']} decisions synced.")
        else:
            print(f"\n💡 {result.get('message', 'Sync completed but no new data.')}")
    else:
        print(f"\n❌ Sync failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()