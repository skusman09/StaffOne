import logging
from typing import Optional

import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis Connection Pool
redis_pool: Optional[redis.ConnectionPool] = None

def init_redis_pool():
    """Initialize Redis connection pool if configured."""
    global redis_pool
    if settings.REDIS_URL:
        try:
            redis_pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                max_connections=settings.REDIS_MAX_CONNECTIONS
            )
            # Test connection
            client = redis.Redis(connection_pool=redis_pool)
            client.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis at {settings.REDIS_URL}: {e}")
            redis_pool = None
    else:
        logger.info("REDIS_URL not configured. Running in fallback mode.")


def get_redis_client() -> Optional[redis.Redis]:
    """Get a Redis client from the pool. Returns None if Redis is unavailable."""
    if redis_pool is None:
        return None
    try:
        return redis.Redis(connection_pool=redis_pool)
    except Exception as e:
        logger.error(f"Error getting Redis client: {e}")
        return None
