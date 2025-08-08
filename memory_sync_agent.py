#!/usr/bin/env python3
"""
Memory Sync Agent for Angles AI Universe™
Syncs unsynced decisions from Supabase decision_vault to Notion database
Marks decisions as synced after successful transfer
Includes rotating logs and sanitized data exports

Author: Angles AI Universe™ Backend Team
Version: 2.0.0
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from pathlib import Path
from logging.handlers import RotatingFileHandler
from supabase import create_client, Client

# Create required directories
Path('logs').mkdir(exist_ok=True)
Path('export').mkdir(exist_ok=True)

# Configure logging with rotating file handler
logger = logging.getLogger('memory_sync')
logger.setLevel(logging.INFO)

# Remove any existing handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Rotating file handler (max 5 files, 1MB each)
file_handler = RotatingFileHandler(
    'logs/memory_sync.log', 
    maxBytes=1024*1024,  # 1MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

class MemorySyncAgent:
    """Agent for syncing decisions from Supabase to Notion"""
    
    def __init__(self):
        """Initialize the sync agent with environment variables"""
        logger.info("Initializing Memory Sync Agent")
        
        # Load environment variables
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
        self.notion_database_id = os.getenv('NOTION_DATABASE_ID')
        self.notion_api_key = os.getenv('NOTION_API_KEY')
        
        # Validate required environment variables
        self._validate_environment()
        
        # Initialize clients
        # Type assertion since we validated env vars above
        self.supabase: Client = create_client(str(self.supabase_url), str(self.supabase_key))
        
        # Notion API headers
        self.notion_headers = {
            "Authorization": f"Bearer {self.notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        logger.info("Memory Sync Agent initialized successfully")
    
    def _validate_environment(self) -> None:
        """Validate that all required environment variables are present"""
        required_vars = {
            'SUPABASE_URL': self.supabase_url,
            'SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY': self.supabase_key,
            'NOTION_DATABASE_ID': self.notion_database_id,
            'NOTION_API_KEY': self.notion_api_key
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("All required environment variables found")
    
    def get_unsynced_decisions(self) -> List[Dict[str, Any]]:
        """Get all unsynced decisions from Supabase"""
        try:
            logger.info("Fetching unsynced decisions from Supabase")
            
            # Get unsynced decisions (notion_synced = false or null)
            try:
                result = self.supabase.table("decision_vault").select("*").or_("notion_synced.is.null,notion_synced.eq.false").execute()
                logger.info("Using notion_synced column for sync tracking")
            except Exception as e:
                if "column" in str(e).lower() and "notion_synced" in str(e).lower():
                    logger.info("notion_synced column doesn't exist, using synced column as fallback")
                    # Fallback to synced column
                    try:
                        result = self.supabase.table("decision_vault").select("*").or_("synced.is.null,synced.eq.false").execute()
                    except Exception as e2:
                        logger.warning("synced column doesn't exist either, fetching all decisions")
                        result = self.supabase.table("decision_vault").select("*").execute()
                else:
                    raise e
            
            decisions = result.data if result.data else []
            logger.info(f"Found {len(decisions)} unsynced decisions")
            return decisions
            
        except Exception as e:
            logger.error(f"Failed to fetch unsynced decisions: {e}")
            raise
    
    def create_notion_page(self, decision: Dict[str, Any]) -> bool:
        """Create a page in Notion for a decision"""
        try:
            # Extract decision data
            decision_id = decision.get('id', '')
            decision_text = decision.get('decision', '')
            decision_type = decision.get('type', 'general')
            decision_date = decision.get('date', date.today().isoformat())
            comment = decision.get('comment', '')
            active = decision.get('active', True)
            
            # Create tags from type and comment
            tags = [decision_type]
            
            if comment and 'Tags:' in comment:
                comment_tags = comment.replace('Tags:', '').strip().split(',')
                tags.extend([tag.strip() for tag in comment_tags if tag.strip()])
            
            # Add active status as tag
            if active:
                tags.append('active')
            else:
                tags.append('inactive')
            
            # Remove duplicates while preserving order
            unique_tags = []
            for tag in tags:
                if tag and tag not in unique_tags:
                    unique_tags.append(tag)
            
            # Prepare tags for Notion multi-select
            tag_objects = [{"name": tag} for tag in unique_tags]
            
            # Prepare Notion page data using correct property names
            page_data = {
                "parent": {"database_id": self.notion_database_id},
                "properties": {
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": decision_text[:100]  # Notion title limit (shorter for titles)
                                }
                            }
                        ]
                    },
                    "Message": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": decision_text[:2000]  # Full message in rich text
                                }
                            }
                        ]
                    },
                    "Date": {
                        "date": {
                            "start": decision_date
                        }
                    },
                    "Tag": {
                        "multi_select": tag_objects
                    }
                }
            }
            
            # Add comment to Message field if it exists
            if comment:
                # Append comment to the Message field
                existing_message = decision_text
                full_message = f"{existing_message}\n\nComment: {comment}"
                page_data["properties"]["Message"]["rich_text"][0]["text"]["content"] = full_message[:2000]
            
            # Send to Notion API with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        "https://api.notion.com/v1/pages",
                        headers=self.notion_headers,
                        json=page_data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"Successfully created Notion page for decision: {decision_text[:50]}...")
                        return True
                    else:
                        logger.error(f"Failed to create Notion page (attempt {attempt + 1}). Status: {response.status_code}")
                        logger.error(f"Response: {response.text}")
                        
                        if attempt == max_retries - 1:
                            return False
                        
                        # Wait before retry (exponential backoff)
                        import time
                        time.sleep(2 ** attempt)
                        
                except requests.RequestException as e:
                    logger.error(f"Request error creating Notion page (attempt {attempt + 1}): {e}")
                    if attempt == max_retries - 1:
                        return False
                    
                    # Wait before retry
                    import time
                    time.sleep(2 ** attempt)
            
            return False
                
        except Exception as e:
            logger.error(f"Error creating Notion page for decision {decision.get('id', 'unknown')}: {e}")
            return False
    
    def mark_as_synced(self, decision_id: str) -> bool:
        """Mark a decision as synced in Supabase"""
        try:
            # Try to mark with notion_synced column first
            try:
                result = self.supabase.table("decision_vault").update(
                    {"notion_synced": True, "notion_synced_at": datetime.utcnow().isoformat()}
                ).eq("id", decision_id).execute()
                logger.debug(f"Marked decision {decision_id} as notion_synced")
            except Exception as e:
                if "column" in str(e).lower() and "notion_synced" in str(e).lower():
                    logger.info(f"notion_synced column doesn't exist, using synced column")
                    # Fallback to synced column
                    result = self.supabase.table("decision_vault").update(
                        {"synced": True, "synced_at": datetime.utcnow().isoformat()}
                    ).eq("id", decision_id).execute()
                else:
                    raise e
            
            if result.data:
                logger.info(f"Marked decision {decision_id} as synced")
                return True
            else:
                logger.warning(f"No rows updated when marking {decision_id} as synced")
                return False
                
        except Exception as e:
            # If both columns don't exist, we can't mark it
            if "column" in str(e).lower() and (("synced" in str(e).lower()) or ("notion_synced" in str(e).lower())):
                logger.warning(f"Cannot mark as synced - sync columns don't exist: {e}")
                return True  # Consider it successful since we can't track it
            else:
                logger.error(f"Error marking decision {decision_id} as synced: {e}")
                return False
    
    def _write_sanitized_export(self, decisions: List[Dict[str, Any]]) -> Optional[str]:
        """Write sanitized export of processed decisions"""
        try:
            if not decisions:
                return None
            
            # Create export filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d")
            export_file = f"export/decisions_{timestamp}.json"
            
            # Prepare export data
            export_data = {
                "export_timestamp": datetime.utcnow().isoformat(),
                "total_decisions": len(decisions),
                "decisions": decisions,
                "metadata": {
                    "export_version": "2.0.0",
                    "source": "memory_sync_agent",
                    "sanitized": True,
                    "contains_secrets": False
                }
            }
            
            # Write to file
            Path(export_file).parent.mkdir(exist_ok=True)
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Sanitized export written to: {export_file}")
            return export_file
            
        except Exception as e:
            logger.error(f"Failed to write sanitized export: {e}")
            return None
    
    def test_connections(self) -> bool:
        """Test connections to both Supabase and Notion"""
        logger.info("Testing connections...")
        
        # Test Supabase connection
        try:
            result = self.supabase.table("decision_vault").select("id").limit(1).execute()
            logger.info("✓ Supabase connection successful")
        except Exception as e:
            logger.error(f"✗ Supabase connection failed: {e}")
            return False
        
        # Test Notion connection
        try:
            response = requests.get(
                f"https://api.notion.com/v1/databases/{self.notion_database_id}",
                headers=self.notion_headers,
                timeout=30
            )
            
            if response.status_code == 200:
                database_info = response.json()
                database_title = database_info.get('title', [{}])[0].get('plain_text', 'Unknown')
                logger.info(f"✓ Notion connection successful - Database: {database_title}")
            else:
                logger.error(f"✗ Notion connection failed. Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Notion connection failed: {e}")
            return False
        
        return True
    
    def sync_all_decisions(self) -> Dict[str, Any]:
        """Main sync function - sync all unsynced decisions"""
        start_time = datetime.utcnow()
        logger.info("Starting memory sync process")
        
        # Store processed decisions for export
        processed_decisions = []
        
        stats = {
            "total_found": 0,
            "successfully_synced": 0,
            "failed_sync": 0,
            "failed_mark": 0,
            "errors": []
        }
        
        try:
            # Test connections first
            if not self.test_connections():
                error_msg = "Connection tests failed"
                logger.error(error_msg)
                return {"success": False, "error": error_msg, "stats": stats}
            
            # Get unsynced decisions
            decisions = self.get_unsynced_decisions()
            stats["total_found"] = len(decisions)
            
            if not decisions:
                logger.info("No unsynced decisions found")
                return {"success": True, "message": "No decisions to sync", "stats": stats}
            
            logger.info(f"Starting sync of {len(decisions)} decisions")
            
            # Sync each decision
            for i, decision in enumerate(decisions, 1):
                decision_id = decision.get('id', 'unknown')
                decision_text = decision.get('decision', '')[:50]
                
                logger.info(f"Processing {i}/{len(decisions)}: {decision_text}...")
                
                # Create Notion page
                if self.create_notion_page(decision):
                    stats["successfully_synced"] += 1
                    
                    # Mark as synced
                    if not self.mark_as_synced(decision_id):
                        stats["failed_mark"] += 1
                        logger.warning(f"Decision synced but failed to mark as synced: {decision_id}")
                    
                    # Add to processed decisions for export (sanitized)
                    sanitized_decision = {
                        "id": decision_id,
                        "decision": decision.get('decision', ''),
                        "type": decision.get('type', ''),
                        "date": decision.get('date', ''),
                        "active": decision.get('active', True),
                        "synced_at": datetime.utcnow().isoformat(),
                        "export_timestamp": datetime.utcnow().isoformat()
                    }
                    # Only add comment if it doesn't contain sensitive information
                    comment = decision.get('comment', '')
                    if comment and not any(keyword in comment.lower() for keyword in ['key', 'token', 'secret', 'password']):
                        sanitized_decision['comment'] = comment
                    
                    processed_decisions.append(sanitized_decision)
                    
                else:
                    stats["failed_sync"] += 1
                    error_msg = f"Failed to sync decision: {decision_text}"
                    stats["errors"].append(error_msg)
                    logger.error(error_msg)
            
            # Write sanitized export if we processed any decisions
            export_file_path = None
            if processed_decisions:
                export_file_path = self._write_sanitized_export(processed_decisions)
            
            # Summary
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 50)
            logger.info("SYNC COMPLETED")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Total found: {stats['total_found']}")
            logger.info(f"Successfully synced: {stats['successfully_synced']}")
            logger.info(f"Failed to sync: {stats['failed_sync']}")
            logger.info(f"Failed to mark: {stats['failed_mark']}")
            if export_file_path:
                logger.info(f"Export file: {export_file_path}")
            logger.info("=" * 50)
            
            success = stats["failed_sync"] == 0
            return {
                "success": success,
                "message": f"Synced {stats['successfully_synced']}/{stats['total_found']} decisions",
                "stats": stats,
                "duration_seconds": duration,
                "export_file": export_file_path
            }
            
        except Exception as e:
            error_msg = f"Sync process failed: {e}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)
            return {"success": False, "error": error_msg, "stats": stats}

def main():
    """Main entry point"""
    try:
        logger.info("Memory Sync Agent started")
        
        # Create and run sync agent
        agent = MemorySyncAgent()
        result = agent.sync_all_decisions()
        
        # Print summary
        if result["success"]:
            logger.info("Memory sync completed successfully")
            print(f"OK: synced {result['stats'].get('successfully_synced', 0)} items")
            if result.get('export_file'):
                print(f"Export file: {result['export_file']}")
            return True
        else:
            logger.error("Memory sync completed with errors")
            print(f"ERROR: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"Memory sync agent failed to start: {e}")
        print(f"FATAL: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)