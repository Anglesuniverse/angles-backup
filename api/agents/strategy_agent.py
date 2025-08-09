"""
Angles OS™ Strategy Agent
Monitors open decisions and generates recommendations
"""
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from api.services.decisions import DecisionService
from api.services.openai_client import OpenAIClient
from api.utils.logging import logger
from api.deps import get_db_cursor

class StrategyAgent:
    """Agent for managing strategic decisions and recommendations"""
    
    def __init__(self):
        self.name = "strategy_agent"
        self.decision_service = DecisionService()
        self.openai = OpenAIClient()
        self.recommendation_threshold_hours = 2  # Recommend after 2 hours
        
    def get_stale_decisions(self) -> List[Dict[str, Any]]:
        """Get open decisions that need recommendations"""
        try:
            with get_db_cursor() as cursor:
                threshold_time = datetime.utcnow() - timedelta(hours=self.recommendation_threshold_hours)
                
                cursor.execute("""
                    SELECT id, topic, options, created_at
                    FROM decisions 
                    WHERE status = 'open' 
                    AND chosen IS NULL
                    AND created_at < %s
                    ORDER BY created_at ASC
                """, (threshold_time,))
                
                decisions = []
                for row in cursor.fetchall():
                    decisions.append({
                        'id': str(row[0]),
                        'topic': row[1],
                        'options': row[2],  # JSON already parsed by psycopg2
                        'created_at': row[3].isoformat()
                    })
                
                return decisions
                
        except Exception as e:
            logger.error(f"Failed to get stale decisions: {e}")
            return []
    
    def process_decision_recommendation(self, decision: Dict[str, Any]) -> bool:
        """Generate recommendation for a single decision"""
        decision_id = decision['id']
        
        try:
            logger.info(f"Generating recommendation for decision: {decision['topic']}")
            
            # Generate recommendation
            if self.openai.is_available():
                ai_result = self.openai.decide(decision['topic'], decision['options'])
                rationale = f"AI-generated recommendation: {ai_result['rationale']}"
            else:
                # Use service's heuristic method
                result = self.decision_service.recommend(decision_id)
                return True
            
            # Apply recommendation
            result = self.decision_service.recommend(decision_id, rationale)
            
            self.log_activity('INFO', f"Generated recommendation for '{decision['topic']}'", {
                'decision_id': decision_id,
                'chosen': result['chosen'],
                'method': 'ai' if self.openai.is_available() else 'heuristic'
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process recommendation for {decision_id}: {e}")
            self.log_activity('ERROR', f"Failed to process recommendation for {decision_id}: {e}")
            return False
    
    def analyze_decision_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in decision making"""
        try:
            with get_db_cursor() as cursor:
                # Get decision metrics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN status = 'open' THEN 1 END) as open_count,
                        COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count,
                        COUNT(CASE WHEN status = 'declined' THEN 1 END) as declined_count,
                        AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_decision_time
                    FROM decisions
                    WHERE created_at > NOW() - INTERVAL '30 days'
                """)
                
                row = cursor.fetchone()
                
                # Get top decision topics
                cursor.execute("""
                    SELECT topic, COUNT(*) as count
                    FROM decisions
                    WHERE created_at > NOW() - INTERVAL '30 days'
                    GROUP BY topic
                    ORDER BY count DESC
                    LIMIT 5
                """)
                
                top_topics = [{'topic': row[0], 'count': row[1]} for row in cursor.fetchall()]
                
                return {
                    'total_decisions_30d': row[0] or 0,
                    'open_decisions': row[1] or 0,
                    'approved_decisions': row[2] or 0,
                    'declined_decisions': row[3] or 0,
                    'avg_decision_time_hours': (row[4] or 0) / 3600,
                    'top_topics': top_topics
                }
                
        except Exception as e:
            logger.error(f"Failed to analyze decision patterns: {e}")
            return {}
    
    def log_activity(self, level: str, message: str, meta: Dict[str, Any] = None):
        """Log agent activity to database"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO agent_logs (agent, level, message, meta, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (self.name, level, message, meta or {}))
                
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
    
    def run(self):
        """Execute strategy agent cycle"""
        start_time = time.time()
        
        try:
            logger.info("Starting strategy agent cycle")
            self.log_activity('INFO', 'Starting strategy agent cycle')
            
            # Get decisions that need recommendations
            stale_decisions = self.get_stale_decisions()
            
            if not stale_decisions:
                logger.info("No decisions require recommendations")
                self.log_activity('INFO', 'No decisions require recommendations')
                return
            
            # Process recommendations
            processed = 0
            failed = 0
            
            for decision in stale_decisions:
                if self.process_decision_recommendation(decision):
                    processed += 1
                else:
                    failed += 1
            
            # Analyze patterns
            patterns = self.analyze_decision_patterns()
            
            duration = time.time() - start_time
            message = f"Strategy cycle complete: {processed} recommendations, {failed} failed in {duration:.2f}s"
            
            logger.info(message)
            self.log_activity('INFO', message, {
                'processed': processed,
                'failed': failed,
                'duration': duration,
                'stale_decisions': len(stale_decisions),
                'patterns': patterns
            })
            
        except Exception as e:
            logger.error(f"Strategy agent failed: {e}")
            self.log_activity('ERROR', f'Strategy agent failed: {e}')
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        stale_count = len(self.get_stale_decisions())
        patterns = self.analyze_decision_patterns()
        
        return {
            'name': self.name,
            'stale_decisions': stale_count,
            'recommendation_threshold_hours': self.recommendation_threshold_hours,
            'openai_available': self.openai.is_available(),
            'patterns': patterns
        }