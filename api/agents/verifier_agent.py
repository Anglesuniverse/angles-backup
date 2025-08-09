"""
Angles OS™ Verifier Agent
Validates system integrity and critical invariants
"""
import time
import requests
from typing import Dict, Any, List
from api.deps import get_db_connection, get_redis_connection
from api.services.supabase_connector import SupabaseConnector
from api.services.notion_connector import NotionConnector
from api.utils.logging import logger
from api.config import settings
from api.deps import get_db_cursor

class VerifierAgent:
    """Agent for verifying system integrity and health"""
    
    def __init__(self):
        self.name = "verifier_agent"
        self.supabase = SupabaseConnector()
        self.notion = NotionConnector()
        
        # Critical invariants to check
        self.required_tables = ['vault_chunks', 'decisions', 'agent_logs']
        self.required_indexes = [
            'idx_vault_chunks_source',
            'idx_decisions_status',
            'idx_agent_logs_agent'
        ]
        
    def verify_database_schema(self) -> Dict[str, Any]:
        """Verify database schema integrity"""
        results = {
            'status': 'healthy',
            'tables': {},
            'indexes': {},
            'issues': []
        }
        
        try:
            with get_db_cursor() as cursor:
                # Check required tables exist
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = ANY(%s)
                """, (self.required_tables,))
                
                existing_tables = {row[0] for row in cursor.fetchall()}
                missing_tables = set(self.required_tables) - existing_tables
                
                for table in self.required_tables:
                    results['tables'][table] = table in existing_tables
                
                if missing_tables:
                    results['status'] = 'critical'
                    results['issues'].extend([f"Missing table: {t}" for t in missing_tables])
                
                # Check required indexes exist
                cursor.execute("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE schemaname = 'public' 
                    AND indexname = ANY(%s)
                """, (self.required_indexes,))
                
                existing_indexes = {row[0] for row in cursor.fetchall()}
                missing_indexes = set(self.required_indexes) - existing_indexes
                
                for index in self.required_indexes:
                    results['indexes'][index] = index in existing_indexes
                
                if missing_indexes:
                    results['status'] = 'warning'
                    results['issues'].extend([f"Missing index: {i}" for i in missing_indexes])
                
                # Check table row counts
                for table in existing_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    results['tables'][f"{table}_count"] = count
        
        except Exception as e:
            results['status'] = 'error'
            results['issues'].append(f"Schema verification failed: {e}")
            logger.error(f"Database schema verification failed: {e}")
        
        return results
    
    def verify_api_endpoints(self) -> Dict[str, Any]:
        """Verify critical API endpoints are responding"""
        results = {
            'status': 'healthy',
            'endpoints': {},
            'issues': []
        }
        
        # Test endpoints (assuming running on localhost)
        test_endpoints = [
            ('health', 'http://localhost:8000/health'),
            ('vault_stats', 'http://localhost:8000/vault/stats'),
            ('decision_stats', 'http://localhost:8000/decisions/stats'),
            ('ui_summary', 'http://localhost:8000/ui/summary')
        ]
        
        for name, url in test_endpoints:
            try:
                response = requests.get(url, timeout=5)
                results['endpoints'][name] = {
                    'status_code': response.status_code,
                    'response_time_ms': int(response.elapsed.total_seconds() * 1000),
                    'healthy': response.status_code == 200
                }
                
                if response.status_code != 200:
                    results['status'] = 'warning'
                    results['issues'].append(f"Endpoint {name} returned {response.status_code}")
                    
            except Exception as e:
                results['endpoints'][name] = {
                    'status_code': None,
                    'response_time_ms': None,
                    'healthy': False,
                    'error': str(e)
                }
                results['status'] = 'critical'
                results['issues'].append(f"Endpoint {name} unreachable: {e}")
        
        return results
    
    def verify_external_services(self) -> Dict[str, Any]:
        """Verify external service connections"""
        results = {
            'status': 'healthy',
            'services': {},
            'issues': []
        }
        
        # Database connectivity
        try:
            db_conn = get_db_connection()
            cursor = db_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            results['services']['database'] = {'status': 'healthy'}
        except Exception as e:
            results['services']['database'] = {'status': 'error', 'error': str(e)}
            results['status'] = 'critical'
            results['issues'].append(f"Database connectivity failed: {e}")
        
        # Redis connectivity
        try:
            redis_conn = get_redis_connection()
            if redis_conn:
                redis_conn.ping()
                results['services']['redis'] = {'status': 'healthy'}
            else:
                results['services']['redis'] = {'status': 'unavailable'}
        except Exception as e:
            results['services']['redis'] = {'status': 'error', 'error': str(e)}
            results['issues'].append(f"Redis connectivity failed: {e}")
        
        # Supabase connectivity
        if self.supabase.is_available():
            supabase_health = self.supabase.health_check()
            results['services']['supabase'] = supabase_health
            if supabase_health.get('status') != 'healthy':
                results['issues'].append("Supabase connectivity issues")
        else:
            results['services']['supabase'] = {'status': 'not_configured'}
        
        # Notion connectivity
        if self.notion.is_available():
            notion_health = self.notion.test_connection()
            results['services']['notion'] = notion_health
            if notion_health.get('status') != 'healthy':
                results['issues'].append("Notion connectivity issues")
        else:
            results['services']['notion'] = {'status': 'not_configured'}
        
        return results
    
    def verify_data_integrity(self) -> Dict[str, Any]:
        """Verify data integrity constraints"""
        results = {
            'status': 'healthy',
            'checks': {},
            'issues': []
        }
        
        try:
            with get_db_cursor() as cursor:
                # Check for orphaned data or constraint violations
                
                # Check for decisions with invalid status
                cursor.execute("""
                    SELECT COUNT(*) FROM decisions 
                    WHERE status NOT IN ('open', 'recommended', 'approved', 'declined')
                """)
                invalid_status_count = cursor.fetchone()[0]
                
                results['checks']['invalid_decision_status'] = {
                    'count': invalid_status_count,
                    'passed': invalid_status_count == 0
                }
                
                if invalid_status_count > 0:
                    results['status'] = 'warning'
                    results['issues'].append(f"Found {invalid_status_count} decisions with invalid status")
                
                # Check for empty vault chunks
                cursor.execute("""
                    SELECT COUNT(*) FROM vault_chunks 
                    WHERE chunk IS NULL OR chunk = ''
                """)
                empty_chunks_count = cursor.fetchone()[0]
                
                results['checks']['empty_vault_chunks'] = {
                    'count': empty_chunks_count,
                    'passed': empty_chunks_count == 0
                }
                
                if empty_chunks_count > 0:
                    results['status'] = 'warning'
                    results['issues'].append(f"Found {empty_chunks_count} empty vault chunks")
                
                # Check for recent agent errors
                cursor.execute("""
                    SELECT COUNT(*) FROM agent_logs 
                    WHERE level = 'ERROR' 
                    AND created_at > NOW() - INTERVAL '1 hour'
                """)
                recent_errors_count = cursor.fetchone()[0]
                
                results['checks']['recent_agent_errors'] = {
                    'count': recent_errors_count,
                    'passed': recent_errors_count < 10  # Allow some errors
                }
                
                if recent_errors_count >= 10:
                    results['status'] = 'critical'
                    results['issues'].append(f"High error rate: {recent_errors_count} agent errors in last hour")
        
        except Exception as e:
            results['status'] = 'error'
            results['issues'].append(f"Data integrity check failed: {e}")
        
        return results
    
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
        """Execute verifier agent cycle"""
        start_time = time.time()
        
        try:
            logger.info("Starting verifier agent cycle")
            self.log_activity('INFO', 'Starting verifier agent cycle')
            
            # Run all verification checks
            schema_results = self.verify_database_schema()
            api_results = self.verify_api_endpoints()
            service_results = self.verify_external_services()
            integrity_results = self.verify_data_integrity()
            
            # Determine overall status
            all_results = [schema_results, api_results, service_results, integrity_results]
            overall_status = 'healthy'
            all_issues = []
            
            for result in all_results:
                if result['status'] == 'critical':
                    overall_status = 'critical'
                elif result['status'] in ['warning', 'error'] and overall_status != 'critical':
                    overall_status = 'warning'
                all_issues.extend(result.get('issues', []))
            
            duration = time.time() - start_time
            
            # Log results
            if overall_status == 'healthy':
                message = f"System verification complete: All checks passed in {duration:.2f}s"
                log_level = 'INFO'
            elif overall_status == 'warning':
                message = f"System verification complete: {len(all_issues)} warnings in {duration:.2f}s"
                log_level = 'WARNING'
            else:
                message = f"System verification complete: Critical issues found in {duration:.2f}s"
                log_level = 'ERROR'
            
            logger.info(message)
            self.log_activity(log_level, message, {
                'overall_status': overall_status,
                'duration': duration,
                'issues_count': len(all_issues),
                'issues': all_issues[:10],  # Limit to first 10 issues
                'schema': schema_results,
                'api': api_results,
                'services': service_results,
                'integrity': integrity_results
            })
            
        except Exception as e:
            logger.error(f"Verifier agent failed: {e}")
            self.log_activity('ERROR', f'Verifier agent failed: {e}')
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'name': self.name,
            'required_tables': self.required_tables,
            'required_indexes': self.required_indexes,
            'supabase_available': self.supabase.is_available(),
            'notion_available': self.notion.is_available()
        }