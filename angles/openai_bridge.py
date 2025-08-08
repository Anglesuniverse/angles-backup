"""
OpenAI bridge for Angles AI Universe™
Handles OpenAI API operations with graceful fallback
"""

import logging
from typing import Optional

from .config import has_openai, OPENAI_API_KEY, OPENAI_MODEL


logger = logging.getLogger(__name__)


class OpenAIBridge:
    """Bridge for OpenAI operations with graceful fallback"""
    
    def __init__(self):
        self.available = has_openai()
        self.client = None
        self.model = OPENAI_MODEL
        
        if self.available:
            try:
                # Try to import and initialize OpenAI client
                from openai import OpenAI
                self.client = OpenAI(api_key=OPENAI_API_KEY)
            except ImportError:
                logger.warning("openai package not available")
                self.available = False
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.available = False
    
    def is_available(self) -> bool:
        """Check if OpenAI integration is available"""
        return self.available
    
    def analyze_text(self, prompt: str) -> str:
        """Analyze text using OpenAI with safe defaults"""
        if not self.available:
            logger.info("OpenAI unavailable, returning graceful message")
            return "OpenAI analysis unavailable - manual review recommended"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant analyzing system data. Provide concise, actionable insights."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            logger.info("✅ OpenAI analysis completed")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return f"OpenAI analysis failed: {str(e)}"
    
    def generate_fix_list(self, logs: list, repo_structure: str) -> str:
        """Generate prioritized fix list from logs and repo structure"""
        prompt = f"""
Analyze the following system logs and repository structure to generate a prioritized fix list.

Recent System Logs:
{logs[:5] if logs else 'No recent logs available'}

Repository Structure:
{repo_structure[:1000] if repo_structure else 'Structure not available'}

Please provide:
1. Top 3 immediate fixes needed
2. Top 2 optimization opportunities  
3. Any security or reliability concerns

Format as a numbered list with brief explanations.
"""
        
        return self.analyze_text(prompt)
    
    def analyze_deployment_health(self, health_data: dict) -> str:
        """Analyze deployment health status"""
        prompt = f"""
Analyze this deployment health data and provide recommendations:

Health Status: {health_data}

Provide:
1. Overall health assessment
2. Critical issues to address
3. Performance optimizations
4. Monitoring recommendations

Be concise and actionable.
"""
        
        return self.analyze_text(prompt)