"""
GPT output parser for different data formats
Handles JSON, structured text, and unstructured content
"""

import json
import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from utils.logger import setup_logger


class GPTParser:
    """Parser for GPT assistant outputs"""
    
    def __init__(self, config):
        self.config = config
        self.logger = setup_logger(__name__, config.LOG_LEVEL)
    
    def parse_output(self, raw_output: str, output_type: Optional[str] = None) -> Dict[str, Any]:
        """Parse GPT output based on detected or specified type"""
        try:
            self.logger.debug(f"Parsing GPT output of type: {output_type}")
            
            # Clean the input
            cleaned_output = self._clean_output(raw_output)
            
            # Determine parsing strategy
            if output_type == "json" or self._is_json_format(cleaned_output):
                return self._parse_json_output(cleaned_output)
            elif output_type == "structured" or self._is_structured_text(cleaned_output):
                return self._parse_structured_text(cleaned_output)
            else:
                return self._parse_unstructured_text(cleaned_output)
                
        except Exception as e:
            self.logger.error(f"Failed to parse GPT output: {str(e)}")
            # Fallback to unstructured parsing
            return self._parse_unstructured_text(raw_output)
    
    def _clean_output(self, output: str) -> str:
        """Clean and normalize the output text"""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', output.strip())
        
        # Remove common GPT artifacts
        artifacts = [
            r'^(GPT|Assistant):\s*',
            r'^Response:\s*',
            r'^Output:\s*',
            r'```json\s*',
            r'```\s*$',
            r'^```\s*',
        ]
        
        for pattern in artifacts:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        
        return cleaned.strip()
    
    def _is_json_format(self, text: str) -> bool:
        """Check if text appears to be JSON format"""
        text = text.strip()
        return (text.startswith('{') and text.endswith('}')) or \
               (text.startswith('[') and text.endswith(']'))
    
    def _is_structured_text(self, text: str) -> bool:
        """Check if text appears to be structured (has clear patterns)"""
        # Look for common structured patterns
        patterns = [
            r'^\s*[-*]\s+',  # Bullet points
            r'^\s*\d+\.\s+',  # Numbered lists
            r'^\s*[A-Za-z]+:\s*',  # Key-value pairs
            r'^\s*##?\s+',  # Headers
            r'Title:\s*',
            r'Summary:\s*',
            r'Task:\s*',
            r'Memory:\s*'
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.MULTILINE):
                return True
        
        return False
    
    def _parse_json_output(self, text: str) -> Dict[str, Any]:
        """Parse JSON formatted output"""
        try:
            parsed = json.loads(text)
            
            result = {
                "format_type": "json",
                "parsed_data": parsed,
                "metadata": {
                    "parsing_method": "json",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data_type": type(parsed).__name__
                }
            }
            
            # Add structure analysis
            if isinstance(parsed, dict):
                result["metadata"]["keys"] = list(parsed.keys())
                result["metadata"]["key_count"] = len(parsed.keys())
            elif isinstance(parsed, list):
                result["metadata"]["item_count"] = len(parsed)
                if parsed and isinstance(parsed[0], dict):
                    result["metadata"]["item_keys"] = list(parsed[0].keys())
            
            self.logger.debug("Successfully parsed JSON output")
            return result
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse as JSON: {str(e)}")
            # Fallback to structured text parsing
            return self._parse_structured_text(text)
    
    def _parse_structured_text(self, text: str) -> Dict[str, Any]:
        """Parse structured text output"""
        try:
            parsed_data = {}
            current_section = None
            
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for headers
                header_match = re.match(r'^##?\s*(.+)', line)
                if header_match:
                    current_section = header_match.group(1).lower().replace(' ', '_')
                    parsed_data[current_section] = []
                    continue
                
                # Check for key-value pairs
                kv_match = re.match(r'^([A-Za-z][A-Za-z0-9\s]*?):\s*(.+)', line)
                if kv_match:
                    key = kv_match.group(1).strip().lower().replace(' ', '_')
                    value = kv_match.group(2).strip()
                    parsed_data[key] = value
                    continue
                
                # Check for list items
                list_match = re.match(r'^[-*]\s*(.+)', line)
                if list_match:
                    item = list_match.group(1).strip()
                    if current_section:
                        if current_section not in parsed_data:
                            parsed_data[current_section] = []
                        parsed_data[current_section].append(item)
                    else:
                        if 'items' not in parsed_data:
                            parsed_data['items'] = []
                        parsed_data['items'].append(item)
                    continue
                
                # Check for numbered items
                num_match = re.match(r'^\d+\.\s*(.+)', line)
                if num_match:
                    item = num_match.group(1).strip()
                    if current_section:
                        if current_section not in parsed_data:
                            parsed_data[current_section] = []
                        parsed_data[current_section].append(item)
                    else:
                        if 'numbered_items' not in parsed_data:
                            parsed_data['numbered_items'] = []
                        parsed_data['numbered_items'].append(item)
                    continue
                
                # Default: add as content
                if current_section:
                    if isinstance(parsed_data.get(current_section), list):
                        parsed_data[current_section].append(line)
                    else:
                        parsed_data[current_section] = line
                else:
                    if 'content' not in parsed_data:
                        parsed_data['content'] = []
                    parsed_data['content'].append(line)
            
            result = {
                "format_type": "structured_text",
                "parsed_data": parsed_data,
                "metadata": {
                    "parsing_method": "structured_text",
                    "timestamp": datetime.utcnow().isoformat(),
                    "sections": list(parsed_data.keys()),
                    "section_count": len(parsed_data)
                }
            }
            
            self.logger.debug("Successfully parsed structured text")
            return result
            
        except Exception as e:
            self.logger.warning(f"Failed to parse as structured text: {str(e)}")
            return self._parse_unstructured_text(text)
    
    def _parse_unstructured_text(self, text: str) -> Dict[str, Any]:
        """Parse unstructured text output"""
        try:
            # Extract basic features from unstructured text
            word_count = len(text.split())
            sentence_count = len(re.findall(r'[.!?]+', text))
            
            # Try to identify key phrases or topics
            topics = self._extract_topics(text)
            
            # Check for specific patterns
            patterns = self._identify_patterns(text)
            
            parsed_data = {
                "content": text,
                "word_count": word_count,
                "sentence_count": sentence_count,
                "topics": topics,
                "patterns": patterns
            }
            
            result = {
                "format_type": "unstructured_text",
                "parsed_data": parsed_data,
                "metadata": {
                    "parsing_method": "unstructured_text",
                    "timestamp": datetime.utcnow().isoformat(),
                    "text_length": len(text),
                    "complexity": self._assess_complexity(text)
                }
            }
            
            self.logger.debug("Successfully parsed unstructured text")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to parse unstructured text: {str(e)}")
            # Ultimate fallback
            return {
                "format_type": "raw",
                "parsed_data": {"content": text},
                "metadata": {
                    "parsing_method": "fallback",
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e)
                }
            }
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract potential topics from text"""
        # Simple keyword extraction - could be enhanced with NLP
        keywords = []
        
        # Common topic indicators
        topic_patterns = [
            r'\b(task|todo|reminder)\b',
            r'\b(memory|remember|recall)\b',
            r'\b(analysis|insight|pattern)\b',
            r'\b(conversation|chat|discussion)\b',
            r'\b(question|answer|solution)\b'
        ]
        
        for pattern in topic_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.extend(matches)
        
        # Extract capitalized words (potential proper nouns/topics)
        capitalized = re.findall(r'\b[A-Z][a-z]+\b', text)
        keywords.extend(capitalized[:5])  # Limit to avoid noise
        
        return list(set(keywords))
    
    def _identify_patterns(self, text: str) -> List[str]:
        """Identify common patterns in text"""
        patterns = []
        
        # Common patterns
        if re.search(r'\b(urgent|asap|immediately)\b', text, re.IGNORECASE):
            patterns.append("urgent")
        
        if re.search(r'\b(question|what|how|why|when|where)\b', text, re.IGNORECASE):
            patterns.append("question")
        
        if re.search(r'\b(complete|done|finished|accomplish)\b', text, re.IGNORECASE):
            patterns.append("completion")
        
        if re.search(r'\b(schedule|meeting|appointment|deadline)\b', text, re.IGNORECASE):
            patterns.append("scheduling")
        
        if re.search(r'\b(data|analysis|report|chart|graph)\b', text, re.IGNORECASE):
            patterns.append("analytical")
        
        return patterns
    
    def _assess_complexity(self, text: str) -> str:
        """Assess the complexity of the text"""
        word_count = len(text.split())
        sentence_count = len(re.findall(r'[.!?]+', text))
        
        avg_words_per_sentence = word_count / max(sentence_count, 1)
        
        if word_count < 20:
            return "simple"
        elif word_count < 100 and avg_words_per_sentence < 15:
            return "moderate"
        else:
            return "complex"
