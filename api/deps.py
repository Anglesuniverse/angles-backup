"""
Angles OS™ Dependency Injection
FastAPI dependencies for database connections and services
"""
import psycopg2
import redis
from contextlib import contextmanager
from api.config import settings
from api.utils.logging import logger

# Database connection pool (simplified for Replit)
_db_connection = None
_redis_connection = None

def get_db_connection():
    """Get PostgreSQL database connection"""
    global _db_connection
    
    if not _db_connection or _db_connection.closed:
        try:
            _db_connection = psycopg2.connect(
                settings.postgres_url,
                application_name='angles-os-api'
            )
            _db_connection.autocommit = True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    return _db_connection

def get_redis_connection():
    """Get Redis connection"""
    global _redis_connection
    
    if not _redis_connection:
        try:
            _redis_connection = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            _redis_connection.ping()
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            _redis_connection = None
    
    return _redis_connection

@contextmanager
def get_db_cursor():
    """Context manager for database operations"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yield cursor
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()