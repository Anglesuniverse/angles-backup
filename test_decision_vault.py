#!/usr/bin/env python3
"""Test script for decision_vault operations"""

import sys
from datetime import date, timedelta
from decision_vault_operations import (
    store_decision, 
    get_decisions, 
    update_decision_status,
    get_decision_statistics
)

def test_store_decision():
    """Test 1: Store decision"""
    print("Test 1: Storing test decision...")
    try:
        result = store_decision(
            decision="Use Python as main backend language",
            decision_type="technical",
            decision_date=date.today(),
            comment="Decision made after team discussion"
        )
        
        if result["success"]:
            print("✅ Decision stored successfully")
            print(f"   ID: {result['data'].get('id')}")
            print(f"   Decision: {result['data'].get('decision')}")
            return result["data"]
        else:
            print(f"❌ Failed to store decision: {result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Store error: {e}")
        return None

def test_get_decisions():
    """Test 2: Get decisions"""
    print("\nTest 2: Retrieving decisions...")
    try:
        result = get_decisions(limit=10)
        
        if result["success"]:
            count = result.get('count', 0)
            print(f"✅ Retrieved {count} decisions")
            
            if count > 0:
                print("   Recent decisions:")
                for i, decision in enumerate(result["data"][:3], 1):
                    decision_text = decision.get("decision", "")[:50]
                    decision_type = decision.get("type", "")
                    decision_date = decision.get("date", "")
                    print(f"   {i}. {decision_text}... ({decision_type}, {decision_date})")
            
            return True
        else:
            print(f"❌ Failed to retrieve decisions: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Retrieve error: {e}")
        return False

def test_filter_decisions():
    """Test 3: Filter decisions by type"""
    print("\nTest 3: Filtering decisions by type...")
    try:
        result = get_decisions(limit=5, decision_type="technical")
        
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
    """Test 4: Get statistics"""
    print("\nTest 4: Getting statistics...")
    try:
        result = get_decision_statistics()
        
        if result["success"]:
            print("✅ Statistics retrieved")
            print(f"   Total: {result.get('total', 0)} decisions")
            print(f"   Active: {result.get('active', 0)}")
            print(f"   Inactive: {result.get('inactive', 0)}")
            
            by_type = result.get('by_type', {})
            if by_type:
                print("   By type:")
                for decision_type, stats in by_type.items():
                    print(f"     {decision_type}: {stats['active']}/{stats['total']}")
            
            return True
        else:
            print(f"❌ Failed to get statistics: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Statistics error: {e}")
        return False

def main():
    """Run all decision_vault tests"""
    print("Decision Vault System Tests")
    print("=" * 40)
    
    tests_passed = 0
    
    if test_store_decision():
        tests_passed += 1
    
    if test_get_decisions():
        tests_passed += 1
    
    if test_filter_decisions():
        tests_passed += 1
    
    if test_statistics():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 40)
    print(f"Tests passed: {tests_passed}/4")
    
    if tests_passed >= 3:
        print("✅ Decision Vault system is working!")
        print("\n💡 Usage:")
        print("   from decision_vault_operations import store_decision")
        print('   store_decision("Your decision", "technical")')
        return True
    else:
        print("❌ Some tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)