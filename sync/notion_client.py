#!/usr/bin/env python3
"""
Notion client wrapper for bidirectional sync
Wrapper for Notion REST API for Angles AI Universe™

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

try:
    from notion_client import Client as NotionAPIClient
except ImportError:
    print("Warning: notion-client package not available")
    NotionAPIClient = None

from .config import get_config, NOTION_PROPERTY_MAPPING, DECISION_TYPES
from .logging_util import get_logger


class NotionClient:
    """Enhanced Notion client for sync operations"""
    
    def __init__(self):
        """Initialize Notion client"""
        self.config = get_config()
        self.logger = get_logger()
        
        if NotionAPIClient is None:
            raise ImportError("notion-client package is required")
        
        try:
            self.client = NotionAPIClient(auth=self.config.notion_api_key)
            self.database_id = self.config.notion_database_id
            self.logger.info("✅ Notion client initialized")
        except Exception as e:
            self.logger.error("❌ Failed to initialize Notion client", error=e)
            raise
    
    def test_connection(self) -> bool:
        """Test Notion connection by querying database"""
        try:
            # Test database access
            response = self.client.databases.query(
                database_id=self.database_id,
                page_size=1
            )
            self.logger.info("✅ Notion connection successful")
            return True
        except Exception as e:
            self.logger.error("❌ Notion connection failed", error=e)
            return False
    
    def fetch_all_pages(self) -> List[Dict[str, Any]]:
        """Fetch all pages from Notion database with pagination"""
        
        pages = []
        start_cursor = None
        
        self.logger.info("📥 Fetching Notion pages")
        
        while True:
            try:
                # Fetch batch with retry
                batch, next_cursor = self._fetch_batch_with_retry(start_cursor)
                
                if not batch:
                    break
                
                pages.extend(batch)
                self.logger.info(f"📥 Fetched {len(batch)} pages (total: {len(pages)})")
                
                # Rate limiting for Notion API
                time.sleep(self.config.rate_limit_delay)
                
                # Check if there are more pages
                if not next_cursor:
                    break
                
                start_cursor = next_cursor
                
            except Exception as e:
                self.logger.error(f"❌ Failed to fetch Notion pages", error=e)
                raise
        
        self.logger.info(f"✅ Fetched {len(pages)} total pages from Notion")
        return pages
    
    def _fetch_batch_with_retry(self, start_cursor: Optional[str] = None) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Fetch a batch of pages with retry logic"""
        
        for attempt in range(self.config.max_retries):
            try:
                # Query database
                query_params = {
                    'database_id': self.database_id,
                    'page_size': min(self.config.batch_size, 100)  # Notion max is 100
                }
                
                if start_cursor:
                    query_params['start_cursor'] = start_cursor
                
                response = self.client.databases.query(**query_params)
                
                pages = response.get('results', [])
                next_cursor = response.get('next_cursor')
                
                return pages, next_cursor
                
            except Exception as e:
                # Handle Notion rate limiting (429)
                if hasattr(e, 'status') and e.status == 429:
                    delay = self.config.retry_delay * (2 ** attempt) + 1  # Extra delay for rate limits
                    self.logger.warning(f"⚠️ Rate limited, retrying in {delay}s")
                    time.sleep(delay)
                elif attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2 ** attempt)
                    self.logger.warning(f"⚠️ Retry {attempt + 1}/{self.config.max_retries} after {delay}s", error=e)
                    time.sleep(delay)
                else:
                    raise
    
    def create_page(self, record: Dict[str, Any], dry_run: bool = False) -> Optional[Dict[str, Any]]:
        """Create a new page in Notion database"""
        
        if dry_run:
            self.logger.info(f"🔍 [DRY RUN] Would create Notion page for: {record.get('decision', 'Unknown')}")
            return {'id': f"dry_run_{record.get('id', 'unknown')}"}
        
        try:
            # Build page properties
            properties = self._build_page_properties(record)
            
            # Create page
            response = self.client.pages.create(
                parent={'database_id': self.database_id},
                properties=properties
            )
            
            page_id = response['id']
            self.logger.info(f"✅ Created Notion page: {page_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create Notion page", error=e, record=record.get('id'))
            raise
    
    def update_page(self, page_id: str, record: Dict[str, Any], dry_run: bool = False) -> Optional[Dict[str, Any]]:
        """Update an existing Notion page"""
        
        if dry_run:
            self.logger.info(f"🔍 [DRY RUN] Would update Notion page: {page_id}")
            return {'id': page_id}
        
        try:
            # Build page properties
            properties = self._build_page_properties(record)
            
            # Update page
            response = self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            
            self.logger.info(f"✅ Updated Notion page: {page_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update Notion page", error=e, page_id=page_id)
            raise
    
    def _build_page_properties(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Build Notion page properties from Supabase record"""
        
        properties = {}
        
        # Title property (Decision)
        if record.get('decision'):
            properties[NOTION_PROPERTY_MAPPING['decision']] = {
                'title': [{'text': {'content': str(record['decision'])}}]
            }
        
        # Multi-select property (Type)
        if record.get('type'):
            type_value = str(record['type'])
            if type_value in DECISION_TYPES:
                properties[NOTION_PROPERTY_MAPPING['type']] = {
                    'multi_select': [{'name': type_value}]
                }
        
        # Date property
        if record.get('date'):
            # Handle various date formats
            date_str = str(record['date'])
            if 'T' in date_str:
                date_str = date_str.split('T')[0]  # Extract date part
            
            properties[NOTION_PROPERTY_MAPPING['date']] = {
                'date': {'start': date_str}
            }
        
        # Checksum (Rich text)
        if record.get('checksum'):
            properties[NOTION_PROPERTY_MAPPING['checksum']] = {
                'rich_text': [{'text': {'content': str(record['checksum'])}}]
            }
        
        # Synced checkbox (optional)
        if 'synced' in NOTION_PROPERTY_MAPPING:
            properties[NOTION_PROPERTY_MAPPING['synced']] = {
                'checkbox': True
            }
        
        return properties
    
    def parse_page_to_record(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Notion page to Supabase record format"""
        
        properties = page.get('properties', {})
        
        record = {
            'notion_page_id': page['id'],
            'notion_synced': True
        }
        
        # Extract title (Decision)
        title_prop = properties.get(NOTION_PROPERTY_MAPPING['decision'], {})
        if title_prop.get('title'):
            title_text = title_prop['title'][0]['text']['content'] if title_prop['title'] else ''
            record['decision'] = title_text.strip()
        
        # Extract type (Multi-select)
        type_prop = properties.get(NOTION_PROPERTY_MAPPING['type'], {})
        if type_prop.get('multi_select'):
            if type_prop['multi_select']:
                record['type'] = type_prop['multi_select'][0]['name']
        
        # Extract date
        date_prop = properties.get(NOTION_PROPERTY_MAPPING['date'], {})
        if date_prop.get('date') and date_prop['date'].get('start'):
            record['date'] = date_prop['date']['start']
        
        # Extract checksum
        checksum_prop = properties.get(NOTION_PROPERTY_MAPPING['checksum'], {})
        if checksum_prop.get('rich_text'):
            if checksum_prop['rich_text']:
                record['checksum'] = checksum_prop['rich_text'][0]['text']['content']
        
        # Extract timestamps from Notion metadata
        if page.get('created_time'):
            record['created_at'] = page['created_time']
        if page.get('last_edited_time'):
            record['updated_at'] = page['last_edited_time']
        
        return record
    
    def find_page_by_checksum(self, checksum: str) -> Optional[Dict[str, Any]]:
        """Find page by checksum (fallback matching)"""
        
        try:
            # Query database with filter
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    'property': NOTION_PROPERTY_MAPPING['checksum'],
                    'rich_text': {
                        'equals': checksum
                    }
                }
            )
            
            results = response.get('results', [])
            if results:
                return results[0]  # Return first match
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to find page by checksum", error=e, checksum=checksum)
            return None
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        
        try:
            # Get total count by fetching all pages (Notion doesn't provide count directly)
            all_pages = self.fetch_all_pages()
            total_count = len(all_pages)
            
            return {
                'total': total_count,
                'with_checksum': len([p for p in all_pages if self._has_checksum(p)]),
                'without_checksum': len([p for p in all_pages if not self._has_checksum(p)])
            }
            
        except Exception as e:
            self.logger.error("❌ Failed to get database stats", error=e)
            return {'total': 0, 'with_checksum': 0, 'without_checksum': 0}
    
    def _has_checksum(self, page: Dict[str, Any]) -> bool:
        """Check if page has checksum property"""
        properties = page.get('properties', {})
        checksum_prop = properties.get(NOTION_PROPERTY_MAPPING['checksum'], {})
        return bool(checksum_prop.get('rich_text'))