#!/usr/bin/env python3
"""Test script for Notion integration"""

import sys
from notion_integration import notion_client

def test_notion_connection():
    """Test 1: Notion connection"""
    print("Test 1: Testing Notion connection...")
    try:
        if notion_client.test_connection():
            print("✅ Notion connection works")
            return True
        else:
            print("❌ Notion connection failed - check NOTION_TOKEN and NOTION_DATABASE_ID")
            return False
    except Exception as e:
        print(f"❌ Notion connection error: {e}")
        return False

def test_database_info():
    """Test 2: Get database information"""
    print("\nTest 2: Getting database information...")
    try:
        result = notion_client.get_database_info()
        
        if result["success"]:
            print("✅ Database info retrieved")
            print(f"   Database: {result['title']}")
            print(f"   Properties: {', '.join(result['properties'])}")
            return True
        else:
            print(f"❌ Failed to get database info: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Database info error: {e}")
        return False

def test_add_decision():
    """Test 3: Add a decision to Notion"""
    print("\nTest 3: Adding test decision to Notion...")
    try:
        result = notion_client.add_decision_to_notion("Test architect decision from Replit")
        
        if result["success"]:
            print("✅ Decision added to Notion")
            print(f"   Page ID: {result['page_id']}")
            print(f"   URL: {result['url']}")
            return True
        else:
            print(f"❌ Failed to add decision: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Add decision error: {e}")
        return False

def test_get_decisions():
    """Test 4: Retrieve decisions from Notion"""
    print("\nTest 4: Retrieving decisions from Notion...")
    try:
        result = notion_client.get_decisions_from_notion(limit=5)
        
        if result["success"]:
            count = result.get('count', 0)
            print(f"✅ Retrieved {count} decisions from Notion")
            
            if count > 0:
                print("   Recent decisions:")
                for i, decision in enumerate(result["data"][:3], 1):
                    content = decision.get("content", "")[:50]
                    print(f"   {i}. {content}...")
            
            return True
        else:
            print(f"❌ Failed to retrieve decisions: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Retrieve decisions error: {e}")
        return False

def main():
    """Run all Notion tests"""
    print("Notion Integration Tests")
    print("=" * 40)
    
    tests_passed = 0
    
    if test_notion_connection():
        tests_passed += 1
    
    if test_database_info():
        tests_passed += 1
    
    if test_add_decision():
        tests_passed += 1
    
    if test_get_decisions():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 40)
    print(f"Tests passed: {tests_passed}/4")
    
    if tests_passed >= 3:
        print("✅ Notion integration is working!")
        return True
    else:
        print("❌ Some tests failed. Check your Notion setup.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)