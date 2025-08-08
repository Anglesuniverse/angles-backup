#!/usr/bin/env python3
"""
Angles AI Universe™ GPT-5 Enhanced Memory Bridge
Advanced AI-powered memory management and decision optimization

Author: Angles AI Universe™ AI Team
Version: 2.0.0 - GPT-5 Ready
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Check for OpenAI availability
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

# Import our security module
try:
    from security.data_sanitizer import DataSanitizer, SecureFileManager
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    DataSanitizer = None
    SecureFileManager = None

class AIEnhancedMemoryBridge:
    """
    GPT-5 Enhanced Memory Bridge for intelligent decision management
    
    Features:
    - AI-powered decision classification and optimization
    - Intelligent memory synthesis and duplicate detection  
    - Automated decision priority ranking
    - Context-aware memory retrieval
    - Natural language decision queries
    - Predictive memory insights
    """
    
    def __init__(self, enable_ai: bool = True):
        self.logger = logging.getLogger('ai_memory_bridge')
        self.enable_ai = enable_ai and OPENAI_AVAILABLE
        
        # Initialize OpenAI client if available
        if self.enable_ai and OpenAI:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.client = OpenAI(api_key=api_key)
                self.model = "gpt-4o"  # Latest model as of blueprint
                self.logger.info("✅ GPT-5/GPT-4o AI engine initialized")
            else:
                self.enable_ai = False
                self.logger.warning("⚠️ OPENAI_API_KEY not found - AI features disabled")
        else:
            self.logger.info("ℹ️ AI features disabled - operating in standard mode")
        
        # Initialize security components
        if SECURITY_AVAILABLE and DataSanitizer and SecureFileManager:
            self.sanitizer = DataSanitizer()
            self.secure_manager = SecureFileManager()
            self.logger.info("✅ Security components initialized")
        else:
            self.sanitizer = None
            self.secure_manager = None
            self.logger.warning("⚠️ Security components not available")
    
    def classify_decision(self, decision_text: str) -> Dict[str, Any]:
        """
        AI-powered decision classification and analysis
        
        Args:
            decision_text: The decision text to classify
            
        Returns:
            Classification results with type, priority, and insights
        """
        if not self.enable_ai:
            return self._fallback_classification(decision_text)
        
        try:
            prompt = f"""
            Analyze this architectural decision and provide classification:
            
            Decision: {decision_text}
            
            Please provide a JSON response with:
            {{
                "type": "architecture|technical|business|process|security",
                "priority": "critical|high|medium|low",
                "category": "specific category name",
                "confidence": 0.0-1.0,
                "key_concepts": ["concept1", "concept2"],
                "potential_impact": "brief impact assessment",
                "related_decisions": ["potential related areas"],
                "action_items": ["actionable items if any"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert system architect analyzing architectural decisions. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=500,
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Add metadata
            result['ai_analysis'] = True
            result['analysis_timestamp'] = datetime.now(timezone.utc).isoformat()
            result['model_used'] = self.model
            
            self.logger.info(f"✅ AI classification completed: {result['type']}/{result['priority']}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ AI classification failed: {e}")
            return self._fallback_classification(decision_text)
    
    def _fallback_classification(self, decision_text: str) -> Dict[str, Any]:
        """Fallback classification using keyword matching"""
        text_lower = decision_text.lower()
        
        # Determine type based on keywords
        if any(word in text_lower for word in ['database', 'schema', 'migration', 'sql']):
            decision_type = 'technical'
            category = 'database'
        elif any(word in text_lower for word in ['security', 'auth', 'permission', 'encrypt']):
            decision_type = 'security'
            category = 'security'
        elif any(word in text_lower for word in ['api', 'endpoint', 'service', 'integration']):
            decision_type = 'architecture'
            category = 'api_design'
        elif any(word in text_lower for word in ['process', 'workflow', 'procedure']):
            decision_type = 'process'
            category = 'workflow'
        else:
            decision_type = 'architecture'
            category = 'general'
        
        # Determine priority based on keywords
        if any(word in text_lower for word in ['critical', 'urgent', 'blocking', 'security', 'data loss']):
            priority = 'critical'
        elif any(word in text_lower for word in ['important', 'performance', 'optimization']):
            priority = 'high'
        elif any(word in text_lower for word in ['minor', 'cleanup', 'refactor']):
            priority = 'low'
        else:
            priority = 'medium'
        
        return {
            'type': decision_type,
            'priority': priority,
            'category': category,
            'confidence': 0.7,
            'key_concepts': [],
            'potential_impact': 'Impact assessment not available',
            'related_decisions': [],
            'action_items': [],
            'ai_analysis': False,
            'analysis_timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def optimize_decision_text(self, decision_text: str) -> Dict[str, Any]:
        """
        AI-powered decision text optimization for clarity and completeness
        
        Args:
            decision_text: Original decision text
            
        Returns:
            Optimization results with improved text and suggestions
        """
        if not self.enable_ai:
            return {
                'optimized_text': decision_text,
                'improvements': [],
                'confidence': 0.5,
                'ai_optimized': False
            }
        
        try:
            prompt = f"""
            Optimize this architectural decision for clarity and completeness:
            
            Original Decision: {decision_text}
            
            Please provide a JSON response with:
            {{
                "optimized_text": "improved version of the decision",
                "improvements": ["list of improvements made"],
                "missing_elements": ["elements that could be added"],
                "clarity_score": 0.0-1.0,
                "completeness_score": 0.0-1.0,
                "suggestions": ["additional suggestions"]
            }}
            
            Focus on:
            - Clear problem statement
            - Rationale for decision
            - Alternative considerations
            - Implementation details
            - Risk assessment
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert technical writer specializing in architectural decisions. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
                temperature=0.4
            )
            
            result = json.loads(response.choices[0].message.content)
            result['ai_optimized'] = True
            result['optimization_timestamp'] = datetime.now(timezone.utc).isoformat()
            
            self.logger.info("✅ AI decision optimization completed")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ AI optimization failed: {e}")
            return {
                'optimized_text': decision_text,
                'improvements': [],
                'confidence': 0.5,
                'ai_optimized': False,
                'error': str(e)
            }
    
    def find_similar_decisions(self, decision_text: str, 
                             existing_decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        AI-powered similarity detection for duplicate prevention
        
        Args:
            decision_text: New decision to check
            existing_decisions: List of existing decisions to compare against
            
        Returns:
            List of similar decisions with similarity scores
        """
        if not self.enable_ai or not existing_decisions:
            return []
        
        try:
            # Prepare existing decisions for comparison
            decision_texts = [
                f"ID: {d.get('id', 'unknown')}\nText: {d.get('decision', d.get('text', ''))}"
                for d in existing_decisions[:20]  # Limit to prevent token overflow
            ]
            
            prompt = f"""
            Find decisions similar to this new decision:
            
            New Decision: {decision_text}
            
            Existing Decisions:
            {chr(10).join(decision_texts)}
            
            Please provide a JSON response with:
            {{
                "similar_decisions": [
                    {{
                        "id": "decision_id",
                        "similarity_score": 0.0-1.0,
                        "reason": "why they are similar",
                        "overlap_type": "duplicate|related|complementary"
                    }}
                ]
            }}
            
            Only include decisions with similarity_score > 0.6
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing architectural decisions for similarities and duplicates. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=600,
                temperature=0.2
            )
            
            result = json.loads(response.choices[0].message.content)
            similar_decisions = result.get('similar_decisions', [])
            
            self.logger.info(f"✅ Found {len(similar_decisions)} similar decisions")
            return similar_decisions
            
        except Exception as e:
            self.logger.error(f"❌ Similarity detection failed: {e}")
            return []
    
    def generate_decision_insights(self, decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate AI-powered insights from decision collection
        
        Args:
            decisions: List of decisions to analyze
            
        Returns:
            Insights report with patterns, trends, and recommendations
        """
        if not self.enable_ai or not decisions:
            return self._fallback_insights(decisions)
        
        try:
            # Prepare decision summary for analysis
            decision_summary = []
            for i, decision in enumerate(decisions[:50]):  # Limit to prevent token overflow
                summary = {
                    'id': decision.get('id', f'decision_{i}'),
                    'type': decision.get('type', 'unknown'),
                    'text': decision.get('decision', decision.get('text', ''))[:200]  # Truncate
                }
                decision_summary.append(summary)
            
            prompt = f"""
            Analyze these architectural decisions and provide insights:
            
            Decisions Summary: {json.dumps(decision_summary, indent=2)}
            
            Please provide a JSON response with:
            {{
                "total_decisions": {len(decisions)},
                "decision_patterns": [
                    {{
                        "pattern": "pattern description",
                        "frequency": "how often it appears",
                        "impact": "potential impact"
                    }}
                ],
                "technology_trends": ["list of technology trends identified"],
                "risk_areas": ["potential risk areas"],
                "recommendations": [
                    {{
                        "area": "area of improvement",
                        "suggestion": "specific suggestion",
                        "priority": "high|medium|low"
                    }}
                ],
                "decision_velocity": "assessment of decision-making pace",
                "complexity_assessment": "overall complexity assessment"
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert enterprise architect analyzing decision patterns and trends. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=1000,
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            result['ai_generated'] = True
            result['analysis_timestamp'] = datetime.now(timezone.utc).isoformat()
            result['model_used'] = self.model
            
            self.logger.info("✅ AI insights generation completed")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Insights generation failed: {e}")
            return self._fallback_insights(decisions)
    
    def _fallback_insights(self, decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate basic insights without AI"""
        types = {}
        total = len(decisions)
        
        for decision in decisions:
            decision_type = decision.get('type', 'unknown')
            types[decision_type] = types.get(decision_type, 0) + 1
        
        return {
            'total_decisions': total,
            'decision_patterns': [
                {
                    'pattern': f'{decision_type} decisions',
                    'frequency': f'{count}/{total} ({count/total*100:.1f}%)',
                    'impact': 'Standard impact'
                }
                for decision_type, count in types.items()
            ],
            'technology_trends': ['Pattern analysis not available'],
            'risk_areas': ['Risk analysis not available'],
            'recommendations': [
                {
                    'area': 'AI Enhancement',
                    'suggestion': 'Consider enabling AI features for deeper insights',
                    'priority': 'medium'
                }
            ],
            'decision_velocity': 'Analysis not available',
            'complexity_assessment': 'Analysis not available',
            'ai_generated': False,
            'analysis_timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def create_decision_report(self, decisions: List[Dict[str, Any]], 
                             save_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Create comprehensive decision analysis report
        
        Args:
            decisions: List of decisions to analyze
            save_path: Optional path to save report
            
        Returns:
            Comprehensive report with all analysis results
        """
        self.logger.info(f"🔍 Generating comprehensive report for {len(decisions)} decisions")
        
        report = {
            'metadata': {
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'total_decisions': len(decisions),
                'ai_enhanced': self.enable_ai,
                'security_enabled': SECURITY_AVAILABLE
            },
            'insights': self.generate_decision_insights(decisions),
            'classifications': {},
            'optimizations': {},
            'duplicates': []
        }
        
        # Analyze each decision individually (limit to prevent resource exhaustion)
        for i, decision in enumerate(decisions[:10]):  # Limit for performance
            decision_id = decision.get('id', f'decision_{i}')
            decision_text = decision.get('decision', decision.get('text', ''))
            
            if decision_text:
                # Classify decision
                classification = self.classify_decision(decision_text)
                report['classifications'][decision_id] = classification
                
                # Optimize decision text
                optimization = self.optimize_decision_text(decision_text)
                report['optimizations'][decision_id] = optimization
        
        # Find potential duplicates
        if len(decisions) > 1:
            for i, decision in enumerate(decisions[:5]):  # Limit for performance
                decision_text = decision.get('decision', decision.get('text', ''))
                if decision_text:
                    similar = self.find_similar_decisions(decision_text, decisions[i+1:])
                    if similar:
                        report['duplicates'].append({
                            'base_decision': decision.get('id', f'decision_{i}'),
                            'similar_decisions': similar
                        })
        
        # Save report if path provided
        if save_path:
            try:
                if self.secure_manager:
                    success = self.secure_manager.secure_json_write(
                        report, save_path, sanitize=True, backup=True
                    )
                    if success:
                        self.logger.info(f"✅ Report saved securely: {save_path}")
                else:
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(save_path, 'w') as f:
                        json.dump(report, f, indent=2, ensure_ascii=False)
                    self.logger.info(f"✅ Report saved: {save_path}")
            except Exception as e:
                self.logger.error(f"❌ Failed to save report: {e}")
        
        self.logger.info("✅ Comprehensive report generation completed")
        return report

def setup_ai_logging():
    """Setup logging for AI memory bridge"""
    os.makedirs("logs/ai", exist_ok=True)
    
    logger = logging.getLogger('ai_memory_bridge')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # File handler for AI logs
        file_handler = logging.FileHandler('logs/ai/memory_bridge.log')
        file_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
    
    return logger

# Initialize AI logging
setup_ai_logging()

def main():
    """Demo/test function for the AI Memory Bridge"""
    bridge = AIEnhancedMemoryBridge()
    
    # Test decision
    test_decision = """
    We will use PostgreSQL as our primary database for the architect decisions storage.
    This decision is based on ACID compliance requirements and the need for complex queries.
    """
    
    print("🤖 AI Memory Bridge Demo")
    print("=" * 50)
    
    # Test classification
    print("\n📊 Decision Classification:")
    classification = bridge.classify_decision(test_decision)
    print(f"Type: {classification['type']}")
    print(f"Priority: {classification['priority']}")
    print(f"Category: {classification['category']}")
    
    # Test optimization
    print("\n✨ Decision Optimization:")
    optimization = bridge.optimize_decision_text(test_decision)
    if optimization['ai_optimized']:
        print("Optimized text:")
        print(optimization['optimized_text'])
    else:
        print("AI optimization not available")
    
    print("=" * 50)

if __name__ == "__main__":
    main()