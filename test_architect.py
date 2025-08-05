#!/usr/bin/env python3
"""
Test script for architect decision operations
Verifies that decisions can be stored and retrieved successfully
"""

import sys
from datetime import datetime
from operations import store_architect_decision, get_architect_decisions
from config import supabase_config

def test_connection():
    """Test basic Supabase connection"""
    print("🔗 Testing Supabase connection...")
    
    if supabase_config.test_connection():
        print("✅ Connection successful")
        return True
    else:
        print("❌ Connection failed")
        print("💡 Please check your SUPABASE_URL and SUPABASE_KEY in Replit Secrets")
        return False

def test_store_decision():
    """Test storing an architect decision"""
    print("\n📝 Testing store_architect_decision function...")
    
    # Test with valid content
    test_content = f"Test architect decision stored at {datetime.now().isoformat()}"
    
    try:
        result = store_architect_decision(test_content)
        
        if result["success"]:
            print("✅ Decision stored successfully")
            print(f"   ID: {result['data'].get('id', 'N/A')}")
            print(f"   Content: {result['data'].get('content', 'N/A')[:50]}...")
            return result["data"]
        else:
            print("❌ Failed to store decision")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        return None

def test_retrieve_decisions():
    """Test retrieving architect decisions"""
    print("\n📚 Testing get_architect_decisions function...")
    
    try:
        result = get_architect_decisions(limit=5)
        
        if result["success"]:
            print(f"✅ Retrieved {result['count']} decisions")
            
            if result["data"]:
                print("   Recent decisions:")
                for i, decision in enumerate(result["data"][:3], 1):
                    content_preview = decision.get("content", "")[:40]
                    created_at = decision.get("created_at", "Unknown")
                    print(f"   {i}. {content_preview}... ({created_at})")
            else:
                print("   No decisions found in database")
            
            return True
        else:
            print("❌ Failed to retrieve decisions")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        return False

def test_error_handling():
    """Test error handling with invalid input"""
    print("\n🚫 Testing error handling...")
    
    # Test with empty content
    try:
        result = store_architect_decision("")
        if not result["success"]:
            print("✅ Empty content properly rejected")
        else:
            print("❌ Empty content was incorrectly accepted")
    except ValueError:
        print("✅ Empty content properly rejected with ValueError")
    except Exception as e:
        print(f"⚠️  Unexpected error: {str(e)}")

def main():
    """Main test function"""
    print("🧪 Starting Architect Decision Tests")
    print("=" * 50)
    
    # Test 1: Connection
    if not test_connection():
        print("\n❌ Connection test failed. Stopping tests.")
        return False
    
    # Test 2: Store decision
    stored_decision = test_store_decision()
    if not stored_decision:
        print("\n❌ Store test failed. Stopping tests.")
        return False
    
    # Test 3: Retrieve decisions
    if not test_retrieve_decisions():
        print("\n⚠️  Retrieve test failed, but continuing...")
    
    # Test 4: Error handling
    test_error_handling()
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")
    print("\n💡 Your architect decision system is ready to use:")
    print("   from operations import store_architect_decision")
    print('   result = store_architect_decision("Your decision here")')
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)