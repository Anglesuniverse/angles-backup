#!/usr/bin/env python3
"""
JSON Sanitizer and Schema Validator for Angles AI Universe™ Memory System
Handles data sanitization and validation for restore operations

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import json
import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

logger = logging.getLogger('json_sanitizer')

class JSONSanitizer:
    """Sanitizes and validates JSON data for restore operations"""
    
    # Keys that might contain secrets
    SECRET_KEYS = {
        'token', 'api_key', 'secret', 'password', 'key', 'auth',
        'credential', 'private', 'client_secret', 'access_token',
        'refresh_token', 'session_token', 'bearer_token'
    }
    
    # Required schema for decision_vault records
    DECISION_VAULT_SCHEMA = {
        'required': ['decision', 'date', 'type', 'active'],
        'optional': ['id', 'comment', 'created_at', 'updated_at', 'synced_at', 'export_timestamp'],
        'types': {
            'id': str,
            'decision': str,
            'date': str,
            'type': str,
            'active': bool,
            'comment': (str, type(None)),
            'created_at': (str, type(None)),
            'updated_at': (str, type(None)),
            'synced_at': (str, type(None)),
            'export_timestamp': (str, type(None))
        }
    }
    
    def __init__(self):
        """Initialize the JSON sanitizer"""
        logger.debug("JSON Sanitizer initialized")
    
    def sanitize_data(self, data: Dict[str, Any], remove_secrets: bool = True) -> Dict[str, Any]:
        """
        Sanitize data by removing secrets and normalizing values
        
        Args:
            data: Data to sanitize
            remove_secrets: Whether to remove secret-looking keys
            
        Returns:
            Sanitized data dictionary
        """
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Skip secret-looking keys if requested
            if remove_secrets and any(secret in key_lower for secret in self.SECRET_KEYS):
                logger.debug(f"Removing secret key: {key}")
                continue
            
            # Recursively sanitize nested dictionaries
            if isinstance(value, dict):
                sanitized[key] = self.sanitize_data(value, remove_secrets)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitize_data(item, remove_secrets) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    def validate_decision_vault_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a decision_vault record against schema
        
        Args:
            record: Record to validate
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        
        # Check required fields
        for field in self.DECISION_VAULT_SCHEMA['required']:
            if field not in record:
                errors.append(f"Missing required field: {field}")
            elif record[field] is None or record[field] == '':
                errors.append(f"Required field is empty: {field}")
        
        # Check field types
        for field, value in record.items():
            if field in self.DECISION_VAULT_SCHEMA['types']:
                expected_type = self.DECISION_VAULT_SCHEMA['types'][field]
                if isinstance(expected_type, tuple):
                    # Multiple allowed types (e.g., str or None)
                    if not isinstance(value, expected_type):
                        warnings.append(f"Field {field} has unexpected type: {type(value).__name__}")
                else:
                    # Single expected type
                    if not isinstance(value, expected_type):
                        warnings.append(f"Field {field} has unexpected type: {type(value).__name__}")
        
        # Check for unknown fields
        known_fields = set(self.DECISION_VAULT_SCHEMA['required'] + self.DECISION_VAULT_SCHEMA['optional'])
        for field in record.keys():
            if field not in known_fields:
                warnings.append(f"Unknown field will be ignored: {field}")
        
        # Validate date format
        if 'date' in record:
            try:
                datetime.strptime(record['date'], '%Y-%m-%d')
            except ValueError:
                errors.append(f"Invalid date format: {record['date']} (expected YYYY-MM-DD)")
        
        # Validate type field
        if 'type' in record:
            valid_types = ['technical', 'business', 'strategy', 'process', 'security', 'architectural']
            if record['type'] not in valid_types:
                warnings.append(f"Unusual decision type: {record['type']}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "record": record
        }
    
    def validate_json_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate JSON file and return parsed data with validation results
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Dictionary with validation results and data
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": str(file_path)
            }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Successfully loaded JSON file: {file_path}")
            
            # Determine data structure
            if isinstance(data, dict):
                if 'decisions' in data and isinstance(data['decisions'], list):
                    # Export format with metadata
                    records = data['decisions']
                    metadata = {k: v for k, v in data.items() if k != 'decisions'}
                elif 'export_timestamp' in data or 'total_decisions' in data:
                    # Export format but check for decisions key
                    records = data.get('decisions', [])
                    metadata = {k: v for k, v in data.items() if k != 'decisions'}
                else:
                    # Single record
                    records = [data]
                    metadata = {}
            elif isinstance(data, list):
                # Array of records
                records = data
                metadata = {}
            else:
                return {
                    "success": False,
                    "error": f"Unexpected JSON structure in {file_path}",
                    "file_path": str(file_path)
                }
            
            # Validate each record
            validation_results = []
            valid_records = []
            
            for i, record in enumerate(records):
                validation = self.validate_decision_vault_record(record)
                validation_results.append({
                    "index": i,
                    "validation": validation
                })
                
                if validation["valid"]:
                    valid_records.append(record)
                else:
                    logger.warning(f"Invalid record at index {i}: {validation['errors']}")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "total_records": len(records),
                "valid_records": len(valid_records),
                "invalid_records": len(records) - len(valid_records),
                "records": valid_records,
                "metadata": metadata,
                "validation_results": validation_results
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON in {file_path}: {e}",
                "file_path": str(file_path)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error reading {file_path}: {e}",
                "file_path": str(file_path)
            }
    
    def create_deterministic_id(self, record: Dict[str, Any]) -> str:
        """
        Create a deterministic ID from decision content
        
        Args:
            record: Decision record
            
        Returns:
            Deterministic UUID-like string
        """
        import hashlib
        
        # Create hash from decision + date + type
        content = f"{record.get('decision', '')}-{record.get('date', '')}-{record.get('type', '')}"
        hash_obj = hashlib.md5(content.encode('utf-8'))
        hex_hash = hash_obj.hexdigest()
        
        # Format as UUID-like string
        uuid_like = f"{hex_hash[:8]}-{hex_hash[8:12]}-{hex_hash[12:16]}-{hex_hash[16:20]}-{hex_hash[20:32]}"
        
        return uuid_like
    
    def normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize record for database insertion
        
        Args:
            record: Raw record from JSON
            
        Returns:
            Normalized record ready for database
        """
        normalized = {}
        
        # Copy known fields only
        known_fields = set(self.DECISION_VAULT_SCHEMA['required'] + self.DECISION_VAULT_SCHEMA['optional'])
        
        for field in known_fields:
            if field in record:
                normalized[field] = record[field]
        
        # Ensure ID exists
        if 'id' not in normalized or not normalized['id']:
            normalized['id'] = self.create_deterministic_id(record)
        
        # Ensure timestamps are properly formatted
        for ts_field in ['created_at', 'updated_at', 'synced_at']:
            if ts_field in normalized and normalized[ts_field]:
                try:
                    # Try to parse and reformat timestamp
                    if 'T' in str(normalized[ts_field]):
                        dt = datetime.fromisoformat(str(normalized[ts_field]).replace('Z', '+00:00'))
                        normalized[ts_field] = dt.isoformat()
                except ValueError:
                    logger.warning(f"Invalid timestamp format for {ts_field}: {normalized[ts_field]}")
        
        return normalized