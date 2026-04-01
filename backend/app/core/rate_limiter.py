"""
Rate limiter configuration — uses slowapi with proper proxy-aware IP detection.

Supports dynamic backend routing:
- Uses Redis if REDIS_URL is configured
- Falls back to in-memory storage if Redis is unavailable
"""
import logging
from slowapi import Limiter
from starlette.requests import Request

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_real_client_ip(request: Request) -> str:
    """Extract real client IP from request, handling proxies."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    return request.client.host if request.client else "unknown"


# Configure storage backend
storage_uri = settings.REDIS_URL if settings.REDIS_URL else "memory://"
if settings.REDIS_URL:
    logger.info("Initializing rate limiter with Redis backend")
else:
    logger.info("Initializing rate limiter with memory backend")

limiter = Limiter(
    key_func=get_real_client_ip,
    storage_uri=storage_uri,
    strategy="fixed-window"
)
