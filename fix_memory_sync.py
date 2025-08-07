#!/usr/bin/env python3
"""
Fix memory sync agent by checking Notion database properties
and updating the sync logic accordingly
"""

import os
import requests
from config import supabase

def check_notion_database_properties():
    """Check what properties actually exist in the Notion database"""
    
    notion_database_id = os.getenv('NOTION_DATABASE_ID')
    notion_api_key = os.getenv('NOTION_API_KEY')
    
    if not notion_database_id or not notion_api_key:
        print("Missing NOTION_DATABASE_ID or NOTION_API_KEY")
        return None
    
    headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Notion-Version": "2022-06-28"
    }
    
    try:
        response = requests.get(
            f"https://api.notion.com/v1/databases/{notion_database_id}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            database_info = response.json()
            properties = database_info.get('properties', {})
            
            print("Notion Database Properties:")
            print("=" * 40)
            for prop_name, prop_info in properties.items():
                prop_type = prop_info.get('type', 'unknown')
                print(f"- {prop_name}: {prop_type}")
            
            return properties
        else:
            print(f"Failed to get database info: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"Error checking database: {e}")
        return None

def add_synced_column_to_supabase():
    """Add synced column to decision_vault table"""
    
    print("\nAdding synced column to Supabase...")
    try:
        # Check if column already exists
        result = supabase.table("decision_vault").select("synced").limit(1).execute()
        print("✓ Synced column already exists")
        return True
    except Exception as e:
        if "column" in str(e).lower() and "synced" in str(e).lower():
            print("✗ Synced column doesn't exist")
            print("\nPlease run this SQL in your Supabase SQL Editor:")
            print("-" * 50)
            print("ALTER TABLE decision_vault ADD COLUMN synced BOOLEAN DEFAULT FALSE;")
            print("ALTER TABLE decision_vault ADD COLUMN synced_at TIMESTAMPTZ;")
            print("UPDATE decision_vault SET synced = FALSE WHERE synced IS NULL;")
            print("-" * 50)
            return False
        else:
            print(f"Error checking synced column: {e}")
            return False

def main():
    """Check both Notion and Supabase setup"""
    
    print("Memory Sync Troubleshooting")
    print("=" * 40)
    
    # Check Notion database properties
    properties = check_notion_database_properties()
    
    # Check Supabase synced column
    add_synced_column_to_supabase()
    
    if properties:
        print("\n💡 To fix the sync script:")
        print("The memory sync agent expects these property names:")
        print("- message (title)")
        print("- date (date)")
        print("- tag (multi_select)")
        print("\nBut your Notion database has different property names.")
        print("You need to either:")
        print("1. Rename properties in Notion to match, OR")
        print("2. Update the sync script to use your property names")

if __name__ == "__main__":
    main()