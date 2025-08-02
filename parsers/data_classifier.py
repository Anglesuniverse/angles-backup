"""
Data classifier for intelligent table routing
Determines the appropriate table based on content analysis
"""

import re
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from utils.logger import setup_logger


class DataClassifier:
    """Classifies parsed data to determine appropriate table routing"""
    
    def __init__(self, config):
        self.config = config
        self.logger = setup_logger(__name__, config.LOG_LEVEL)
        
        # Classification weights for different indicators
        self.classification_weights = {
            "keyword_match": 1.0,
            "structure_match": 0.8,
            "pattern_match": 0.6,
            "context_match": 0.4
        }
    
    def classify_data(self, parsed_data: Dict[str, Any]) -> Tuple[str, float]:
        """
        Classify data and return the best table match with confidence score
        Returns: (table_name, confidence_score)
        """
        try:
            self.logger.debug("Starting data classification")
            
            scores = {}
            
            # Get content for analysis
            content = self._extract_content(parsed_data)
            
            # Score each possible table
            for table_name in self.config.get_all_table_names():
                score = self._calculate_table_score(content, parsed_data, table_name)
                scores[table_name] = score
                self.logger.debug(f"Table '{table_name}' score: {score}")
            
            # Find the best match
            if scores:
                best_table = max(scores.keys(), key=lambda k: scores[k])
                best_score = scores[best_table]
            else:
                best_table = "conversations"
                best_score = 0.1
            
            self.logger.info(f"Classified data as '{best_table}' with confidence {best_score:.2f}")
            
            return best_table, best_score
            
        except Exception as e:
            self.logger.error(f"Classification failed: {str(e)}")
            # Default fallback
            return "conversations", 0.1
    
    def _extract_content(self, parsed_data: Dict[str, Any]) -> str:
        """Extract text content from parsed data for analysis"""
        content_parts = []
        
        # Extract from different possible locations
        data = parsed_data.get("parsed_data", {})
        
        if isinstance(data, dict):
            # Look for common content fields
            content_fields = ["content", "text", "message", "description", "title", "summary"]
            
            for field in content_fields:
                if field in data:
                    value = data[field]
                    if isinstance(value, str):
                        content_parts.append(value)
                    elif isinstance(value, list):
                        content_parts.extend([str(item) for item in value])
            
            # If no specific content fields, use all string values
            if not content_parts:
                for key, value in data.items():
                    if isinstance(value, str):
                        content_parts.append(f"{key}: {value}")
                    elif isinstance(value, list):
                        content_parts.append(f"{key}: {' '.join([str(item) for item in value])}")
        
        elif isinstance(data, str):
            content_parts.append(data)
        
        return " ".join(content_parts).lower()
    
    def _calculate_table_score(self, content: str, parsed_data: Dict[str, Any], table_name: str) -> float:
        """Calculate classification score for a specific table"""
        schema = self.config.get_table_schema(table_name)
        if not schema:
            return 0.0
        
        total_score = 0.0
        
        # Keyword matching
        keyword_score = self._calculate_keyword_score(content, schema.get("classification_keywords", []))
        total_score += keyword_score * self.classification_weights["keyword_match"]
        
        # Structure matching
        structure_score = self._calculate_structure_score(parsed_data, schema.get("fields", []))
        total_score += structure_score * self.classification_weights["structure_match"]
        
        # Pattern matching
        pattern_score = self._calculate_pattern_score(parsed_data, table_name)
        total_score += pattern_score * self.classification_weights["pattern_match"]
        
        # Context matching
        context_score = self._calculate_context_score(parsed_data, table_name)
        total_score += context_score * self.classification_weights["context_match"]
        
        return min(total_score, 1.0)  # Cap at 1.0
    
    def _calculate_keyword_score(self, content: str, keywords: List[str]) -> float:
        """Calculate score based on keyword matches"""
        if not keywords:
            return 0.0
        
        matches = 0
        total_keywords = len(keywords)
        
        for keyword in keywords:
            if keyword.lower() in content:
                matches += 1
        
        return matches / total_keywords
    
    def _calculate_structure_score(self, parsed_data: Dict[str, Any], expected_fields: List[str]) -> float:
        """Calculate score based on data structure matching expected fields"""
        if not expected_fields:
            return 0.0
        
        data = parsed_data.get("parsed_data", {})
        if not isinstance(data, dict):
            return 0.0
        
        matches = 0
        total_fields = len(expected_fields)
        
        for field in expected_fields:
            # Check for exact match or similar field names
            if field in data or any(field.lower() in key.lower() for key in data.keys()):
                matches += 1
        
        return matches / total_fields
    
    def _calculate_pattern_score(self, parsed_data: Dict[str, Any], table_name: str) -> float:
        """Calculate score based on data patterns specific to table type"""
        patterns = parsed_data.get("parsed_data", {}).get("patterns", [])
        if not patterns:
            return 0.0
        
        # Table-specific pattern mappings
        pattern_mappings = {
            "conversations": ["question", "completion"],
            "memories": ["analytical", "completion"],
            "tasks": ["urgent", "scheduling", "completion"],
            "analysis": ["analytical", "question"]
        }
        
        relevant_patterns = pattern_mappings.get(table_name, [])
        if not relevant_patterns:
            return 0.0
        
        matches = sum(1 for pattern in patterns if pattern in relevant_patterns)
        return min(matches / len(relevant_patterns), 1.0)
    
    def _calculate_context_score(self, parsed_data: Dict[str, Any], table_name: str) -> float:
        """Calculate score based on contextual indicators"""
        format_type = parsed_data.get("format_type", "")
        metadata = parsed_data.get("metadata", {})
        
        # Format-based scoring
        format_scores = {
            "conversations": {"structured_text": 0.8, "unstructured_text": 0.9},
            "memories": {"json": 0.9, "structured_text": 0.8},
            "tasks": {"structured_text": 0.9, "json": 0.8},
            "analysis": {"json": 1.0, "structured_text": 0.7}
        }
        
        base_score = format_scores.get(table_name, {}).get(format_type, 0.5)
        
        # Adjust based on complexity and other metadata
        complexity = metadata.get("complexity", "moderate")
        if table_name == "analysis" and complexity == "complex":
            base_score += 0.2
        elif table_name == "conversations" and complexity == "simple":
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def get_classification_explanation(self, parsed_data: Dict[str, Any], table_name: str) -> Dict[str, Any]:
        """Get detailed explanation of classification decision"""
        try:
            content = self._extract_content(parsed_data)
            schema = self.config.get_table_schema(table_name)
            
            explanation = {
                "table": table_name,
                "timestamp": datetime.utcnow().isoformat(),
                "content_summary": content[:200] + "..." if len(content) > 200 else content,
                "factors": {}
            }
            
            if schema:
                # Keyword analysis
                keywords = schema.get("classification_keywords", [])
                keyword_matches = [kw for kw in keywords if kw.lower() in content]
                explanation["factors"]["keyword_matches"] = keyword_matches
                
                # Structure analysis
                data = parsed_data.get("parsed_data", {})
                if isinstance(data, dict):
                    available_fields = list(data.keys())
                    expected_fields = schema.get("fields", [])
                    field_matches = [field for field in expected_fields 
                                   if field in available_fields or 
                                   any(field.lower() in key.lower() for key in available_fields)]
                    explanation["factors"]["structure_matches"] = field_matches
                
                # Pattern analysis
                patterns = data.get("patterns", []) if isinstance(data, dict) else []
                explanation["factors"]["detected_patterns"] = patterns
            
            return explanation
            
        except Exception as e:
            self.logger.error(f"Failed to generate classification explanation: {str(e)}")
            return {"error": str(e), "table": table_name}
