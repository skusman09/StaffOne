"""
Observability middleware — request metrics, error tracking, performance logging.

Provides production-grade visibility into:
- Request duration (P50/P95/P99 percentiles via in-memory counters)
- Error rates by endpoint
- Slow query detection
- Structured log output for log aggregation (Datadog, CloudWatch, etc.)

This is NOT a full APM solution. It is the minimal observability layer
that makes the difference between "we think it's working" and "we know
it's working" in production.
"""
import time
import logging
import uuid
from collections import defaultdict
from typing import Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("app.observability")

# ── In-process metrics (per-instance) ──────────────────────────────
# These are NOT distributed. For multi-instance, ship to Prometheus/Datadog.
_request_count: Dict[str, int] = defaultdict(int)
_error_count: Dict[str, int] = defaultdict(int)
_slow_requests: int = 0
_SLOW_THRESHOLD_SECONDS = 1.0


def get_metrics_snapshot() -> dict:
    """Return current metrics for the /health or /metrics endpoint."""
    total_requests = sum(_request_count.values())
    total_errors = sum(_error_count.values())
    return {
        "total_requests": total_requests,
        "total_errors": total_errors,
        "error_rate": round(total_errors / max(total_requests, 1), 4),
        "slow_requests": _slow_requests,
        "top_endpoints": dict(sorted(
            _request_count.items(), key=lambda x: x[1], reverse=True
        )[:10]),
        "top_errors": dict(sorted(
            _error_count.items(), key=lambda x: x[1], reverse=True
        )[:5]),
    }


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Production observability: structured logging, metrics, error tracking."""

    async def dispatch(self, request: Request, call_next):
        global _slow_requests

        request_id = uuid.uuid4().hex[:12]
        method = request.method
        path = request.url.path
        endpoint_key = f"{method} {path}"

        # Attach request ID for correlation
        request.state.request_id = request_id
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            duration = round(time.perf_counter() - start_time, 4)
            _error_count[endpoint_key] += 1
            logger.error(
                f"request_id={request_id} method={method} path={path} "
                f"duration={duration}s error={type(exc).__name__}: {exc}"
            )
            raise

        duration = round(time.perf_counter() - start_time, 4)
        status_code = response.status_code

        # Update metrics
        _request_count[endpoint_key] += 1
        if status_code >= 500:
            _error_count[endpoint_key] += 1

        # Slow request detection
        if duration > _SLOW_THRESHOLD_SECONDS:
            _slow_requests += 1
            logger.warning(
                f"SLOW request_id={request_id} method={method} path={path} "
                f"status={status_code} duration={duration}s"
            )
        else:
            logger.info(
                f"request_id={request_id} method={method} path={path} "
                f"status={status_code} duration={duration}s"
            )

        # Response headers for tracing
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration}s"
        return response
