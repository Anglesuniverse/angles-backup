"""
High-level database operations for memory management
Provides specialized operations for different data types
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from database.supabase_client import SupabaseClient
from utils.logger import setup_logger
from validators.schemas import validate_data


class DatabaseOperations:
    """High-level database operations manager"""
    
    def __init__(self, config, supabase_client: SupabaseClient):
        self.config = config
        self.client = supabase_client
        self.logger = setup_logger(__name__, config.LOG_LEVEL)
    
    async def store_conversation(self, user_id: str, content: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Store conversation data"""
        try:
            data = {
                "user_id": user_id,
                "content": content,
                "context": json.dumps(context) if context else None,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {"source": "gpt_processor", "type": "conversation"}
            }
            
            # Validate data
            validated_data = validate_data(data, "conversations", self.config)
            
            result = await self.client.insert_data("conversations", validated_data)
            self.logger.info(f"Stored conversation for user {user_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to store conversation: {str(e)}")
            raise
    
    async def store_memory(self, content: str, category: str, importance: int = 5, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Store memory/knowledge data"""
        try:
            data = {
                "content": content,
                "category": category,
                "importance": importance,
                "tags": json.dumps(tags) if tags else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Validate data
            validated_data = validate_data(data, "memories", self.config)
            
            result = await self.client.insert_data("memories", validated_data)
            self.logger.info(f"Stored memory in category '{category}'")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to store memory: {str(e)}")
            raise
    
    async def store_task(self, title: str, description: str, priority: str = "medium", 
                        due_date: Optional[str] = None) -> Dict[str, Any]:
        """Store task data"""
        try:
            data = {
                "title": title,
                "description": description,
                "status": "pending",
                "priority": priority,
                "due_date": due_date,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Validate data
            validated_data = validate_data(data, "tasks", self.config)
            
            result = await self.client.insert_data("tasks", validated_data)
            self.logger.info(f"Stored task: {title}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to store task: {str(e)}")
            raise
    
    async def store_analysis(self, analysis_type: str, data_input: Dict[str, Any], 
                           results: Dict[str, Any], confidence: float = 0.5) -> Dict[str, Any]:
        """Store analysis results"""
        try:
            data = {
                "type": analysis_type,
                "data": json.dumps(data_input),
                "results": json.dumps(results),
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Validate data
            validated_data = validate_data(data, "analysis", self.config)
            
            result = await self.client.insert_data("analysis", validated_data)
            self.logger.info(f"Stored analysis of type '{analysis_type}'")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to store analysis: {str(e)}")
            raise
    
    async def get_recent_conversations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations for context"""
        try:
            filters = {"user_id": user_id}
            conversations = await self.client.query_data(
                "conversations", 
                filters=filters, 
                limit=limit, 
                order_by="timestamp.desc"
            )
            
            self.logger.debug(f"Retrieved {len(conversations)} recent conversations for user {user_id}")
            return conversations
            
        except Exception as e:
            self.logger.error(f"Failed to get recent conversations: {str(e)}")
            return []
    
    async def get_relevant_memories(self, keywords: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """Get memories relevant to keywords"""
        try:
            # This is a simplified implementation - in practice you might want
            # to use full-text search or vector similarity
            memories = await self.client.query_data("memories", limit=limit * 2)
            
            # Filter memories based on keyword relevance
            relevant_memories = []
            for memory in memories:
                content = memory.get("content", "").lower()
                tags = json.loads(memory.get("tags", "[]")) if memory.get("tags") else []
                
                # Check if any keyword appears in content or tags
                for keyword in keywords:
                    if keyword.lower() in content or keyword.lower() in [tag.lower() for tag in tags]:
                        relevant_memories.append(memory)
                        break
                
                if len(relevant_memories) >= limit:
                    break
            
            self.logger.debug(f"Retrieved {len(relevant_memories)} relevant memories")
            return relevant_memories
            
        except Exception as e:
            self.logger.error(f"Failed to get relevant memories: {str(e)}")
            return []
    
    async def cleanup_old_data(self) -> Dict[str, int]:
        """Clean up old data based on retention policy"""
        cleanup_results = {}
        cutoff_date = (datetime.utcnow() - timedelta(days=self.config.MEMORY_RETENTION_DAYS)).isoformat()
        
        try:
            # Clean up old conversations (keep memories and tasks longer)
            deleted_conversations = await self.client.delete_data(
                "conversations",
                {"timestamp": f"lt.{cutoff_date}"}
            )
            cleanup_results["conversations"] = deleted_conversations
            
            # Clean up old analysis data
            deleted_analysis = await self.client.delete_data(
                "analysis",
                {"timestamp": f"lt.{cutoff_date}"}
            )
            cleanup_results["analysis"] = deleted_analysis
            
            self.logger.info(f"Cleanup completed: {cleanup_results}")
            return cleanup_results
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {str(e)}")
            return cleanup_results
    
    async def get_data_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored data"""
        stats = {}
        
        try:
            for table_name in self.config.get_all_table_names():
                try:
                    data = await self.client.query_data(table_name, limit=1000)  # Sample for stats
                    stats[table_name] = {
                        "count": len(data),
                        "latest_timestamp": max([item.get("timestamp", "") for item in data]) if data else None
                    }
                except Exception as e:
                    self.logger.warning(f"Failed to get stats for table {table_name}: {str(e)}")
                    stats[table_name] = {"count": 0, "latest_timestamp": None}
            
            self.logger.debug(f"Data statistics: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get data statistics: {str(e)}")
            return {}
