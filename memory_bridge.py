#!/usr/bin/env python3
"""
Memory Bridge for Angles AI Universe™
Connects Replit with Supabase for persistent AI memory management

This module provides functionality to:
- Fetch unsynced decisions from Supabase
- Send data to Notion (placeholder for future implementation)  
- Mark decisions as synced
- Run the main sync loop

Author: Backend Engineering Team
Version: 1.0.0
"""

import os
import logging
import requests
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging for the memory bridge
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('memory_bridge.log', mode='a')
    ]
)

logger = logging.getLogger('memory_bridge')

class MemoryBridge:
    """
    Main class for the Angles AI Universe™ Memory Bridge
    Handles all operations for syncing decisions between Replit and external services
    """
    
    def __init__(self):
        """Initialize the Memory Bridge with environment configuration"""
        logger.info("Initializing Angles AI Universe™ Memory Bridge")
        
        # Load environment variables
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.notion_api_key = os.getenv('NOTION_API_KEY')
        self.notion_database_id = os.getenv('NOTION_DATABASE_ID')
        
        # Validate required environment variables
        self._validate_environment()
        
        # Initialize Supabase client
        self.supabase: Client = create_client(str(self.supabase_url), str(self.supabase_key))
        
        # Initialize Notion headers (for future implementation)
        self.notion_headers = {
            "Authorization": f"Bearer {self.notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        logger.info("Memory Bridge initialized successfully")
    
    def _validate_environment(self) -> None:
        """
        Validate that all required environment variables are present
        Raises ValueError if any required variables are missing
        """
        required_vars = {
            'SUPABASE_URL': self.supabase_url,
            'SUPABASE_KEY': self.supabase_key,
            'NOTION_API_KEY': self.notion_api_key,
            'NOTION_DATABASE_ID': self.notion_database_id
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("All required environment variables validated")
    
    def fetch_unsynced_decisions(self) -> List[Dict[str, Any]]:
        """
        Fetch decisions from Supabase that haven't been synced yet
        
        Returns:
            List of decision dictionaries that need to be synced
        """
        try:
            logger.info("Fetching unsynced decisions from Supabase")
            
            # Query for decisions where synced = false or synced is null
            result = self.supabase.table("decision_vault").select("*").or_("synced.is.null,synced.eq.false").order("created_at", desc=True).execute()
            
            decisions = result.data if result.data else []
            logger.info(f"Found {len(decisions)} unsynced decisions")
            
            # Log some details about the unsynced decisions
            if decisions:
                logger.info("Unsynced decisions overview:")
                for i, decision in enumerate(decisions[:5], 1):  # Show first 5
                    decision_text = decision.get('decision', '')[:50]
                    decision_type = decision.get('type', 'unknown')
                    logger.info(f"  {i}. [{decision_type}] {decision_text}...")
                
                if len(decisions) > 5:
                    logger.info(f"  ... and {len(decisions) - 5} more decisions")
            
            return decisions
            
        except Exception as e:
            logger.error(f"Failed to fetch unsynced decisions: {e}")
            raise
    
    def send_to_notion(self, decision: Dict[str, Any]) -> bool:
        """
        Send decision data to Notion database
        
        Args:
            decision: Dictionary containing decision data
            
        Returns:
            True if successfully sent to Notion, False otherwise
            
        Note: This is currently a placeholder implementation.
              Full Notion integration will be implemented in future versions.
        """
        try:
            # Extract decision data
            decision_text = decision.get('decision', '')
            decision_type = decision.get('type', 'general')
            decision_date = decision.get('date', date.today().isoformat())
            decision_comment = decision.get('comment', '')
            decision_active = decision.get('active', True)
            
            # Create tags from type and status
            tags = [decision_type]
            if decision_active:
                tags.append('active')
            else:
                tags.append('inactive')
            
            # Prepare Notion page data
            page_data = {
                "parent": {"database_id": self.notion_database_id},
                "properties": {
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": decision_text[:100]  # Notion title limit
                                }
                            }
                        ]
                    },
                    "Message": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": f"{decision_text}\n\nComment: {decision_comment}" if decision_comment else decision_text
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
                        "multi_select": [{"name": tag} for tag in tags]
                    }
                }
            }
            
            # Send to Notion API
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=self.notion_headers,
                json=page_data,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully sent decision to Notion: {decision_text[:50]}...")
                return True
            else:
                logger.error(f"Failed to send to Notion. Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending decision to Notion: {e}")
            return False
    
    def mark_as_synced(self, decision_id: str) -> bool:
        """
        Mark a decision as synced in the Supabase database
        
        Args:
            decision_id: UUID string of the decision to mark as synced
            
        Returns:
            True if successfully marked as synced, False otherwise
        """
        try:
            logger.info(f"Marking decision {decision_id} as synced")
            
            # Update the decision record with synced=true and synced_at timestamp
            result = self.supabase.table("decision_vault").update({
                "synced": True,
                "synced_at": datetime.utcnow().isoformat()
            }).eq("id", decision_id).execute()
            
            if result.data:
                logger.info(f"Successfully marked decision {decision_id} as synced")
                return True
            else:
                logger.warning(f"No rows updated when marking {decision_id} as synced")
                return False
                
        except Exception as e:
            logger.error(f"Failed to mark decision {decision_id} as synced: {e}")
            return False
    
    def sync(self) -> Dict[str, Any]:
        """
        Main sync function - orchestrates the entire memory bridge process
        
        Returns:
            Dictionary containing sync results and statistics
        """
        start_time = datetime.utcnow()
        logger.info("="*60)
        logger.info("ANGLES AI UNIVERSE™ MEMORY BRIDGE - SYNC START")
        logger.info("="*60)
        
        # Initialize statistics
        stats = {
            "total_found": 0,
            "successfully_synced": 0,
            "failed_sync": 0,
            "failed_mark": 0,
            "errors": []
        }
        
        try:
            # Step 1: Test Supabase connection
            logger.info("Testing Supabase connection...")
            test_result = self.supabase.table("decision_vault").select("id").limit(1).execute()
            logger.info("✓ Supabase connection successful")
            
            # Step 2: Fetch unsynced decisions
            decisions = self.fetch_unsynced_decisions()
            stats["total_found"] = len(decisions)
            
            if not decisions:
                logger.info("No unsynced decisions found - memory bridge is up to date")
                return {
                    "success": True, 
                    "message": "No decisions to sync", 
                    "stats": stats,
                    "duration_seconds": (datetime.utcnow() - start_time).total_seconds()
                }
            
            # Step 3: Process each decision
            logger.info(f"Processing {len(decisions)} unsynced decisions...")
            
            for i, decision in enumerate(decisions, 1):
                decision_id = decision.get('id', 'unknown')
                decision_text = decision.get('decision', '')[:50]
                
                logger.info(f"[{i}/{len(decisions)}] Processing: {decision_text}...")
                
                # Send to Notion (if enabled)
                notion_success = self.send_to_notion(decision)
                
                if notion_success:
                    stats["successfully_synced"] += 1
                    
                    # Mark as synced in Supabase
                    if not self.mark_as_synced(decision_id):
                        stats["failed_mark"] += 1
                        logger.warning(f"Decision synced but failed to mark as synced: {decision_id}")
                else:
                    stats["failed_sync"] += 1
                    error_msg = f"Failed to sync decision: {decision_text}"
                    stats["errors"].append(error_msg)
                    logger.error(error_msg)
            
            # Step 4: Generate summary
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("="*60)
            logger.info("MEMORY BRIDGE SYNC COMPLETED")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Total found: {stats['total_found']}")
            logger.info(f"Successfully synced: {stats['successfully_synced']}")
            logger.info(f"Failed to sync: {stats['failed_sync']}")
            logger.info(f"Failed to mark: {stats['failed_mark']}")
            logger.info("="*60)
            
            # Determine overall success
            success = stats["failed_sync"] == 0
            
            return {
                "success": success,
                "message": f"Synced {stats['successfully_synced']}/{stats['total_found']} decisions",
                "stats": stats,
                "duration_seconds": duration
            }
            
        except Exception as e:
            error_msg = f"Memory bridge sync failed: {e}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "stats": stats,
                "duration_seconds": (datetime.utcnow() - start_time).total_seconds()
            }

def main():
    """
    Main entry point for the memory bridge
    Can be run manually or scheduled for automated syncing
    """
    try:
        logger.info("Starting Angles AI Universe™ Memory Bridge")
        
        # Create memory bridge instance
        bridge = MemoryBridge()
        
        # Run sync process
        result = bridge.sync()
        
        # Log final result
        if result["success"]:
            logger.info(f"Memory bridge completed successfully: {result['message']}")
            exit_code = 0
        else:
            logger.error(f"Memory bridge completed with errors: {result.get('error', 'Unknown error')}")
            exit_code = 1
        
        # Exit with appropriate code for scheduling systems
        exit(exit_code)
        
    except Exception as e:
        logger.error(f"Memory bridge failed to start: {e}")
        exit(1)

if __name__ == "__main__":
    main()