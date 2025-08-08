#!/usr/bin/env python3
"""
Angles AI Universe™ GPT-5 Client
Centralized OpenAI GPT-5 client for the backend system

Author: Angles AI Universe™ AI Team
Version: 1.0.0 - GPT-5 Integration
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union

# Check for OpenAI availability
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

# Default model configuration
DEFAULT_MODEL = "gpt-5"
FALLBACK_MODEL = "gpt-4o"  # Fallback if GPT-5 not available yet

def get_client() -> Optional[OpenAI]:
    """
    Get configured OpenAI client for GPT-5 integration
    
    Returns:
        OpenAI client instance or None if not available
    """
    if not OPENAI_AVAILABLE:
        return None
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None
    
    try:
        client = OpenAI(api_key=api_key)
        return client
    except Exception as e:
        logging.error(f"Failed to initialize OpenAI client: {e}")
        return None

def get_model() -> str:
    """
    Get the configured model name
    
    Returns:
        Model name string (GPT-5 or fallback)
    """
    # Check if GPT-5 is explicitly disabled
    force_fallback = os.getenv('USE_GPT4O_FALLBACK', '').lower() == 'true'
    
    if force_fallback:
        return FALLBACK_MODEL
    
    return DEFAULT_MODEL

async def analyze_decision_with_gpt5(client: OpenAI, decision_text: str) -> Dict[str, Any]:
    """
    Analyze architectural decision using GPT-5
    
    Args:
        client: OpenAI client instance
        decision_text: Decision text to analyze
        
    Returns:
        Analysis results in structured format
    """
    if not client:
        raise ValueError("OpenAI client not available")
    
    model = get_model()
    
    prompt = f"""
    Analyze this architectural decision and provide comprehensive classification:
    
    Decision: {decision_text}
    
    Please provide a JSON response with exactly this structure:
    {{
        "type": "strategy|technical|architecture|process|security|ethical|product|other",
        "priority": "P0|P1|P2",
        "category": "specific descriptive category",
        "confidence": 0.85,
        "key_concepts": ["concept1", "concept2", "concept3"],
        "potential_impact": "Brief assessment of potential impact",
        "recommendations": ["rec1", "rec2"],
        "related_areas": ["area1", "area2"],
        "risk_level": "low|medium|high|critical",
        "complexity": "simple|moderate|complex|very_complex",
        "timeline_estimate": "immediate|short_term|medium_term|long_term",
        "stakeholders": ["stakeholder1", "stakeholder2"],
        "dependencies": ["dependency1", "dependency2"],
        "success_metrics": ["metric1", "metric2"]
    }}
    
    Focus on providing actionable insights for architectural decision management.
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert architectural decision analyst. Provide structured, actionable analysis of technical decisions in JSON format."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1,  # Low temperature for consistent analysis
            max_tokens=1500
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Add metadata
        result["analyzed_by"] = model
        result["analysis_timestamp"] = "2025-08-08T11:17:00Z"
        result["analysis_version"] = "1.0.0"
        
        return result
        
    except Exception as e:
        logging.error(f"GPT-5 analysis failed: {e}")
        # Return fallback structure
        return {
            "type": "other",
            "priority": "P2",
            "category": "unclassified",
            "confidence": 0.0,
            "key_concepts": [],
            "potential_impact": f"Analysis failed: {str(e)}",
            "recommendations": ["Review decision manually"],
            "related_areas": [],
            "risk_level": "medium",
            "complexity": "moderate",
            "timeline_estimate": "medium_term",
            "stakeholders": [],
            "dependencies": [],
            "success_metrics": [],
            "analyzed_by": "fallback",
            "analysis_timestamp": "2025-08-08T11:17:00Z",
            "analysis_version": "1.0.0",
            "error": str(e)
        }

def test_gpt5_connection() -> Dict[str, Any]:
    """
    Test GPT-5 connection and capabilities
    
    Returns:
        Test results with status and details
    """
    result = {
        "timestamp": "2025-08-08T11:17:00Z",
        "openai_available": OPENAI_AVAILABLE,
        "client_status": "not_tested",
        "model": get_model(),
        "test_successful": False,
        "error": None
    }
    
    if not OPENAI_AVAILABLE:
        result["error"] = "OpenAI package not available"
        return result
    
    client = get_client()
    if not client:
        result["error"] = "Failed to initialize OpenAI client"
        return result
    
    result["client_status"] = "initialized"
    
    try:
        # Simple test query
        response = client.chat.completions.create(
            model=get_model(),
            messages=[
                {
                    "role": "user",
                    "content": "Respond with a single word: 'SUCCESS'"
                }
            ],
            max_tokens=10
        )
        
        if "SUCCESS" in response.choices[0].message.content:
            result["test_successful"] = True
            result["response"] = response.choices[0].message.content.strip()
        else:
            result["error"] = f"Unexpected response: {response.choices[0].message.content}"
            
    except Exception as e:
        result["error"] = str(e)
    
    return result

def get_ai_enhancement_status() -> Dict[str, Any]:
    """
    Get comprehensive AI enhancement status
    
    Returns:
        Status report with capabilities and configuration
    """
    return {
        "timestamp": "2025-08-08T11:17:00Z",
        "openai_package_available": OPENAI_AVAILABLE,
        "api_key_configured": bool(os.getenv('OPENAI_API_KEY')),
        "default_model": DEFAULT_MODEL,
        "fallback_model": FALLBACK_MODEL,
        "current_model": get_model(),
        "client_ready": get_client() is not None,
        "features": {
            "decision_analysis": True,
            "classification": True,
            "priority_ranking": True,
            "impact_assessment": True,
            "recommendation_generation": True
        },
        "version": "1.0.0"
    }

# Initialize logging for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"✅ AI Client initialized - Model: {get_model()}, Available: {OPENAI_AVAILABLE}")