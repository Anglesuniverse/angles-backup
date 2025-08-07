"""
Notion Logger Module
Logs messages with tags to a Notion database using the Notion API
"""

import os
import requests
from datetime import date
from typing import List, Dict, Any

def log_to_notion(message: str, tags: List[str] = []) -> bool:
    """
    Log a message with tags to a Notion database
    
    Args:
        message: The message to log (will be used as title)
        tags: List of tags for multi-select property
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    # Get environment variables
    database_id = os.getenv('NOTION_DATABASE_ID')
    api_key = os.getenv('NOTION_API_KEY')
    
    if not database_id:
        print("Error: NOTION_DATABASE_ID environment variable not found")
        return False
    
    if not api_key:
        print("Error: NOTION_API_KEY environment variable not found")
        return False
    
    if not message or not message.strip():
        print("Error: Message cannot be empty")
        return False
    
    # Prepare headers for Notion API
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Prepare tags for multi-select property
    tag_objects = []
    for tag in tags:
        if tag and tag.strip():
            tag_objects.append({"name": tag.strip()})
    
    # Prepare the data payload using correct Notion property names
    data = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": message.strip()[:100]  # Shorter for title
                        }
                    }
                ]
            },
            "Message": {
                "rich_text": [
                    {
                        "text": {
                            "content": message.strip()
                        }
                    }
                ]
            },
            "Date": {
                "date": {
                    "start": date.today().isoformat()
                }
            },
            "Tag": {
                "multi_select": tag_objects
            }
        }
    }
    
    try:
        # Make request to Notion API
        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"Successfully logged to Notion: {message}")
            return True
        else:
            print(f"Failed to log to Notion. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def test_notion_connection() -> bool:
    """
    Test the Notion API connection by checking if the database exists
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    
    database_id = os.getenv('NOTION_DATABASE_ID')
    api_key = os.getenv('NOTION_API_KEY')
    
    if not database_id or not api_key:
        print("Error: Missing NOTION_DATABASE_ID or NOTION_API_KEY")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28"
    }
    
    try:
        response = requests.get(
            f"https://api.notion.com/v1/databases/{database_id}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            database_info = response.json()
            print(f"✅ Connected to Notion database: {database_info.get('title', [{}])[0].get('plain_text', 'Unknown')}")
            return True
        else:
            print(f"❌ Failed to connect to Notion database. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False