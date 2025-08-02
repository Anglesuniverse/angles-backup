"""
Configuration management for GPT Processor
Handles environment variables and application settings
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Application configuration class"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Supabase configuration
        self.SUPABASE_URL = os.getenv("SUPABASE_URL", "")
        self.SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
        self.SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
        
        if not self.SUPABASE_URL or not self.SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be provided")
        
        # Processing configuration
        self.PROCESSING_INTERVAL = int(os.getenv("PROCESSING_INTERVAL", "30"))  # seconds
        self.BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
        self.MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
        self.RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))  # seconds
        
        # Data paths
        self.INPUT_DATA_PATH = os.getenv("INPUT_DATA_PATH", "./data/input")
        self.PROCESSED_DATA_PATH = os.getenv("PROCESSED_DATA_PATH", "./data/processed")
        self.ERROR_DATA_PATH = os.getenv("ERROR_DATA_PATH", "./data/errors")
        
        # Logging configuration
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE = os.getenv("LOG_FILE", "gpt_processor.log")
        
        # Table schemas configuration
        self.TABLE_SCHEMAS_PATH = os.getenv("TABLE_SCHEMAS_PATH", "./config/table_schemas.json")
        
        # Memory system configuration
        self.MEMORY_RETENTION_DAYS = int(os.getenv("MEMORY_RETENTION_DAYS", "30"))
        self.AUTO_CLASSIFY = os.getenv("AUTO_CLASSIFY", "true").lower() == "true"
        
        # Performance settings
        self.MAX_CONCURRENT_OPERATIONS = int(os.getenv("MAX_CONCURRENT_OPERATIONS", "5"))
        self.CONNECTION_TIMEOUT = int(os.getenv("CONNECTION_TIMEOUT", "30"))
        
        # Load table schemas
        self.table_schemas = self._load_table_schemas()
        
        # Create necessary directories
        self._create_directories()
    
    def _load_table_schemas(self) -> Dict[str, Any]:
        """Load table schemas from configuration file"""
        try:
            schema_path = Path(self.TABLE_SCHEMAS_PATH)
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    return json.load(f)
            else:
                # Return default schemas if file doesn't exist
                return self._get_default_schemas()
        except Exception as e:
            print(f"Warning: Failed to load table schemas: {e}")
            return self._get_default_schemas()
    
    def _get_default_schemas(self) -> Dict[str, Any]:
        """Return default table schemas"""
        return {
            "conversations": {
                "description": "Stores conversation history and context",
                "classification_keywords": ["conversation", "chat", "dialogue", "interaction"],
                "fields": ["id", "user_id", "content", "timestamp", "context", "metadata"]
            },
            "memories": {
                "description": "Stores long-term memory and learned information",
                "classification_keywords": ["memory", "remember", "learned", "fact", "knowledge"],
                "fields": ["id", "content", "category", "importance", "timestamp", "tags"]
            },
            "tasks": {
                "description": "Stores tasks and action items",
                "classification_keywords": ["task", "todo", "action", "reminder", "schedule"],
                "fields": ["id", "title", "description", "status", "priority", "due_date", "created_at"]
            },
            "analysis": {
                "description": "Stores analysis results and insights",
                "classification_keywords": ["analysis", "insight", "pattern", "trend", "summary"],
                "fields": ["id", "type", "data", "results", "confidence", "timestamp"]
            }
        }
    
    def _create_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.INPUT_DATA_PATH,
            self.PROCESSED_DATA_PATH,
            self.ERROR_DATA_PATH,
            os.path.dirname(self.TABLE_SCHEMAS_PATH)
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def get_table_schema(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get schema for a specific table"""
        return self.table_schemas.get(table_name)
    
    def get_all_table_names(self) -> list:
        """Get list of all configured table names"""
        return list(self.table_schemas.keys())
