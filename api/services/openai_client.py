"""
Angles OS™ OpenAI Integration
GPT-5 ready client with fallback to rule-based systems
"""
from typing import Optional, Dict, Any, List
from api.config import settings
from api.utils.logging import logger

try:
    from openai import OpenAI
    _openai_available = True
except ImportError:
    _openai_available = False
    logger.warning("OpenAI library not available, using fallbacks")

class OpenAIClient:
    """OpenAI GPT-5 client with fallbacks"""
    
    def __init__(self):
        self.client = None
        if _openai_available and settings.has_openai():
            try:
                self.client = OpenAI(api_key=settings.openai_api_key)
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"OpenAI client initialization failed: {e}")
    
    def is_available(self) -> bool:
        """Check if OpenAI is available"""
        return self.client is not None
    
    def summarize(self, text: str, max_length: int = 100) -> str:
        """Summarize text using GPT-5 or fallback"""
        if not self.is_available():
            return self._fallback_summarize(text, max_length)
        
        try:
            # Using gpt-5 as placeholder for future model
            response = self.client.chat.completions.create(
                model="gpt-5",  # Note: GPT-5 ready naming
                messages=[
                    {
                        "role": "system",
                        "content": f"Summarize the following text in {max_length} characters or less. Be concise and capture key points."
                    },
                    {"role": "user", "content": text}
                ],
                max_tokens=50,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            logger.debug(f"Generated summary for text of length {len(text)}")
            return summary
            
        except Exception as e:
            logger.error(f"OpenAI summarization failed: {e}")
            return self._fallback_summarize(text, max_length)
    
    def decide(self, topic: str, options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate decision recommendation using GPT-5 or fallback"""
        if not self.is_available():
            return self._fallback_decide(topic, options)
        
        try:
            options_text = "\n".join([
                f"Option {i+1}: {opt['option']}\n  Pros: {', '.join(opt.get('pros', []))}\n  Cons: {', '.join(opt.get('cons', []))}"
                for i, opt in enumerate(options)
            ])
            
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a strategic decision advisor. Analyze options and provide a clear recommendation with rationale."
                    },
                    {
                        "role": "user",
                        "content": f"Decision needed: {topic}\n\nOptions:\n{options_text}\n\nProvide your recommendation and reasoning."
                    }
                ],
                max_tokens=200,
                temperature=0.5
            )
            
            recommendation = response.choices[0].message.content.strip()
            
            # Extract recommendation (simplified parsing)
            chosen = self._extract_chosen_option(recommendation, options)
            
            return {
                'chosen': chosen,
                'rationale': recommendation,
                'method': 'gpt-5'
            }
            
        except Exception as e:
            logger.error(f"OpenAI decision failed: {e}")
            return self._fallback_decide(topic, options)
    
    def _fallback_summarize(self, text: str, max_length: int) -> str:
        """Simple rule-based summarization"""
        # Take first sentence or truncate to max_length
        sentences = text.split('. ')
        if sentences and len(sentences[0]) <= max_length:
            return sentences[0] + ('.' if not sentences[0].endswith('.') else '')
        
        # Truncate to max_length
        if len(text) <= max_length:
            return text
        
        return text[:max_length-3] + "..."
    
    def _fallback_decide(self, topic: str, options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple heuristic-based decision"""
        best_score = -999
        best_option = None
        
        for option in options:
            pros = len(option.get('pros', []))
            cons = len(option.get('cons', []))
            score = pros - cons
            
            if score > best_score:
                best_score = score
                best_option = option['option']
        
        return {
            'chosen': best_option or options[0]['option'] if options else 'No option',
            'rationale': f"Selected based on pros/cons analysis (score: {best_score})",
            'method': 'heuristic'
        }
    
    def _extract_chosen_option(self, recommendation: str, options: List[Dict[str, Any]]) -> str:
        """Extract chosen option from GPT response"""
        recommendation_lower = recommendation.lower()
        
        for option in options:
            if option['option'].lower() in recommendation_lower:
                return option['option']
        
        # Default to first option if none detected
        return options[0]['option'] if options else 'Unknown'