"""
RQ Worker entry point for StaffOne background jobs.

Usage:
    # Start a single worker (development)
    cd backend
    .venv/Scripts/python worker.py

    # Start a worker via rq CLI (production)
    cd backend
    rq worker staffone --url redis://localhost:6379

    # Start with logging  
    rq worker staffone --url redis://localhost:6379 --verbose

The worker will:
1. Connect to Redis
2. Listen on the 'staffone' queue
3. Execute jobs defined in app/core/jobs.py
4. Failed jobs go to the 'failed' registry for inspection

To inspect failed jobs:
    rq info --url redis://localhost:6379
"""
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("worker")


def main():
    from app.core.config import settings

    if not settings.REDIS_URL:
        logger.error("REDIS_URL not configured. Cannot start worker.")
        sys.exit(1)

    try:
        import redis
        from rq import Worker, Queue

        conn = redis.from_url(settings.REDIS_URL)
        conn.ping()
        logger.info(f"Connected to Redis: {settings.REDIS_URL}")

        queue = Queue("staffone", connection=conn)
        worker = Worker([queue], connection=conn, name="staffone-worker")

        logger.info("StaffOne RQ worker starting...")
        logger.info("Listening on queue: staffone")
        logger.info("Press Ctrl+C to stop")

        worker.work(with_scheduler=False)

    except redis.exceptions.ConnectionError as e:
        logger.error(f"Cannot connect to Redis: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
