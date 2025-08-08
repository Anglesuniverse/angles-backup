#!/usr/bin/env python3
"""
Simple test script to verify Supabase connection and show available tables
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test Supabase connection and list available tables"""
    
    # Get credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    print(f"Testing connection to: {url}")
    print(f"Using key (first 10 chars): {key[:10] if key else 'None'}...")
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY")
        return False
    
    try:
        # Create client
        supabase = create_client(url, key)
        print("✅ Supabase client created successfully")
        
        # Try a simple query to test connection - check auth
        result = supabase.auth.get_user()
        print("✅ Basic connection test successful")
        
        # Try to access any table to verify permissions
        try:
            # This will fail if no tables exist, but succeed if we have access
            tables_result = supabase.table('conversations').select("*").limit(1).execute()
            print("✅ Database access confirmed - 'conversations' table accessible")
        except Exception as table_error:
            print(f"ℹ️  Table access test: {str(table_error)}")
            if "relation" in str(table_error) and "does not exist" in str(table_error):
                print("💡 This means the connection works but tables need to be created first")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        
        # Try to give more specific error info
        if "Invalid API key" in str(e):
            print("💡 The API key appears to be invalid. Please check:")
            print("   1. Is this the correct 'anon' or 'public' key from your Supabase dashboard?")
            print("   2. Is the key copied completely without extra spaces?")
            print("   3. Is this key from the correct Supabase project?")
        
        return False

if __name__ == "__main__":
    test_connection()