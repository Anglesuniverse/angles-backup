#!/usr/bin/env python3
"""
Test script for memory sync agent
"""

import os
from memory_sync_agent import MemorySyncAgent

def test_memory_sync():
    """Test the memory sync agent"""
    
    print("Memory Sync Agent Test")
    print("=" * 40)
    
    try:
        # Create agent
        agent = MemorySyncAgent()
        
        # Test connections
        print("Testing connections...")
        if agent.test_connections():
            print("✓ All connections successful")
        else:
            print("✗ Connection tests failed")
            return False
        
        # Check unsynced decisions
        print("\nChecking for unsynced decisions...")
        decisions = agent.get_unsynced_decisions()
        print(f"Found {len(decisions)} unsynced decisions")
        
        if decisions:
            print("\nUnsynced decisions:")
            for i, decision in enumerate(decisions[:5], 1):  # Show first 5
                decision_text = decision.get('decision', '')[:60]
                decision_type = decision.get('type', 'unknown')
                print(f"  {i}. {decision_text}... ({decision_type})")
            
            if len(decisions) > 5:
                print(f"  ... and {len(decisions) - 5} more")
        
        # Ask if user wants to run sync
        print(f"\nWould you like to sync {len(decisions)} decisions to Notion? (y/n): ", end="")
        response = input().lower().strip()
        
        if response == 'y' or response == 'yes':
            print("\nRunning sync...")
            result = agent.sync_all_decisions()
            
            if result["success"]:
                print("✓ Sync completed successfully")
                stats = result.get("stats", {})
                print(f"  Synced: {stats.get('successfully_synced', 0)}")
                print(f"  Failed: {stats.get('failed_sync', 0)}")
            else:
                print("✗ Sync failed")
                print(f"  Error: {result.get('error', 'Unknown error')}")
        else:
            print("Sync cancelled by user")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_memory_sync()
    if success:
        print("\n✓ Test completed")
    else:
        print("\n✗ Test failed")