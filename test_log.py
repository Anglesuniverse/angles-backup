#!/usr/bin/env python3
"""
Test script for log_to_notion function
"""

from log_to_notion import log_to_notion, test_notion_connection

def main():
    """Test the Notion logging functionality"""
    
    print("Notion Logger Test")
    print("=" * 40)
    
    # Test 1: Connection test
    print("Test 1: Testing Notion connection...")
    if test_notion_connection():
        print("✅ Notion connection successful")
    else:
        print("❌ Notion connection failed")
        print("Make sure you have:")
        print("- NOTION_DATABASE_ID environment variable set")
        print("- NOTION_API_KEY environment variable set")
        print("- Notion integration has access to the database")
        return
    
    print("\n" + "-" * 40)
    
    # Test 2: Log simple message
    print("Test 2: Logging simple message...")
    result1 = log_to_notion("Test message from Python script")
    print(f"Result: {'✅ Success' if result1 else '❌ Failed'}")
    
    print("\n" + "-" * 40)
    
    # Test 3: Log message with tags
    print("Test 3: Logging message with tags...")
    result2 = log_to_notion(
        message="I approve technical autonomy for AI",
        tags=["decision", "core", "technical"]
    )
    print(f"Result: {'✅ Success' if result2 else '❌ Failed'}")
    
    print("\n" + "-" * 40)
    
    # Test 4: Log message with different tags
    print("Test 4: Logging another message...")
    result3 = log_to_notion(
        message="Implementing new logging system for better tracking",
        tags=["development", "logging", "enhancement"]
    )
    print(f"Result: {'✅ Success' if result3 else '❌ Failed'}")
    
    print("\n" + "-" * 40)
    
    # Test 5: Test with empty tags
    print("Test 5: Testing with empty tags...")
    result4 = log_to_notion(
        message="Message without tags",
        tags=[]
    )
    print(f"Result: {'✅ Success' if result4 else '❌ Failed'}")
    
    # Summary
    print("\n" + "=" * 40)
    tests_passed = sum([result1, result2, result3, result4])
    print(f"Tests passed: {tests_passed}/4")
    
    if tests_passed >= 3:
        print("✅ Notion logging is working!")
        print("\n💡 Usage:")
        print("from log_to_notion import log_to_notion")
        print('log_to_notion("Your message", ["tag1", "tag2"])')
    else:
        print("❌ Some tests failed. Check your Notion setup.")
        print("\n🔧 Troubleshooting:")
        print("1. Verify NOTION_DATABASE_ID is correct")
        print("2. Verify NOTION_API_KEY is correct")
        print("3. Check that integration has access to the database")
        print("4. Ensure database has 'message', 'date', and 'tag' properties")

if __name__ == "__main__":
    main()