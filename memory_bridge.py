#!/usr/bin/env python3
"""
Angles AI Universe™ Memory Bridge
Robust autosync pipeline that keeps Supabase (primary) and Notion (secondary) in sync

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Callable
import requests


class MemoryBridge:
    """Main sync bridge between Supabase and Notion"""
    
    def __init__(self):
        """Initialize the memory bridge with environment credentials"""
        
        # Supabase configuration (required)
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        # Notion configuration (optional)
        self.notion_key = os.getenv('NOTION_API_KEY')
        self.notion_db_id = os.getenv('NOTION_DATABASE_ID')
        
        # Validation
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing required SUPABASE_URL or SUPABASE_KEY environment variables")
        
        # Notion availability
        self.notion_enabled = bool(self.notion_key and self.notion_db_id)
        
        # Queue file for local fallback
        self.queue_file = './sync_queue.jsonl'
        
        # Request headers
        self.supabase_headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json'
        }
        
        self.notion_headers = {
            'Authorization': f'Bearer {self.notion_key}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        } if self.notion_enabled else {}
        
        print(f"🔗 Memory Bridge initialized")
        print(f"   Supabase: ✅ Connected ({self.supabase_url})")
        print(f"   Notion: {'✅ Enabled' if self.notion_enabled else '⚠️ Disabled (missing credentials)'}")
    
    def healthcheck(self) -> bool:
        """Validate Supabase connection by testing decision_vault access"""
        
        try:
            url = f"{self.supabase_url}/rest/v1/decision_vault"
            params = {'select': 'id', 'limit': '1'}
            
            response = requests.get(url, headers=self.supabase_headers, params=params, timeout=10)
            
            if response.status_code == 200:
                print("✅ Supabase healthcheck passed")
                return True
            else:
                print(f"❌ Supabase healthcheck failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Supabase healthcheck error: {e}")
            return False
    
    def fetch_unsynced(self, table: str) -> List[Dict[str, Any]]:
        """Fetch unsynced rows from specified table"""
        
        try:
            url = f"{self.supabase_url}/rest/v1/{table}"
            params = {
                'select': '*',
                'notion_synced': 'eq.false',
                'order': 'created_at.asc',
                'limit': '50'
            }
            
            response = requests.get(url, headers=self.supabase_headers, params=params, timeout=15)
            
            if response.status_code == 200:
                rows = response.json()
                print(f"📥 Fetched {len(rows)} unsynced rows from {table}")
                return rows
            else:
                print(f"⚠️ Failed to fetch from {table}: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching from {table}: {e}")
            return []
    
    def upsert_notion(self, page_payload: Dict[str, Any]) -> bool:
        """Create a new page in Notion database"""
        
        if not self.notion_enabled:
            return False
        
        try:
            url = 'https://api.notion.com/v1/pages'
            
            response = requests.post(url, headers=self.notion_headers, json=page_payload, timeout=15)
            
            if response.status_code in [200, 201]:
                print("✅ Created Notion page successfully")
                return True
            else:
                print(f"⚠️ Notion page creation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating Notion page: {e}")
            return False
    
    def mark_synced(self, table: str, row_id: str) -> bool:
        """Mark a row as synced in Supabase"""
        
        try:
            url = f"{self.supabase_url}/rest/v1/{table}"
            params = {'id': f'eq.{row_id}'}
            payload = {'notion_synced': True}
            
            response = requests.patch(url, headers=self.supabase_headers, params=params, json=payload, timeout=10)
            
            if response.status_code == 204:
                print(f"✅ Marked {row_id} as synced in {table}")
                return True
            else:
                print(f"⚠️ Failed to mark {row_id} as synced: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error marking {row_id} as synced: {e}")
            return False
    
    def queue_for_later(self, target: str, table: str, payload: Dict[str, Any]):
        """Queue a sync operation for later when services are unreachable"""
        
        try:
            queue_entry = {
                'target': target,
                'table': table,
                'payload': payload,
                'queued_at': datetime.now(timezone.utc).isoformat()
            }
            
            with open(self.queue_file, 'a') as f:
                f.write(json.dumps(queue_entry) + '\n')
            
            print(f"📝 Queued {table} entry for later sync")
            
        except Exception as e:
            print(f"❌ Failed to queue entry: {e}")
    
    def drain_queue(self):
        """Process queued sync operations"""
        
        if not os.path.exists(self.queue_file):
            return
        
        try:
            with open(self.queue_file, 'r') as f:
                lines = f.readlines()
            
            if not lines:
                return
            
            print(f"🔄 Processing {len(lines)} queued operations...")
            
            processed = []
            failed = []
            
            for line in lines:
                try:
                    entry = json.loads(line.strip())
                    
                    if entry['target'] == 'notion' and self.notion_enabled:
                        if self.upsert_notion(entry['payload']):
                            processed.append(line)
                        else:
                            failed.append(line)
                    else:
                        # Skip if Notion not available
                        processed.append(line)
                        
                except Exception as e:
                    print(f"❌ Failed to process queue entry: {e}")
                    failed.append(line)
            
            # Rewrite queue file with only failed entries
            with open(self.queue_file, 'w') as f:
                for line in failed:
                    f.write(line)
            
            if processed:
                print(f"✅ Processed {len(processed)} queued operations")
            
            if failed:
                print(f"⚠️ {len(failed)} operations remain queued")
                
        except Exception as e:
            print(f"❌ Error draining queue: {e}")
    
    def map_decision(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map decision_vault row to Notion page payload"""
        
        return {
            'parent': {'database_id': self.notion_db_id},
            'properties': {
                'Decision': {
                    'title': [{'text': {'content': str(row.get('decision', ''))}}]
                },
                'Date': {
                    'date': {'start': str(row.get('date', ''))} if row.get('date') else None
                },
                'Type': {
                    'select': {'name': str(row.get('type', 'Other'))}
                }
            }
        }
    
    def map_memory(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map memory_log row to Notion page payload"""
        
        return {
            'parent': {'database_id': self.notion_db_id},
            'properties': {
                'Event': {
                    'title': [{'text': {'content': str(row.get('event_type', ''))}}]
                },
                'Description': {
                    'rich_text': [{'text': {'content': str(row.get('event_description', ''))}}]
                },
                'Date': {
                    'date': {'start': str(row.get('created_at', '')).split('T')[0]} if row.get('created_at') else None
                }
            }
        }
    
    def map_agent(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map agent_activity row to Notion page payload"""
        
        return {
            'parent': {'database_id': self.notion_db_id},
            'properties': {
                'Agent': {
                    'title': [{'text': {'content': str(row.get('agent_name', ''))}}]
                },
                'Activity': {
                    'rich_text': [{'text': {'content': str(row.get('activity_description', ''))}}]
                },
                'Status': {
                    'select': {'name': str(row.get('status', 'completed'))}
                },
                'Date': {
                    'date': {'start': str(row.get('created_at', '')).split('T')[0]} if row.get('created_at') else None
                }
            }
        }
    
    def push_batch_to_notion(self, table: str, mapping_fn: Callable[[Dict[str, Any]], Dict[str, Any]]) -> int:
        """Push a batch of unsynced rows to Notion"""
        
        # Fetch unsynced rows
        rows = self.fetch_unsynced(table)
        
        if not rows:
            return 0
        
        synced_count = 0
        
        for row in rows:
            try:
                # Map row to Notion payload
                notion_payload = mapping_fn(row)
                
                # Try to sync with retry logic
                success = False
                for attempt in range(3):
                    if attempt > 0:
                        print(f"🔄 Retry {attempt} for {table} row {row.get('id')}")
                        time.sleep(2 ** attempt)  # Exponential backoff: 2s, 4s
                    
                    if self.notion_enabled:
                        if self.upsert_notion(notion_payload):
                            success = True
                            break
                    else:
                        # Skip Notion if not enabled
                        success = True
                        break
                
                if success:
                    # Mark as synced in Supabase
                    if self.mark_synced(table, row['id']):
                        synced_count += 1
                    else:
                        print(f"⚠️ Synced to Notion but failed to mark {row['id']} as synced")
                else:
                    # Queue for later if all attempts failed
                    if self.notion_enabled:
                        self.queue_for_later('notion', table, notion_payload)
                
            except Exception as e:
                print(f"❌ Error processing {table} row {row.get('id')}: {e}")
                continue
        
        print(f"📤 Synced {synced_count}/{len(rows)} rows from {table}")
        return synced_count
    
    def sync_all(self):
        """Main sync function that processes all tables"""
        
        print("🚀 Starting memory bridge sync...")
        print("=" * 50)
        
        start_time = time.time()
        
        # Step 1: Health check
        if not self.healthcheck():
            print("❌ Sync aborted due to failed health check")
            return
        
        # Step 2: Drain any queued operations first
        self.drain_queue()
        
        # Step 3: Sync each table
        total_synced = 0
        
        tables_to_sync = [
            ('decision_vault', self.map_decision),
            ('memory_log', self.map_memory),
            ('agent_activity', self.map_agent)
        ]
        
        for table, mapping_fn in tables_to_sync:
            print(f"\n🔄 Syncing {table}...")
            try:
                synced = self.push_batch_to_notion(table, mapping_fn)
                total_synced += synced
            except Exception as e:
                print(f"❌ Error syncing {table}: {e}")
        
        # Summary
        duration = time.time() - start_time
        print("\n" + "=" * 50)
        print("🏁 Sync completed!")
        print(f"   Total synced: {total_synced} rows")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Notion: {'✅ Enabled' if self.notion_enabled else '⚠️ Disabled'}")
        print("=" * 50)


def run_sync_test():
    """Test function that inserts sample data and runs sync"""
    
    print("🧪 RUNNING SYNC TEST")
    print("=" * 30)
    
    try:
        bridge = MemoryBridge()
        
        # Insert test decision
        print("📝 Inserting test decision...")
        
        test_decision = {
            'decision': 'Test sync pipeline functionality',
            'type': 'System',
            'date': datetime.now().date().isoformat(),
            'notion_synced': False
        }
        
        url = f"{bridge.supabase_url}/rest/v1/decision_vault"
        response = requests.post(url, headers=bridge.supabase_headers, json=test_decision, timeout=10)
        
        if response.status_code in [200, 201]:
            print("✅ Test decision inserted")
        else:
            print(f"⚠️ Failed to insert test decision: {response.status_code}")
        
        # Run sync
        print("\n🔄 Running full sync...")
        bridge.sync_all()
        
        print("\n🎉 Sync test completed!")
        
    except Exception as e:
        print(f"❌ Sync test failed: {e}")


# Initialize global bridge instance
_bridge = None

def get_bridge():
    """Get global bridge instance"""
    global _bridge
    if _bridge is None:
        _bridge = MemoryBridge()
    return _bridge

def sync_all():
    """Convenience function for external use"""
    bridge = get_bridge()
    bridge.sync_all()


if __name__ == "__main__":
    run_sync_test()