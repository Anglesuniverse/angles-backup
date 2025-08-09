"""
Angles OS™ Notion Integration
Connector for syncing data to Notion databases
"""
from typing import Optional, Dict, Any, List
from api.config import settings
from api.utils.logging import logger

try:
    from notion_client import Client
    _notion_available = True
except ImportError:
    _notion_available = False
    logger.warning("Notion client library not available")

class NotionConnector:
    """Notion database connector"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        
        if _notion_available and settings.has_notion():
            try:
                self.client = Client(auth=settings.notion_api_key)
                logger.info("Notion client initialized")
            except Exception as e:
                logger.error(f"Notion client initialization failed: {e}")
    
    def is_available(self) -> bool:
        """Check if Notion is available"""
        return self.client is not None
    
    def create_page(self, database_id: str, properties: Dict[str, Any]) -> Optional[str]:
        """Create a page in Notion database"""
        if not self.is_available():
            logger.warning("Notion not available for page creation")
            return None
        
        try:
            # Format properties for Notion API
            formatted_properties = self._format_properties(properties)
            
            response = self.client.pages.create(
                parent={"database_id": database_id},
                properties=formatted_properties
            )
            
            page_id = response['id']
            logger.info(f"Created Notion page: {page_id}")
            return page_id
            
        except Exception as e:
            logger.error(f"Failed to create Notion page: {e}")
            return None
    
    def sync_vault_chunk(self, database_id: str, chunk_data: Dict[str, Any]) -> bool:
        """Sync vault chunk to Notion database"""
        # TODO: Map vault chunk fields to Notion database properties
        properties = {
            'Title': chunk_data.get('source', 'Unknown Source'),
            'Content': chunk_data.get('chunk', ''),
            'Summary': chunk_data.get('summary', ''),
            'Source': chunk_data.get('source', ''),
            'Created': chunk_data.get('created_at', '')
        }
        
        result = self.create_page(database_id, properties)
        return result is not None
    
    def sync_decision(self, database_id: str, decision_data: Dict[str, Any]) -> bool:
        """Sync decision to Notion database"""
        # TODO: Map decision fields to Notion database properties
        properties = {
            'Title': decision_data.get('topic', 'Decision'),
            'Status': decision_data.get('status', 'open'),
            'Chosen': decision_data.get('chosen', ''),
            'Rationale': decision_data.get('rationale', ''),
            'Created': decision_data.get('created_at', '')
        }
        
        result = self.create_page(database_id, properties)
        return result is not None
    
    def log_agent_activity(self, database_id: str, agent: str, level: str, 
                          message: str, meta: Optional[Dict[str, Any]] = None) -> bool:
        """Log agent activity to Notion"""
        properties = {
            'Title': f"{agent} - {level}",
            'Agent': agent,
            'Level': level,
            'Message': message,
            'Metadata': str(meta) if meta else '',
            'Timestamp': ''  # Will be filled by Notion
        }
        
        result = self.create_page(database_id, properties)
        return result is not None
    
    def _format_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Format properties for Notion API"""
        formatted = {}
        
        for key, value in properties.items():
            if isinstance(value, str):
                if key.lower() in ['title', 'name']:
                    formatted[key] = {
                        "title": [{"text": {"content": value}}]
                    }
                else:
                    formatted[key] = {
                        "rich_text": [{"text": {"content": value}}]
                    }
            elif isinstance(value, bool):
                formatted[key] = {"checkbox": value}
            elif isinstance(value, (int, float)):
                formatted[key] = {"number": value}
            else:
                # Default to rich text
                formatted[key] = {
                    "rich_text": [{"text": {"content": str(value)}}]
                }
        
        return formatted
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Notion connection"""
        if not self.is_available():
            return {'status': 'unavailable', 'error': 'Not configured'}
        
        try:
            # Try to get user info
            user = self.client.users.me()
            return {
                'status': 'healthy',
                'user_id': user.get('id'),
                'user_name': user.get('name', 'Unknown')
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def get_databases(self) -> List[Dict[str, Any]]:
        """Get available databases (requires proper permissions)"""
        if not self.is_available():
            return []
        
        try:
            response = self.client.search(
                filter={"property": "object", "value": "database"}
            )
            
            databases = []
            for result in response.get('results', []):
                databases.append({
                    'id': result['id'],
                    'title': self._extract_title(result.get('title', [])),
                    'url': result.get('url', '')
                })
            
            return databases
            
        except Exception as e:
            logger.error(f"Failed to get databases: {e}")
            return []
    
    def _extract_title(self, title_array: List[Dict[str, Any]]) -> str:
        """Extract title from Notion title array"""
        if not title_array:
            return "Untitled"
        
        return "".join([item.get('plain_text', '') for item in title_array])