"""
Data validation schemas using Pydantic
Ensures data integrity before database operations
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, validator, Field
import json

from utils.logger import setup_logger


class ConversationSchema(BaseModel):
    """Schema for conversation data"""
    user_id: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=10000)
    context: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Optional[str] = None
    
    @validator('context', 'metadata')
    def validate_json_fields(cls, v):
        if v is not None and isinstance(v, dict):
            return json.dumps(v)
        return v
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            return datetime.utcnow().isoformat()


class MemorySchema(BaseModel):
    """Schema for memory/knowledge data"""
    content: str = Field(..., min_length=1, max_length=10000)
    category: str = Field(..., min_length=1, max_length=100)
    importance: int = Field(default=5, ge=1, le=10)
    tags: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None and isinstance(v, list):
            return json.dumps(v)
        return v
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            return datetime.utcnow().isoformat()


class TaskSchema(BaseModel):
    """Schema for task data"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    status: str = Field(default="pending")
    priority: str = Field(default="medium")
    due_date: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["pending", "in_progress", "completed", "canceled"]
        if v not in valid_statuses:
            return "pending"
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        valid_priorities = ["low", "medium", "high", "urgent"]
        if v not in valid_priorities:
            return "medium"
        return v
    
    @validator('due_date')
    def validate_due_date(cls, v):
        if v is not None:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
                return v
            except ValueError:
                return None
        return v
    
    @validator('created_at')
    def validate_created_at(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            return datetime.utcnow().isoformat()


class AnalysisSchema(BaseModel):
    """Schema for analysis data"""
    type: str = Field(..., min_length=1, max_length=100)
    data: str = Field(..., min_length=1)
    results: str = Field(..., min_length=1)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    @validator('data', 'results')
    def validate_json_fields(cls, v):
        if isinstance(v, dict):
            return json.dumps(v)
        return v
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            return datetime.utcnow().isoformat()


# Schema mapping for different table types
SCHEMA_MAPPING = {
    "conversations": ConversationSchema,
    "memories": MemorySchema,
    "tasks": TaskSchema,
    "analysis": AnalysisSchema
}


def validate_data(data: Dict[str, Any], table_name: str, config) -> Dict[str, Any]:
    """
    Validate data against the appropriate schema
    Returns validated and cleaned data
    """
    logger = setup_logger(__name__, config.LOG_LEVEL)
    
    try:
        # Get the appropriate schema
        schema_class = SCHEMA_MAPPING.get(table_name)
        
        if not schema_class:
            logger.warning(f"No schema found for table '{table_name}', skipping validation")
            return data
        
        # Validate the data
        validated_instance = schema_class(**data)
        validated_data = validated_instance.dict()
        
        logger.debug(f"Successfully validated data for table '{table_name}'")
        return validated_data
        
    except Exception as e:
        logger.error(f"Validation failed for table '{table_name}': {str(e)}")
        
        # Try to fix common issues and re-validate
        try:
            fixed_data = _fix_common_validation_issues(data, table_name)
            schema_class = SCHEMA_MAPPING.get(table_name)
            
            if schema_class:
                validated_instance = schema_class(**fixed_data)
                validated_data = validated_instance.dict()
                logger.info(f"Successfully validated data after fixes for table '{table_name}'")
                return validated_data
            
        except Exception as fix_error:
            logger.error(f"Failed to fix validation issues: {str(fix_error)}")
        
        # Ultimate fallback - return original data with warning
        logger.warning(f"Returning unvalidated data for table '{table_name}'")
        return data


def _fix_common_validation_issues(data: Dict[str, Any], table_name: str) -> Dict[str, Any]:
    """Attempt to fix common validation issues"""
    fixed_data = data.copy()
    
    # Fix timestamp issues
    if 'timestamp' in fixed_data and not isinstance(fixed_data['timestamp'], str):
        fixed_data['timestamp'] = datetime.utcnow().isoformat()
    
    if 'created_at' in fixed_data and not isinstance(fixed_data['created_at'], str):
        fixed_data['created_at'] = datetime.utcnow().isoformat()
    
    # Fix JSON field issues
    json_fields = {
        'conversations': ['context', 'metadata'],
        'memories': ['tags'],
        'analysis': ['data', 'results']
    }
    
    table_json_fields = json_fields.get(table_name, [])
    for field in table_json_fields:
        if field in fixed_data and isinstance(fixed_data[field], dict):
            fixed_data[field] = json.dumps(fixed_data[field])
    
    # Fix string length issues
    string_fields = {
        'conversations': {'user_id': 255, 'content': 10000},
        'memories': {'content': 10000, 'category': 100},
        'tasks': {'title': 200, 'description': 2000},
        'analysis': {'type': 100}
    }
    
    table_string_fields = string_fields.get(table_name, {})
    for field, max_length in table_string_fields.items():
        if field in fixed_data and isinstance(fixed_data[field], str):
            if len(fixed_data[field]) > max_length:
                fixed_data[field] = fixed_data[field][:max_length]
    
    # Fix specific field issues by table
    if table_name == 'tasks':
        if 'status' in fixed_data and fixed_data['status'] not in ["pending", "in_progress", "completed", "canceled"]:
            fixed_data['status'] = "pending"
        
        if 'priority' in fixed_data and fixed_data['priority'] not in ["low", "medium", "high", "urgent"]:
            fixed_data['priority'] = "medium"
    
    elif table_name == 'memories':
        if 'importance' in fixed_data:
            try:
                importance = int(fixed_data['importance'])
                fixed_data['importance'] = max(1, min(10, importance))
            except (ValueError, TypeError):
                fixed_data['importance'] = 5
    
    elif table_name == 'analysis':
        if 'confidence' in fixed_data:
            try:
                confidence = float(fixed_data['confidence'])
                fixed_data['confidence'] = max(0.0, min(1.0, confidence))
            except (ValueError, TypeError):
                fixed_data['confidence'] = 0.5
    
    return fixed_data


def get_schema_info(table_name: str) -> Dict[str, Any]:
    """Get information about a table's schema"""
    schema_class = SCHEMA_MAPPING.get(table_name)
    
    if not schema_class:
        return {"error": f"No schema found for table '{table_name}'"}
    
    # Get field information
    fields = {}
    for field_name, field_info in schema_class.__fields__.items():
        fields[field_name] = {
            "type": str(field_info.type_),
            "required": field_info.is_required(),
            "default": str(field_info.default) if field_info.default is not None else None
        }
    
    return {
        "table_name": table_name,
        "fields": fields,
        "description": schema_class.__doc__ or f"Schema for {table_name} table"
    }
