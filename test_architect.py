#!/usr/bin/env python3
"""Test script for architect decision operations"""

import sys
from operations import store_architect_decision, get_architect_decisions
from config import supabase_config

def test_connection():
    """Test 1: Supabase connection"""
    print("Test 1: Testing Supabase connection...")
    try:
        if supabase_config.test_connection():
            print("✅ Connection works")
            return True
        else:
            print("❌ Connection failed - check SUPABASE_URL and SUPABASE_KEY in Secrets")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_store_decision():
    """Test 2: Store a test decision"""
    print("\nTest 2: Storing test decision...")
    try:
        result = store_architect_decision("Test decision from script")
        
        if result["success"]:
            print("✅ Storing decision works")
            print(f"   Stored with ID: {result['data'].get('id')}")
            return True
        else:
            print(f"❌ Store failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Store error: {e}")
        return False

def test_retrieve_decisions():
    """Test 3: Retrieve decisions"""
    print("\nTest 3: Retrieving decisions...")
    try:
        result = get_architect_decisions(limit=10)
        
        if result["success"]:
            count = result.get('count', 0)
            print(f"✅ Retrieving works - found {count} decisions")
            
            if count > 0:
                print("   Recent decisions:")
                for i, decision in enumerate(result["data"][:3], 1):
                    content = decision.get("content", "")[:50]
                    print(f"   {i}. {content}...")
            
            return True
        else:
            print(f"❌ Retrieve failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Retrieve error: {e}")
        return False

def main():
    """Run all tests"""
    print("Architect Decision Tests")
    print("=" * 40)
    
    # Run tests
    tests_passed = 0
    
    if test_connection():
        tests_passed += 1
    
    if test_store_decision():
        tests_passed += 1
    
    if test_retrieve_decisions():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 40)
    print(f"Tests passed: {tests_passed}/3")
    
    if tests_passed == 3:
        print("✅ All tests passed! System is ready.")
        return True
    else:
        print("❌ Some tests failed. Check your Supabase setup.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)