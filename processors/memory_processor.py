"""
Main memory processor that orchestrates the GPT output processing workflow
Coordinates parsing, classification, validation, and storage operations
"""

import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from database.supabase_client import SupabaseClient
from database.operations import DatabaseOperations
from parsers.gpt_parser import GPTParser
from parsers.data_classifier import DataClassifier
from validators.schemas import validate_data
from utils.logger import setup_logger, OperationLogger, PerformanceMonitor
from utils.retry import execute_with_retry_manager, DATABASE_RETRY_MANAGER


class MemoryProcessor:
    """Main processor for GPT outputs and memory management"""
    
    def __init__(self, config, supabase_client: SupabaseClient):
        self.config = config
        self.supabase_client = supabase_client
        self.logger = setup_logger(__name__, config.LOG_LEVEL)
        
        # Initialize components
        self.gpt_parser = GPTParser(config)
        self.data_classifier = DataClassifier(config)
        self.db_operations = DatabaseOperations(config, supabase_client)
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor(self.logger)
        
        # Processing statistics
        self.stats = {
            "processed_count": 0,
            "success_count": 0,
            "error_count": 0,
            "classification_accuracy": 0.0,
            "last_processed": None
        }
        
        # Processing queue
        self.processing_queue = asyncio.Queue()
        self.is_processing = False
    
    async def initialize(self):
        """Initialize the memory processor"""
        try:
            self.logger.info("Initializing Memory Processor...")
            
            # Create necessary directories
            self._ensure_directories()
            
            # Load any pending inputs
            await self._load_pending_inputs()
            
            self.logger.info("Memory Processor initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Memory Processor: {str(e)}")
            raise
    
    def _ensure_directories(self):
        """Ensure all necessary directories exist"""
        directories = [
            self.config.INPUT_DATA_PATH,
            self.config.PROCESSED_DATA_PATH,
            self.config.ERROR_DATA_PATH
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    async def _load_pending_inputs(self):
        """Load any pending input files for processing"""
        try:
            input_path = Path(self.config.INPUT_DATA_PATH)
            if not input_path.exists():
                return
            
            # Look for JSON and text files
            file_patterns = ["*.json", "*.txt"]
            pending_files = []
            
            for pattern in file_patterns:
                pending_files.extend(input_path.glob(pattern))
            
            if pending_files:
                self.logger.info(f"Found {len(pending_files)} pending input files")
                
                for file_path in pending_files:
                    await self.processing_queue.put({
                        "type": "file",
                        "path": str(file_path),
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
        except Exception as e:
            self.logger.error(f"Failed to load pending inputs: {str(e)}")
    
    async def process_pending_outputs(self):
        """Process all pending GPT outputs"""
        if self.is_processing:
            self.logger.debug("Processing already in progress, skipping")
            return
        
        self.is_processing = True
        
        try:
            with OperationLogger(self.logger, "process_pending_outputs"):
                # Check for new input files
                await self._load_pending_inputs()
                
                # Process items from queue
                processed_count = 0
                
                while not self.processing_queue.empty() and processed_count < self.config.BATCH_SIZE:
                    try:
                        item = await asyncio.wait_for(self.processing_queue.get(), timeout=1.0)
                        await self._process_single_item(item)
                        processed_count += 1
                        
                    except asyncio.TimeoutError:
                        break
                    except Exception as e:
                        self.logger.error(f"Failed to process queue item: {str(e)}")
                        self.stats["error_count"] += 1
                
                if processed_count > 0:
                    self.logger.info(f"Processed {processed_count} items in this batch")
                    
                    # Log performance statistics periodically
                    if self.stats["processed_count"] % 50 == 0:
                        self.performance_monitor.log_statistics()
                
        finally:
            self.is_processing = False
    
    async def _process_single_item(self, item: Dict[str, Any]):
        """Process a single input item"""
        start_time = datetime.utcnow()
        
        try:
            self.logger.debug(f"Processing item: {item}")
            
            # Read the content
            content = await self._read_item_content(item)
            if not content:
                self.logger.warning(f"No content found for item: {item}")
                return
            
            # Parse the GPT output
            parsed_data = self.gpt_parser.parse_output(content)
            
            # Classify the data to determine table routing
            table_name, confidence = self.data_classifier.classify_data(parsed_data)
            
            # Skip processing if confidence is too low
            if confidence < 0.3:
                self.logger.warning(f"Classification confidence too low ({confidence:.2f}), skipping")
                await self._move_to_error(item, f"Low classification confidence: {confidence:.2f}")
                return
            
            # Store the data
            await self._store_classified_data(parsed_data, table_name, item)
            
            # Update statistics
            self.stats["processed_count"] += 1
            self.stats["success_count"] += 1
            self.stats["last_processed"] = datetime.utcnow().isoformat()
            
            # Move processed file
            await self._move_to_processed(item)
            
            # Record performance
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.performance_monitor.record_operation("process_single_item", duration)
            
            self.logger.info(f"Successfully processed item into {table_name} table (confidence: {confidence:.2f})")
            
        except Exception as e:
            self.logger.error(f"Failed to process item {item}: {str(e)}")
            self.stats["error_count"] += 1
            await self._move_to_error(item, str(e))
    
    async def _read_item_content(self, item: Dict[str, Any]) -> Optional[str]:
        """Read content from an input item"""
        try:
            if item["type"] == "file":
                file_path = Path(item["path"])
                if file_path.exists():
                    return file_path.read_text(encoding='utf-8')
            elif item["type"] == "content":
                return item.get("content")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to read item content: {str(e)}")
            return None
    
    async def _store_classified_data(self, parsed_data: Dict[str, Any], table_name: str, source_item: Dict[str, Any]):
        """Store classified data in the appropriate table"""
        try:
            # Extract the actual data for storage
            data = parsed_data.get("parsed_data", {})
            
            # Add metadata about the processing
            processing_metadata = {
                "source_type": source_item["type"],
                "processed_at": datetime.utcnow().isoformat(),
                "classification_confidence": 0.0,  # Will be updated by classifier
                "parsing_method": parsed_data.get("metadata", {}).get("parsing_method", "unknown")
            }
            
            # Store using appropriate method based on table type
            if table_name == "conversations":
                await self._store_conversation_data(data, processing_metadata)
            elif table_name == "memories":
                await self._store_memory_data(data, processing_metadata)
            elif table_name == "tasks":
                await self._store_task_data(data, processing_metadata)
            elif table_name == "analysis":
                await self._store_analysis_data(data, processing_metadata)
            else:
                # Generic storage for unknown table types
                await self._store_generic_data(data, table_name, processing_metadata)
                
        except Exception as e:
            self.logger.error(f"Failed to store classified data: {str(e)}")
            raise
    
    async def _store_conversation_data(self, data: Dict[str, Any], metadata: Dict[str, Any]):
        """Store conversation data"""
        # Extract or generate required fields
        user_id = data.get("user_id", "system")
        content = data.get("content") or data.get("text") or str(data)
        context = data.get("context", metadata)
        
        await execute_with_retry_manager(
            DATABASE_RETRY_MANAGER,
            self.db_operations.store_conversation,
            user_id, content, context
        )
    
    async def _store_memory_data(self, data: Dict[str, Any], metadata: Dict[str, Any]):
        """Store memory data"""
        content = data.get("content") or data.get("text") or str(data)
        category = data.get("category", "general")
        importance = int(data.get("importance", 5))
        tags = data.get("tags", [])
        
        await execute_with_retry_manager(
            DATABASE_RETRY_MANAGER,
            self.db_operations.store_memory,
            content, category, importance, tags
        )
    
    async def _store_task_data(self, data: Dict[str, Any], metadata: Dict[str, Any]):
        """Store task data"""
        title = data.get("title") or data.get("name") or "Untitled Task"
        description = data.get("description") or data.get("content") or str(data)
        priority = data.get("priority", "medium")
        due_date = data.get("due_date")
        
        await execute_with_retry_manager(
            DATABASE_RETRY_MANAGER,
            self.db_operations.store_task,
            title, description, priority, due_date
        )
    
    async def _store_analysis_data(self, data: Dict[str, Any], metadata: Dict[str, Any]):
        """Store analysis data"""
        analysis_type = data.get("type", "general")
        input_data = data.get("data", data)
        results = data.get("results", {})
        confidence = float(data.get("confidence", 0.5))
        
        await execute_with_retry_manager(
            DATABASE_RETRY_MANAGER,
            self.db_operations.store_analysis,
            analysis_type, input_data, results, confidence
        )
    
    async def _store_generic_data(self, data: Dict[str, Any], table_name: str, metadata: Dict[str, Any]):
        """Store data in a generic table"""
        # Add processing metadata
        data_with_metadata = {**data, **metadata}
        
        # Validate the data
        validated_data = validate_data(data_with_metadata, table_name, self.config)
        
        # Store using direct client
        await execute_with_retry_manager(
            DATABASE_RETRY_MANAGER,
            self.supabase_client.insert_data,
            table_name, validated_data
        )
    
    async def _move_to_processed(self, item: Dict[str, Any]):
        """Move processed file to processed directory"""
        try:
            if item["type"] == "file":
                source_path = Path(item["path"])
                if source_path.exists():
                    dest_path = Path(self.config.PROCESSED_DATA_PATH) / source_path.name
                    source_path.rename(dest_path)
                    self.logger.debug(f"Moved processed file to {dest_path}")
                    
        except Exception as e:
            self.logger.warning(f"Failed to move processed file: {str(e)}")
    
    async def _move_to_error(self, item: Dict[str, Any], error_msg: str):
        """Move failed file to error directory with error info"""
        try:
            if item["type"] == "file":
                source_path = Path(item["path"])
                if source_path.exists():
                    dest_path = Path(self.config.ERROR_DATA_PATH) / source_path.name
                    source_path.rename(dest_path)
                    
                    # Create error info file
                    error_info = {
                        "original_file": source_path.name,
                        "error": error_msg,
                        "timestamp": datetime.utcnow().isoformat(),
                        "item": item
                    }
                    
                    error_info_path = dest_path.with_suffix(dest_path.suffix + ".error")
                    error_info_path.write_text(json.dumps(error_info, indent=2))
                    
                    self.logger.debug(f"Moved error file to {dest_path}")
                    
        except Exception as e:
            self.logger.warning(f"Failed to move error file: {str(e)}")
    
    async def add_direct_input(self, content: str, content_type: Optional[str] = None):
        """Add content directly to processing queue"""
        try:
            await self.processing_queue.put({
                "type": "content",
                "content": content,
                "content_type": content_type,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            self.logger.info("Added direct input to processing queue")
            
        except Exception as e:
            self.logger.error(f"Failed to add direct input: {str(e)}")
            raise
    
    async def get_context_for_user(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get relevant context for a user"""
        try:
            # Get recent conversations
            conversations = await self.db_operations.get_recent_conversations(user_id, limit)
            
            # Get relevant memories (based on recent conversation topics)
            topics = []
            for conv in conversations[:3]:  # Use last 3 conversations for topics
                content = conv.get("content", "")
                # Simple topic extraction - could be enhanced
                words = content.lower().split()
                topics.extend([word for word in words if len(word) > 4])
            
            memories = await self.db_operations.get_relevant_memories(topics[:10], 5)
            
            return {
                "user_id": user_id,
                "recent_conversations": conversations,
                "relevant_memories": memories,
                "context_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get context for user {user_id}: {str(e)}")
            return {"user_id": user_id, "error": str(e)}
    
    async def cleanup_old_data(self):
        """Clean up old data based on retention policy"""
        try:
            with OperationLogger(self.logger, "cleanup_old_data"):
                results = await self.db_operations.cleanup_old_data()
                self.logger.info(f"Cleanup completed: {results}")
                return results
                
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")
            return {}
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        performance_stats = self.performance_monitor.get_statistics()
        
        return {
            **self.stats,
            "performance": performance_stats,
            "queue_size": self.processing_queue.qsize(),
            "is_processing": self.is_processing
        }
    
    async def shutdown(self):
        """Graceful shutdown of the processor"""
        try:
            self.logger.info("Shutting down Memory Processor...")
            
            # Wait for current processing to complete
            while self.is_processing:
                await asyncio.sleep(0.1)
            
            # Log final statistics
            self.performance_monitor.log_statistics()
            
            final_stats = self.get_processing_statistics()
            self.logger.info(f"Final processing statistics: {final_stats}")
            
            self.logger.info("Memory Processor shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}")
