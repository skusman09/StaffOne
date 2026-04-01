"""
Request logging middleware — logs every request with method, path, status, and duration.
Adds X-Request-ID header to every response.
"""
import time
import uuid
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("app.middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every HTTP request and adds X-Request-ID header."""

    async def dispatch(self, request: Request, call_next):
        request_id = uuid.uuid4().hex[:8]
        start_time = time.time()

        response = await call_next(request)

        duration = round(time.time() - start_time, 3)
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} → {response.status_code} ({duration}s)"
        )

        response.headers["X-Request-ID"] = request_id
        return response
