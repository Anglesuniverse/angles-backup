#!/usr/bin/env python3
"""Test script for AI Decision Logger"""

import sys
from datetime import datetime
from ai_decision_logger import (
    log_ai_decision,
    get_recent_ai_decisions,
    get_ai_decision_stats,
    AIDecisionLogger
)

def test_log_decision():
    """Test 1: Log AI decision"""
    print("Test 1: Logging AI decision...")
    try:
        result = log_ai_decision(
            decision_text="Recommended using FastAPI over Flask for better async support",
            decision_type="technical",
            context="User building a real-time chat application",
            confidence=0.89,
            metadata={
                "factors": ["async support", "performance", "type hints"],
                "alternatives_considered": ["Flask", "Django"]
            }
        )
        
        if result["success"]:
            print("✅ AI decision logged successfully")
            print(f"   ID: {result.get('id')}")
            print(f"   Decision: {result['data'].get('decision_text')[:50]}...")
            return result["data"]
        else:
            print(f"❌ Failed to log decision: {result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Log error: {e}")
        return None

def test_get_recent_decisions():
    """Test 2: Get recent decisions"""
    print("\nTest 2: Retrieving recent AI decisions...")
    try:
        result = get_recent_ai_decisions(limit=5)
        
        if result["success"]:
            count = result.get('count', 0)
            print(f"✅ Retrieved {count} recent decisions")
            
            if count > 0:
                print("   Recent decisions:")
                for i, decision in enumerate(result["data"][:3], 1):
                    decision_text = decision.get("decision_text", "")[:40]
                    decision_type = decision.get("decision_type", "")
                    timestamp = decision.get("timestamp", "")
                    confidence = decision.get("confidence", "N/A")
                    print(f"   {i}. {decision_text}... ({decision_type}, conf: {confidence})")
            
            return True
        else:
            print(f"❌ Failed to retrieve decisions: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Retrieve error: {e}")
        return False

def test_filter_by_type():
    """Test 3: Filter decisions by type"""
    print("\nTest 3: Filtering decisions by type...")
    try:
        result = get_recent_ai_decisions(limit=5, decision_type="technical")
        
        if result["success"]:
            count = result.get('count', 0)
            print(f"✅ Retrieved {count} technical decisions")
            return True
        else:
            print(f"❌ Failed to filter: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Filter error: {e}")
        return False

def test_statistics():
    """Test 4: Get decision statistics"""
    print("\nTest 4: Getting AI decision statistics...")
    try:
        result = get_ai_decision_stats()
        
        if result["success"]:
            print("✅ Statistics retrieved")
            print(f"   Total decisions: {result.get('total_decisions', 0)}")
            print(f"   Average confidence: {result.get('avg_confidence', 'N/A')}")
            
            by_type = result.get('by_type', {})
            if by_type:
                print("   Decisions by type:")
                for decision_type, count in by_type.items():
                    print(f"     {decision_type}: {count}")
            
            return True
        else:
            print(f"❌ Failed to get statistics: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Statistics error: {e}")
        return False

def test_class_usage():
    """Test 5: Using the AIDecisionLogger class directly"""
    print("\nTest 5: Testing AIDecisionLogger class...")
    try:
        logger = AIDecisionLogger()
        
        result = logger.log_decision(
            decision_text="Suggested using Docker for consistent development environments",
            decision_type="infrastructure",
            context="Team experiencing environment inconsistencies",
            confidence=0.91
        )
        
        if result["success"]:
            print("✅ Class-based logging successful")
            return True
        else:
            print(f"❌ Class-based logging failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Class usage error: {e}")
        return False

def main():
    """Run all AI decision logger tests"""
    print("AI Decision Logger Tests")
    print("=" * 40)
    
    tests_passed = 0
    
    if test_log_decision():
        tests_passed += 1
    
    if test_get_recent_decisions():
        tests_passed += 1
    
    if test_filter_by_type():
        tests_passed += 1
    
    if test_statistics():
        tests_passed += 1
    
    if test_class_usage():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 40)
    print(f"Tests passed: {tests_passed}/5")
    
    if tests_passed >= 4:
        print("✅ AI Decision Logger is working!")
        print("\n💡 Usage examples:")
        print("   # Simple logging")
        print('   log_ai_decision("My AI decision", "technical")')
        print()
        print("   # With confidence and context")
        print('   log_ai_decision("Use React", "recommendation", ')
        print('                   context="Frontend choice", confidence=0.95)')
        print()
        print("   # Get recent decisions")
        print('   recent = get_recent_ai_decisions(10)')
        return True
    else:
        print("❌ Some tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)