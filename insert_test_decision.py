#!/usr/bin/env python3
"""
Insert test decision into Supabase table
"""

from datetime import datetime
from decision_vault_operations import store_decision
from ai_decision_logger import log_ai_decision

def insert_test_decision():
    """Insert the Swedish test decision"""
    
    # Test data
    message = "Jag godkänner teknisk autonomi för AI."
    date_str = "2025-08-07" 
    tags = ["beslut", "core"]
    
    print("Inserting test decision into Supabase...")
    print(f"Message: {message}")
    print(f"Date: {date_str}")
    print(f"Tags: {tags}")
    print("-" * 50)
    
    # Try decision_vault table first (matches your Swedish data)
    print("Attempting to insert into decision_vault table...")
    try:
        from datetime import date
        decision_date = date.fromisoformat(date_str)
        
        result = store_decision(
            decision=message,
            decision_type="strategy",  # Based on the "beslut" tag
            decision_date=decision_date,
            active=True,
            comment=f"Tags: {', '.join(tags)}"
        )
        
        if result["success"]:
            print("✅ Successfully inserted into decision_vault table!")
            print(f"   ID: {result['data'].get('id')}")
            print(f"   Decision: {result['data'].get('decision')}")
            print(f"   Type: {result['data'].get('type')}")
            print(f"   Date: {result['data'].get('date')}")
            print(f"   Comment: {result['data'].get('comment')}")
            return True
        else:
            print(f"❌ Failed to insert into decision_vault: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error with decision_vault: {e}")
    
    # Try ai_decision_log table as alternative
    print("\nAttempting to insert into ai_decision_log table...")
    try:
        result = log_ai_decision(
            decision_text=message,
            decision_type="strategy",
            context=f"Test decision with tags: {', '.join(tags)}",
            confidence=1.0,
            metadata={
                "tags": tags,
                "date": date_str,
                "language": "swedish"
            }
        )
        
        if result["success"]:
            print("✅ Successfully inserted into ai_decision_log table!")
            print(f"   ID: {result.get('id')}")
            print(f"   Decision: {result['data'].get('decision_text')}")
            print(f"   Type: {result['data'].get('decision_type')}")
            print(f"   Metadata: {result['data'].get('metadata')}")
            return True
        else:
            print(f"❌ Failed to insert into ai_decision_log: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error with ai_decision_log: {e}")
    
    print("\n❌ Could not insert into either table. Make sure tables exist in Supabase.")
    return False

if __name__ == "__main__":
    success = insert_test_decision()
    if success:
        print("\n🎉 Test decision successfully stored!")
    else:
        print("\n💡 To fix this:")
        print("1. Run the SQL scripts in Supabase to create the tables")
        print("2. Check your SUPABASE_URL and SUPABASE_KEY environment variables")