#!/usr/bin/env python3
"""
Diff engine for Supabase-Notion bidirectional sync
Handles checksum computation and record comparison for Angles AI Universe™

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import hashlib
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass

from .logging_util import get_logger


@dataclass
class SyncDelta:
    """Represents sync changes needed"""
    
    # Records to create
    create_in_supabase: List[Dict[str, Any]]
    create_in_notion: List[Dict[str, Any]]
    
    # Records to update
    update_in_supabase: List[Tuple[Dict[str, Any], Dict[str, Any]]]  # (current, new)
    update_in_notion: List[Tuple[Dict[str, Any], Dict[str, Any]]]    # (current, new)
    
    # Statistics
    total_changes: int = 0


class DiffEngine:
    """Engine for computing sync differences between Supabase and Notion"""
    
    def __init__(self):
        """Initialize diff engine"""
        self.logger = get_logger()
    
    def compute_checksum(self, record: Dict[str, Any]) -> str:
        """Compute SHA256 checksum for record normalization"""
        
        # Extract core fields for checksum
        decision = self._normalize_text(record.get('decision', ''))
        type_val = self._normalize_text(record.get('type', ''))
        date_val = self._normalize_date(record.get('date'))
        
        # Create checksum string
        checksum_data = f"{decision}|{type_val}|{date_val}"
        
        # Compute SHA256
        checksum = hashlib.sha256(checksum_data.encode('utf-8')).hexdigest()
        
        self.logger.info(f"🔢 Computed checksum for record", checksum=checksum[:8])
        return checksum
    
    def _normalize_text(self, text: Any) -> str:
        """Normalize text for consistent comparison"""
        if not text:
            return ''
        
        # Convert to string and normalize whitespace
        normalized = str(text).strip()
        normalized = re.sub(r'\s+', ' ', normalized)  # Multiple spaces to single
        normalized = normalized.lower()  # Case insensitive
        
        return normalized
    
    def _normalize_date(self, date_val: Any) -> str:
        """Normalize date to ISO format"""
        if not date_val:
            return ''
        
        date_str = str(date_val)
        
        # Handle various date formats
        if 'T' in date_str:
            # ISO datetime, extract date part
            return date_str.split('T')[0]
        
        # Already in YYYY-MM-DD format
        return date_str
    
    def compute_sync_delta(self, 
                          supabase_records: List[Dict[str, Any]], 
                          notion_records: List[Dict[str, Any]]) -> SyncDelta:
        """Compute sync differences between Supabase and Notion"""
        
        self.logger.info(f"🔍 Computing sync delta: {len(supabase_records)} Supabase, {len(notion_records)} Notion")
        
        # Normalize and index records
        sb_by_id, sb_by_checksum = self._index_supabase_records(supabase_records)
        notion_by_id, notion_by_checksum = self._index_notion_records(notion_records)
        
        # Initialize delta
        delta = SyncDelta(
            create_in_supabase=[],
            create_in_notion=[],
            update_in_supabase=[],
            update_in_notion=[]
        )
        
        # Track processed records
        processed_sb_ids: Set[str] = set()
        processed_notion_ids: Set[str] = set()
        
        # 1. Match by notion_page_id (primary strategy)
        self._match_by_page_id(sb_by_id, notion_by_id, delta, processed_sb_ids, processed_notion_ids)
        
        # 2. Match by checksum (fallback strategy)
        remaining_sb = {k: v for k, v in sb_by_checksum.items() if v['id'] not in processed_sb_ids}
        remaining_notion = {k: v for k, v in notion_by_checksum.items() if v['notion_page_id'] not in processed_notion_ids}
        
        self._match_by_checksum(remaining_sb, remaining_notion, delta, processed_sb_ids, processed_notion_ids)
        
        # 3. Handle unmatched records (creates)
        self._handle_unmatched_records(sb_by_id, notion_by_id, delta, processed_sb_ids, processed_notion_ids)
        
        # Calculate total changes
        delta.total_changes = (len(delta.create_in_supabase) + len(delta.create_in_notion) + 
                              len(delta.update_in_supabase) + len(delta.update_in_notion))
        
        self.logger.info(f"✅ Sync delta computed", 
                        create_sb=len(delta.create_in_supabase),
                        create_notion=len(delta.create_in_notion),
                        update_sb=len(delta.update_in_supabase),
                        update_notion=len(delta.update_in_notion),
                        total=delta.total_changes)
        
        return delta
    
    def _index_supabase_records(self, records: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """Index Supabase records by ID and checksum"""
        
        by_id = {}
        by_checksum = {}
        
        for record in records:
            # Ensure checksum is computed
            if not record.get('checksum'):
                record['checksum'] = self.compute_checksum(record)
            
            # Index by ID
            if record.get('id'):
                by_id[record['id']] = record
            
            # Index by checksum
            by_checksum[record['checksum']] = record
        
        return by_id, by_checksum
    
    def _index_notion_records(self, records: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """Index Notion records by page ID and checksum"""
        
        by_id = {}
        by_checksum = {}
        
        for record in records:
            # Ensure checksum is computed
            if not record.get('checksum'):
                record['checksum'] = self.compute_checksum(record)
            
            # Index by page ID
            if record.get('notion_page_id'):
                by_id[record['notion_page_id']] = record
            
            # Index by checksum
            by_checksum[record['checksum']] = record
        
        return by_id, by_checksum
    
    def _match_by_page_id(self, sb_by_id: Dict[str, Dict[str, Any]], 
                         notion_by_id: Dict[str, Dict[str, Any]],
                         delta: SyncDelta,
                         processed_sb_ids: Set[str],
                         processed_notion_ids: Set[str]):
        """Match records by notion_page_id"""
        
        for sb_record in sb_by_id.values():
            notion_page_id = sb_record.get('notion_page_id')
            if not notion_page_id or notion_page_id in processed_notion_ids:
                continue
            
            notion_record = notion_by_id.get(notion_page_id)
            if not notion_record:
                continue
            
            # Found match, check for updates
            if self._needs_update(sb_record, notion_record):
                winner = self._resolve_conflict(sb_record, notion_record)
                
                if winner == 'supabase':
                    delta.update_in_notion.append((notion_record, sb_record))
                else:
                    delta.update_in_supabase.append((sb_record, notion_record))
            
            # Mark as processed
            processed_sb_ids.add(sb_record['id'])
            processed_notion_ids.add(notion_page_id)
    
    def _match_by_checksum(self, sb_by_checksum: Dict[str, Dict[str, Any]],
                          notion_by_checksum: Dict[str, Dict[str, Any]],
                          delta: SyncDelta,
                          processed_sb_ids: Set[str],
                          processed_notion_ids: Set[str]):
        """Match records by checksum (fallback)"""
        
        for checksum, sb_record in sb_by_checksum.items():
            if sb_record['id'] in processed_sb_ids:
                continue
            
            notion_record = notion_by_checksum.get(checksum)
            if not notion_record or notion_record['notion_page_id'] in processed_notion_ids:
                continue
            
            # Found match by checksum, link them
            # Update Supabase with notion_page_id
            linked_sb_record = sb_record.copy()
            linked_sb_record['notion_page_id'] = notion_record['notion_page_id']
            linked_sb_record['notion_synced'] = True
            
            delta.update_in_supabase.append((sb_record, linked_sb_record))
            
            # Mark as processed
            processed_sb_ids.add(sb_record['id'])
            processed_notion_ids.add(notion_record['notion_page_id'])
    
    def _handle_unmatched_records(self, sb_by_id: Dict[str, Dict[str, Any]],
                                 notion_by_id: Dict[str, Dict[str, Any]],
                                 delta: SyncDelta,
                                 processed_sb_ids: Set[str],
                                 processed_notion_ids: Set[str]):
        """Handle unmatched records (creates)"""
        
        # Supabase records not in Notion (create in Notion)
        for sb_record in sb_by_id.values():
            if sb_record['id'] not in processed_sb_ids:
                delta.create_in_notion.append(sb_record)
        
        # Notion records not in Supabase (create in Supabase)
        for notion_record in notion_by_id.values():
            if notion_record['notion_page_id'] not in processed_notion_ids:
                delta.create_in_supabase.append(notion_record)
    
    def _needs_update(self, sb_record: Dict[str, Any], notion_record: Dict[str, Any]) -> bool:
        """Check if records need updating"""
        
        # Compare checksums
        sb_checksum = sb_record.get('checksum')
        notion_checksum = notion_record.get('checksum')
        
        if not sb_checksum:
            sb_checksum = self.compute_checksum(sb_record)
        if not notion_checksum:
            notion_checksum = self.compute_checksum(notion_record)
        
        return sb_checksum != notion_checksum
    
    def _resolve_conflict(self, sb_record: Dict[str, Any], notion_record: Dict[str, Any]) -> str:
        """Resolve conflict between records (returns 'supabase' or 'notion')"""
        
        # Compare last updated timestamps
        sb_updated = self._parse_timestamp(sb_record.get('updated_at'))
        notion_updated = self._parse_timestamp(notion_record.get('updated_at'))
        
        if sb_updated and notion_updated:
            # Return the more recently updated one
            return 'supabase' if sb_updated > notion_updated else 'notion'
        elif sb_updated:
            return 'supabase'
        elif notion_updated:
            return 'notion'
        else:
            # No timestamps, default to Supabase as source of truth
            return 'supabase'
    
    def _parse_timestamp(self, timestamp: Any) -> Optional[datetime]:
        """Parse timestamp string to datetime"""
        if not timestamp:
            return None
        
        try:
            timestamp_str = str(timestamp)
            
            # Handle ISO format with timezone
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            
            return datetime.fromisoformat(timestamp_str)
        except Exception:
            return None
    
    def validate_record(self, record: Dict[str, Any]) -> bool:
        """Validate record has required fields"""
        
        required_fields = ['decision', 'type', 'date']
        
        for field in required_fields:
            if not record.get(field):
                self.logger.warning(f"⚠️ Record missing required field: {field}")
                return False
        
        return True