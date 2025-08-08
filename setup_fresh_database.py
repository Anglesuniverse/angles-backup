#!/usr/bin/env python3
"""
Fresh database setup script for GPT Processor
Creates all necessary tables with proper schema
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def execute_sql_file(supabase_client, sql_file_path):
    """Execute SQL commands from a file"""
    try:
        with open(sql_file_path, 'r') as file:
            sql_content = file.read()
        
        # Split SQL commands by semicolon and execute each one
        sql_commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
        
        results = []
        for i, command in enumerate(sql_commands):
            if command.upper().startswith(('CREATE', 'DROP', 'INSERT', 'ALTER')):
                try:
                    print(f"Executing command {i+1}/{len(sql_commands)}: {command[:50]}...")
                    # Use the SQL editor functionality
                    result = supabase_client.postgrest.session.post(
                        f"{supabase_client.supabase_url}/rest/v1/rpc/exec_sql",
                        json={"sql": command},
                        headers=supabase_client.postgrest.session.headers
                    )
                    if result.status_code == 200:
                        print(f"✅ Command executed successfully")
                        results.append(("success", command[:50]))
                    else:
                        print(f"❌ Command failed: {result.text}")
                        results.append(("error", f"{command[:50]} - {result.text}"))
                except Exception as e:
                    print(f"❌ Error executing command: {str(e)}")
                    results.append(("error", f"{command[:50]} - {str(e)}"))
        
        return results
        
    except Exception as e:
        print(f"❌ Failed to read SQL file: {str(e)}")
        return [("error", str(e))]

def setup_fresh_database():
    """Set up fresh database with all necessary tables"""
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        print("Please update your Replit Secrets with the correct Supabase credentials")
        return False
    
    print(f"🔗 Connecting to Supabase: {url}")
    print(f"🔑 Using API key: {key[:10]}...")
    
    try:
        # Create Supabase client
        supabase = create_client(url, key)
        print("✅ Supabase client created successfully")
        
        # Test basic connection first
        try:
            # Try a simple auth check
            user_response = supabase.auth.get_user()
            print("✅ Authentication successful")
        except Exception as auth_error:
            print(f"❌ Authentication failed: {str(auth_error)}")
            if "Invalid API key" in str(auth_error):
                print("💡 Please verify your API key is correct:")
                print("   1. Go to your Supabase dashboard")
                print("   2. Navigate to Settings → API")
                print("   3. Copy the 'anon public' key (not service_role)")
                print("   4. Update your Replit Secrets")
            return False
        
        # Execute the SQL file
        print("\n📊 Setting up database tables...")
        results = execute_sql_file(supabase, "create_tables.sql")
        
        # Summary
        success_count = len([r for r in results if r[0] == "success"])
        error_count = len([r for r in results if r[0] == "error"])
        
        print(f"\n📈 Setup Summary:")
        print(f"   ✅ Successful operations: {success_count}")
        print(f"   ❌ Failed operations: {error_count}")
        
        if error_count > 0:
            print("\n🔍 Errors encountered:")
            for result_type, message in results:
                if result_type == "error":
                    print(f"   • {message}")
        
        # Test table access
        print("\n🧪 Testing table access...")
        test_tables = ["conversations", "memories", "tasks", "analysis"]
        
        for table in test_tables:
            try:
                result = supabase.table(table).select("id").limit(1).execute()
                print(f"   ✅ {table} table accessible")
            except Exception as e:
                print(f"   ❌ {table} table error: {str(e)}")
        
        if error_count == 0:
            print("\n🎉 Database setup completed successfully!")
            print("Your GPT Processor is ready to use.")
            return True
        else:
            print("\n⚠️  Database setup completed with some errors.")
            print("You may need to manually create some tables using the Supabase SQL editor.")
            return False
        
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = setup_fresh_database()
    sys.exit(0 if success else 1)