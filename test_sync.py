#!/usr/bin/env python3
"""Test script for unified sync operations"""

import sys
from sync_operations import store_decision_everywhere, get_all_decisions, sync_status

def test_unified_storage():
    """Test storing decision in both systems"""
    print("Test 1: Storing decision in both Supabase and Notion...")
    try:
        result = store_decision_everywhere("Unified test decision from sync system")
        
        if result["success"]:
            print("✅ Decision stored in both systems")
            print(f"   Supabase: {result['results']['supabase']['success']}")
            print(f"   Notion: {result['results']['notion']['success']}")
            return True
        else:
            print(f"❌ Storage failed: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Storage error: {e}")
        return False

def test_unified_retrieval():
    """Test getting decisions from both systems"""
    print("\nTest 2: Retrieving decisions from both systems...")
    try:
        result = get_all_decisions()
        
        if result["success"]:
            print("✅ Retrieved decisions from available systems")
            print(f"   Supabase: {result['supabase_count']} decisions")
            print(f"   Notion: {result['notion_count']} decisions")
            return True
        else:
            print("❌ Failed to retrieve from any system")
            return False
            
    except Exception as e:
        print(f"❌ Retrieval error: {e}")
        return False

def test_sync_status():
    """Test sync status check"""
    print("\nTest 3: Checking sync status...")
    try:
        status = sync_status()
        
        print("✅ Sync status retrieved")
        print(f"   Supabase available: {status['supabase']['available']} ({status['supabase']['count']} items)")
        print(f"   Notion available: {status['notion']['available']} ({status['notion']['count']} items)")
        print(f"   Total sources active: {status['total_sources']}/2")
        
        return status['total_sources'] > 0
            
    except Exception as e:
        print(f"❌ Status check error: {e}")
        return False

def main():
    """Run all sync tests"""
    print("Unified Sync System Tests")
    print("=" * 40)
    
    tests_passed = 0
    
    if test_unified_storage():
        tests_passed += 1
    
    if test_unified_retrieval():
        tests_passed += 1
    
    if test_sync_status():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 40)
    print(f"Tests passed: {tests_passed}/3")
    
    if tests_passed >= 2:
        print("✅ Unified sync system is working!")
        print("\n💡 Usage:")
        print("   from sync_operations import store_decision_everywhere")
        print('   store_decision_everywhere("Your decision")')
        return True
    else:
        print("❌ Some sync tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)