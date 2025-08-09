"""
Angles OS™ Decision Management
CRUD operations and recommendation system for decisions
"""
import json
import uuid
from typing import List, Dict, Any, Optional
from api.deps import get_db_cursor
from api.utils.logging import logger
from api.utils.time import utc_now

class DecisionService:
    """Decision tracking and recommendation system"""
    
    def __init__(self):
        self.table = 'decisions'
    
    def create_decision(self, topic: str, options: List[Dict[str, Any]]) -> str:
        """Create a new decision"""
        decision_id = str(uuid.uuid4())
        
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO decisions (id, topic, options, status, created_at, updated_at)
                    VALUES (%s, %s, %s, 'open', %s, %s)
                """, (decision_id, topic, json.dumps(options), utc_now(), utc_now()))
                
            logger.info(f"Created decision: {topic}")
            return decision_id
            
        except Exception as e:
            logger.error(f"Failed to create decision: {e}")
            raise
    
    def list_decisions(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List decisions with optional status filter"""
        try:
            with get_db_cursor() as cursor:
                if status:
                    cursor.execute("""
                        SELECT id, topic, options, chosen, rationale, status, created_at, updated_at
                        FROM decisions 
                        WHERE status = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (status, limit))
                else:
                    cursor.execute("""
                        SELECT id, topic, options, chosen, rationale, status, created_at, updated_at
                        FROM decisions 
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (limit,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'id': str(row[0]),
                        'topic': row[1],
                        'options': row[2] if isinstance(row[2], list) else (json.loads(row[2]) if row[2] else []),
                        'chosen': row[3],
                        'rationale': row[4],
                        'status': row[5],
                        'created_at': row[6].isoformat(),
                        'updated_at': row[7].isoformat() if row[7] else None
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to list decisions: {e}")
            return []
    
    def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific decision by ID"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT id, topic, options, chosen, rationale, status, created_at, updated_at
                    FROM decisions 
                    WHERE id = %s
                """, (decision_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return {
                    'id': str(row[0]),
                    'topic': row[1],
                    'options': row[2] if isinstance(row[2], list) else (json.loads(row[2]) if row[2] else []),
                    'chosen': row[3],
                    'rationale': row[4],
                    'status': row[5],
                    'created_at': row[6].isoformat(),
                    'updated_at': row[7].isoformat() if row[7] else None
                }
                
        except Exception as e:
            logger.error(f"Failed to get decision {decision_id}: {e}")
            return None
    
    def recommend(self, decision_id: str, rationale: Optional[str] = None) -> Dict[str, Any]:
        """Generate recommendation for a decision"""
        decision = self.get_decision(decision_id)
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")
        
        options = decision['options']
        if not options:
            raise ValueError("No options available for recommendation")
        
        # Simple heuristic: choose option with best pros/cons ratio
        best_option = None
        best_score = -999
        
        for option in options:
            pros = len(option.get('pros', []))
            cons = len(option.get('cons', []))
            score = pros - cons
            
            if score > best_score:
                best_score = score
                best_option = option['option']
        
        # Generate default rationale if none provided
        if not rationale:
            rationale = f"Recommended based on analysis: {best_option} has the best pros/cons ratio (score: {best_score})"
        
        # Update decision in database
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    UPDATE decisions 
                    SET chosen = %s, rationale = %s, status = 'recommended', updated_at = %s
                    WHERE id = %s
                """, (best_option, rationale, utc_now(), decision_id))
                
            logger.info(f"Generated recommendation for {decision_id}: {best_option}")
            return {
                'decision_id': decision_id,
                'chosen': best_option,
                'rationale': rationale,
                'status': 'recommended'
            }
            
        except Exception as e:
            logger.error(f"Failed to save recommendation: {e}")
            raise
    
    def approve(self, decision_id: str) -> Dict[str, Any]:
        """Approve a decision"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    UPDATE decisions 
                    SET status = 'approved', updated_at = %s
                    WHERE id = %s
                """, (utc_now(), decision_id))
                
                if cursor.rowcount == 0:
                    raise ValueError(f"Decision {decision_id} not found")
                
            logger.info(f"Approved decision {decision_id}")
            return {'decision_id': decision_id, 'status': 'approved'}
            
        except Exception as e:
            logger.error(f"Failed to approve decision: {e}")
            raise
    
    def decline(self, decision_id: str, rationale: Optional[str] = None) -> Dict[str, Any]:
        """Decline a decision"""
        try:
            with get_db_cursor() as cursor:
                update_fields = ['status = %s', 'updated_at = %s']
                values = ['declined', utc_now()]
                
                if rationale:
                    update_fields.append('rationale = %s')
                    values.append(rationale)
                
                values.append(decision_id)
                
                cursor.execute(f"""
                    UPDATE decisions 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                """, values)
                
                if cursor.rowcount == 0:
                    raise ValueError(f"Decision {decision_id} not found")
                
            logger.info(f"Declined decision {decision_id}")
            return {'decision_id': decision_id, 'status': 'declined'}
            
        except Exception as e:
            logger.error(f"Failed to decline decision: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get decision statistics"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM decisions")
                total = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM decisions 
                    GROUP BY status
                """)
                by_status = {row[0]: row[1] for row in cursor.fetchall()}
                
                return {
                    'total_decisions': total,
                    'by_status': by_status
                }
                
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'total_decisions': 0, 'by_status': {}}