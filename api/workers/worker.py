"""
Angles OS™ RQ Worker
Background job processing for scheduled tasks
"""
import os
import sys
from rq import Worker, Queue, Connection
from api.deps import get_redis_connection
from api.utils.logging import logger
from api.workers.jobs import ingest_rss, daily_backup, summarize_artifact

def main():
    """Main worker process"""
    try:
        # Connect to Redis
        redis_conn = get_redis_connection()
        if not redis_conn:
            logger.error("Redis connection not available")
            sys.exit(1)
        
        # Create queue
        queue = Queue('angles_os', connection=redis_conn)
        
        # Create worker
        worker = Worker([queue], connection=redis_conn, name=f'angles-worker-{os.getpid()}')
        
        logger.info(f"Starting Angles OS™ worker {worker.name}")
        worker.work()
        
    except KeyboardInterrupt:
        logger.info("Worker shutdown requested")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()