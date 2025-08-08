"""
Notion client wrapper for Angles AI Universe™
Handles Notion API operations with graceful degradation
"""

import logging
from typing import List, Optional
from datetime import datetime

from .config import has_notion, NOTION_API_KEY, NOTION_DATABASE_ID
from .utils import retry_with_backoff


logger = logging.getLogger(__name__)


class NotionClientWrap:
    """Wrapper for Notion operations with graceful fallback"""
    
    def __init__(self):
        self.available = has_notion()
        self.client = None
        
        if self.available:
            try:
                # Try to import and initialize notion-client
                from notion_client import Client
                self.client = Client(auth=NOTION_API_KEY)
            except ImportError:
                logger.warning("notion-client package not available")
                self.available = False
            except Exception as e:
                logger.warning(f"Failed to initialize Notion client: {e}")
                self.available = False
    
    def is_available(self) -> bool:
        """Check if Notion integration is available"""
        return self.available
    
    @retry_with_backoff(max_retries=3)
    def write_summary(self, title: str, text: str, tags: List[str] = None) -> bool:
        """Write summary to Notion database"""
        if not self.available:
            logger.info(f"Notion unavailable, skipping summary: {title}")
            return True
        
        try:
            properties = {
                'Name': {
                    'title': [
                        {
                            'text': {
                                'content': title[:100]  # Notion title limit
                            }
                        }
                    ]
                },
                'Content': {
                    'rich_text': [
                        {
                            'text': {
                                'content': text[:2000]  # Reasonable limit
                            }
                        }
                    ]
                },
                'Date': {
                    'date': {
                        'start': datetime.now().date().isoformat()
                    }
                }
            }
            
            # Add tags if provided and supported
            if tags:
                properties['Tags'] = {
                    'multi_select': [{'name': tag} for tag in tags[:10]]  # Limit tags
                }
            
            response = self.client.pages.create(
                parent={'database_id': NOTION_DATABASE_ID},
                properties=properties
            )
            
            logger.info(f"✅ Written to Notion: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write Notion summary: {e}")
            return False
    
    def write_deployment_summary(self, status: dict) -> bool:
        """Write deployment status summary to Notion"""
        title = f"Angles AI Deployment - {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
        
        text = f"""
Deployment Status: {'✅ Complete' if status.get('success') else '⚠️ Partial'}

Components:
- Migration: {status.get('migration', 'Unknown')}
- Memory Sync: {status.get('memory_sync', 'Unknown')}
- Historical Sweep: {status.get('historical_sweep', 'Unknown')}
- Backend Monitor: {status.get('backend_monitor', 'Unknown')}
- Scheduler: {status.get('scheduler', 'Unknown')}

Integrations:
- Supabase: {status.get('supabase', 'Unknown')}
- Notion: {status.get('notion', 'Unknown')}
- OpenAI: {status.get('openai', 'Unknown')}
- GitHub: {status.get('github', 'Unknown')}

Next Steps:
{chr(10).join(f'- {step}' for step in status.get('next_steps', ['System monitoring']))}
"""
        
        return self.write_summary(title, text, ['deployment', 'system'])
    
    def write_error_report(self, component: str, error: str, context: dict = None) -> bool:
        """Write error report to Notion"""
        title = f"Error Report: {component} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        text = f"""
Component: {component}
Error: {error}
Timestamp: {datetime.now().isoformat()}

Context: {context or 'None provided'}
"""
        
        return self.write_summary(title, text, ['error', 'system', component])