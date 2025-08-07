#!/usr/bin/env python3
"""
Supabase client wrapper for bidirectional sync
Thin wrapper around supabase-py for Angles AI Universe™

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

try:
    from supabase import create_client, Client
except ImportError:
    print("Warning: supabase package not available")
    create_client = None
    Client = None

from .config import get_config, SUPABASE_TABLE
from .logging_util import get_logger


class SupabaseClient:
    """Enhanced Supabase client for sync operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        self.config = get_config()
        self.logger = get_logger()
        
        if create_client is None:
            raise ImportError("supabase package is required")
        
        try:
            self.client: Client = create_client(
                self.config.supabase_url,
                self.config.supabase_service_key
            )
            self.logger.info("✅ Supabase client initialized")
        except Exception as e:
            self.logger.error("❌ Failed to initialize Supabase client", error=e)
            raise
    
    def test_connection(self) -> bool:
        """Test Supabase connection"""
        try:
            # Simple test query
            result = self.client.table(SUPABASE_TABLE).select("id").limit(1).execute()
            self.logger.info("✅ Supabase connection successful")
            return True
        except Exception as e:
            self.logger.error("❌ Supabase connection failed", error=e)
            return False
    
    def fetch_all_records(self) -> List[Dict[str, Any]]:
        """Fetch all records from decision_vault with pagination"""
        
        records = []
        offset = 0
        batch_size = self.config.batch_size
        
        self.logger.info(f"📥 Fetching Supabase records (batch size: {batch_size})")
        
        while True:
            try:
                # Fetch batch with retry
                batch = self._fetch_batch_with_retry(offset, batch_size)
                
                if not batch:
                    break
                
                records.extend(batch)
                offset += len(batch)
                
                self.logger.info(f"📥 Fetched {len(batch)} records (total: {len(records)})")
                
                # Rate limiting
                time.sleep(self.config.rate_limit_delay)
                
                # Check if we got less than batch size (last page)
                if len(batch) < batch_size:
                    break
                    
            except Exception as e:
                self.logger.error(f"❌ Failed to fetch batch at offset {offset}", error=e)
                raise
        
        self.logger.info(f"✅ Fetched {len(records)} total records from Supabase")
        return records
    
    def _fetch_batch_with_retry(self, offset: int, limit: int) -> List[Dict[str, Any]]:
        """Fetch a batch of records with retry logic"""
        
        for attempt in range(self.config.max_retries):
            try:
                result = (self.client.table(SUPABASE_TABLE)
                         .select("*")
                         .range(offset, offset + limit - 1)
                         .order('created_at')
                         .execute())
                
                return result.data if result.data else []
                
            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                    self.logger.warning(f"⚠️ Retry {attempt + 1}/{self.config.max_retries} after {delay}s", error=e)
                    time.sleep(delay)
                else:
                    raise
    
    def upsert_record(self, record: Dict[str, Any], dry_run: bool = False) -> Optional[Dict[str, Any]]:
        """Insert or update a record in Supabase"""
        
        if dry_run:
            self.logger.info(f"🔍 [DRY RUN] Would upsert record: {record.get('id', 'new')}")
            return record
        
        try:
            # Set updated timestamp
            record['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Upsert record
            result = (self.client.table(SUPABASE_TABLE)
                     .upsert(record)
                     .execute())
            
            if result.data:
                upserted = result.data[0]
                self.logger.info(f"✅ Upserted record: {upserted.get('id')}")
                return upserted
            else:
                self.logger.error("❌ Upsert failed: no data returned")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Failed to upsert record", error=e, record_id=record.get('id'))
            raise
    
    def bulk_upsert_records(self, records: List[Dict[str, Any]], dry_run: bool = False) -> List[Dict[str, Any]]:
        """Bulk upsert multiple records"""
        
        if dry_run:
            self.logger.info(f"🔍 [DRY RUN] Would bulk upsert {len(records)} records")
            return records
        
        if not records:
            return []
        
        try:
            # Set updated timestamps
            for record in records:
                record['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Bulk upsert
            result = (self.client.table(SUPABASE_TABLE)
                     .upsert(records)
                     .execute())
            
            if result.data:
                self.logger.info(f"✅ Bulk upserted {len(result.data)} records")
                return result.data
            else:
                self.logger.warning("⚠️ Bulk upsert returned no data")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Failed to bulk upsert {len(records)} records", error=e)
            raise
    
    def mark_synced(self, record_id: str, notion_page_id: str, dry_run: bool = False) -> bool:
        """Mark a record as synced with Notion"""
        
        if dry_run:
            self.logger.info(f"🔍 [DRY RUN] Would mark record {record_id} as synced")
            return True
        
        try:
            update_data = {
                'notion_page_id': notion_page_id,
                'notion_synced': True,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = (self.client.table(SUPABASE_TABLE)
                     .update(update_data)
                     .eq('id', record_id)
                     .execute())
            
            if result.data:
                self.logger.info(f"✅ Marked record {record_id} as synced")
                return True
            else:
                self.logger.warning(f"⚠️ Failed to mark record {record_id} as synced")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to mark record as synced", error=e, record_id=record_id)
            return False
    
    def find_by_checksum(self, checksum: str) -> Optional[Dict[str, Any]]:
        """Find record by checksum (fallback matching)"""
        
        try:
            result = (self.client.table(SUPABASE_TABLE)
                     .select("*")
                     .eq('checksum', checksum)
                     .limit(1)
                     .execute())
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to find record by checksum", error=e, checksum=checksum)
            return None
    
    def get_table_stats(self) -> Dict[str, int]:
        """Get table statistics"""
        
        try:
            # Total count
            total_result = (self.client.table(SUPABASE_TABLE)
                           .select("id", count="exact")
                           .execute())
            
            # Synced count
            synced_result = (self.client.table(SUPABASE_TABLE)
                            .select("id", count="exact")
                            .eq('notion_synced', True)
                            .execute())
            
            return {
                'total': total_result.count if total_result.count else 0,
                'synced': synced_result.count if synced_result.count else 0,
                'unsynced': (total_result.count or 0) - (synced_result.count or 0)
            }
            
        except Exception as e:
            self.logger.error("❌ Failed to get table stats", error=e)
            return {'total': 0, 'synced': 0, 'unsynced': 0}