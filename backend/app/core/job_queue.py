"""
Background job queue — Redis Queue (RQ) based job processing.

Replaces APScheduler's in-process model with a durable, distributed queue.

Architecture:
- Jobs are enqueued from the web process into Redis
- A separate RQ worker process picks them up (rq worker staffone)
- If the web process crashes, pending jobs survive in Redis
- If a job fails, it goes to the failed queue for inspection

For development without Redis, falls back to synchronous execution.
"""
import logging
from typing import Optional, Callable, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# Lazy-initialized queue
_queue = None
_sync_mode = False


def init_job_queue():
    """Initialize the RQ job queue. Called during app startup."""
    global _queue, _sync_mode

    if not settings.REDIS_URL:
        logger.warning("REDIS_URL not configured — background jobs will run synchronously")
        _sync_mode = True
        return

    try:
        import redis
        from rq import Queue

        conn = redis.from_url(settings.REDIS_URL)
        conn.ping()
        _queue = Queue("staffone", connection=conn)
        _sync_mode = False
        logger.info(f"RQ job queue initialized (Redis: {settings.REDIS_URL})")
    except Exception as e:
        if settings.is_production:
            raise RuntimeError(
                f"FATAL: Cannot connect to Redis for job queue: {e}. "
                f"Redis is required in production."
            ) from e
        logger.warning(f"Redis unavailable for job queue: {e}. Falling back to sync mode.")
        _sync_mode = True


def enqueue(func: Callable, *args: Any, **kwargs: Any) -> Optional[str]:
    """Enqueue a background job.

    In production (Redis available): enqueues to RQ for async processing.
    In development (no Redis): executes synchronously as a fallback.

    Returns the job ID if enqueued, None if executed synchronously.
    """
    if _sync_mode or _queue is None:
        # Synchronous fallback — execute immediately
        try:
            func(*args, **kwargs)
            logger.debug(f"Job {func.__name__} executed synchronously")
        except Exception as e:
            logger.error(f"Sync job {func.__name__} failed: {e}")
        return None

    try:
        job = _queue.enqueue(func, *args, **kwargs)
        logger.info(f"Job {func.__name__} enqueued (id={job.id})")
        return job.id
    except Exception as e:
        logger.error(f"Failed to enqueue {func.__name__}: {e}. Executing synchronously.")
        try:
            func(*args, **kwargs)
        except Exception as inner:
            logger.error(f"Fallback sync execution of {func.__name__} also failed: {inner}")
        return None


def get_queue_status() -> dict:
    """Get current queue health for the /health endpoint."""
    if _sync_mode or _queue is None:
        return {"mode": "sync", "reason": "Redis unavailable"}

    try:
        return {
            "mode": "async",
            "queued": len(_queue),
            "failed": len(_queue.failed_job_registry),
            "workers": len([w for w in _queue.connection.client_list() if b"rq:worker" in w.get(b"name", b"")]) if hasattr(_queue, 'connection') else "unknown",
        }
    except Exception as e:
        return {"mode": "async", "error": str(e)}
