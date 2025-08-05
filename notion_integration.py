"""
Notion API client for managing architect decisions
Connects to Notion database and syncs with Supabase
"""

import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

class NotionClient:
    """Client for Notion API operations"""
    
    def __init__(self):
        self.token = os.getenv("NOTION_TOKEN")
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        self._client = None
        
        if not self.token:
            raise ValueError("NOTION_TOKEN environment variable is required")
        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID environment variable is required")
    
    @property
    def client(self) -> Client:
        """Get or create Notion client instance"""
        if self._client is None:
            self._client = Client(auth=self.token)
        return self._client
    
    def test_connection(self) -> bool:
        """Test the Notion connection"""
        try:
            # Test by retrieving database info
            response = self.client.databases.retrieve(database_id=self.database_id)
            return response is not None
        except Exception as e:
            print(f"Notion connection test failed: {e}")
            return False
    
    def get_database_info(self) -> dict:
        """Get database information and schema"""
        try:
            response = self.client.databases.retrieve(database_id=self.database_id)
            return {
                "success": True,
                "title": response.get("title", [{}])[0].get("plain_text", "Unknown"),
                "properties": list(response.get("properties", {}).keys()),
                "id": response.get("id")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_decision_to_notion(self, content: str, status: str = "active") -> dict:
        """Add an architect decision to Notion database"""
        try:
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": content[:100]  # Notion title limit
                            }
                        }
                    ]
                }
            }
            
            # Add content as rich text if there's a content property
            db_info = self.get_database_info()
            if db_info["success"] and "Content" in db_info["properties"]:
                properties["Content"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": content
                            }
                        }
                    ]
                }
            
            # Add status if there's a status property
            if db_info["success"] and "Status" in db_info["properties"]:
                properties["Status"] = {
                    "select": {
                        "name": status
                    }
                }
            
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            return {
                "success": True,
                "page_id": response["id"],
                "url": response["url"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_decisions_from_notion(self, limit: int = 10) -> dict:
        """Retrieve architect decisions from Notion database"""
        try:
            response = self.client.databases.query(
                database_id=self.database_id,
                page_size=limit,
                sorts=[
                    {
                        "timestamp": "created_time",
                        "direction": "descending"
                    }
                ]
            )
            
            decisions = []
            for page in response.get("results", []):
                title = ""
                content = ""
                
                # Extract title
                title_prop = page.get("properties", {}).get("Name", {})
                if title_prop.get("title"):
                    title = title_prop["title"][0]["plain_text"]
                
                # Extract content if available
                content_prop = page.get("properties", {}).get("Content", {})
                if content_prop.get("rich_text"):
                    content = content_prop["rich_text"][0]["plain_text"]
                
                decisions.append({
                    "id": page["id"],
                    "title": title,
                    "content": content or title,
                    "created_time": page["created_time"],
                    "url": page["url"]
                })
            
            return {
                "success": True,
                "data": decisions,
                "count": len(decisions)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Global client instance
notion_client = NotionClient()