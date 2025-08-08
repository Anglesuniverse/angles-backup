#!/usr/bin/env python3
"""
Update the Swedish decision to English
"""

from config import supabase

def update_decision_to_english():
    """Update the Swedish decision to English"""
    
    # Original Swedish text
    swedish_text = "Jag godkänner teknisk autonomi för AI."
    
    # English translation
    english_text = "I approve technical autonomy for AI."
    
    print("Updating Swedish decision to English...")
    print(f"From: {swedish_text}")
    print(f"To: {english_text}")
    print("-" * 50)
    
    try:
        # Find the Swedish decision
        result = supabase.table("decision_vault").select("*").eq("decision", swedish_text).execute()
        
        if not result.data:
            print("❌ Swedish decision not found in database")
            return False
        
        decision_id = result.data[0]["id"]
        print(f"Found decision with ID: {decision_id}")
        
        # Update to English
        update_result = supabase.table("decision_vault").update({
            "decision": english_text,
            "comment": "Tags: decision, core"  # Also translate the comment
        }).eq("id", decision_id).execute()
        
        if update_result.data:
            print("✅ Successfully updated to English!")
            updated_decision = update_result.data[0]
            print(f"   Decision: {updated_decision.get('decision')}")
            print(f"   Type: {updated_decision.get('type')}")
            print(f"   Date: {updated_decision.get('date')}")
            print(f"   Comment: {updated_decision.get('comment')}")
            return True
        else:
            print("❌ Failed to update decision")
            return False
            
    except Exception as e:
        print(f"❌ Error updating decision: {e}")
        return False

if __name__ == "__main__":
    success = update_decision_to_english()
    if success:
        print("\n🎉 Decision successfully updated to English!")
    else:
        print("\n💡 Could not update decision")