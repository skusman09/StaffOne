"""
StaffOne API — Main application entry point.

Uses FastAPI lifespan for startup/shutdown hooks.
Registers:
- Global exception handler
- Request logging middleware
- Rate limiting (slowapi)
- Structured logging
- API versioning under /api/v1
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.observability import ObservabilityMiddleware, get_metrics_snapshot
from app.core.exception_handlers import unhandled_exception_handler, validation_exception_handler
from app.core.rate_limiter import limiter
from app.database import Base, engine, check_db_connectivity
from app.routes import (
    auth, attendance, admin, locations, leaves, notifications,
    analytics, reports, holidays, payroll, config, audit,
    scheduler, department, compoff, pulse, onboarding
)

# ── Structured logging setup ───────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


# ── Lifespan (replaces deprecated @app.on_event) ──────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle management."""
    # ── 1. Database tables (dev only; production uses Alembic) ─────
    if not settings.is_production:
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as e:
            logger.warning(f"Could not create tables automatically: {e}")
    else:
        logger.info("Production mode — skipping auto table creation (use Alembic).")

    # ── 2. Redis + Job Queue ──────────────────────────────────────
    try:
        from app.core.job_queue import init_job_queue
        init_job_queue()
        logger.info("Job queue initialized")
    except Exception as e:
        if settings.is_production:
            logger.critical(f"FATAL: Job queue initialization failed: {e}")
            raise
        logger.warning(f"Job queue init failed (non-fatal in dev): {e}")

    # ── 3. APScheduler (legacy — still needed until full RQ migration) ─
    try:
        from app.core.scheduler import init_scheduler
        init_scheduler()
        logger.info("Background scheduler initialized")
    except Exception as e:
        logger.warning(f"Could not initialize scheduler: {e}")

    logger.info(f"StaffOne API started [env={settings.ENVIRONMENT}]")
    yield

    # ── Shutdown ──────────────────────────────────────────────────
    try:
        from app.core.scheduler import shutdown_scheduler
        shutdown_scheduler()
    except Exception as e:
        logger.warning(f"Error shutting down scheduler: {e}")

    logger.info("StaffOne API shutdown")


# ── App factory ────────────────────────────────────────────────────
app = FastAPI(
    title="StaffOne API",
    description="StaffOne HR Management System API",
    version="1.0.0",
    lifespan=lifespan
)

# ── Rate limiter ───────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Global exception handlers ─────────────────────────────────────
app.add_exception_handler(Exception, unhandled_exception_handler)

from fastapi.exceptions import RequestValidationError
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# ── Middleware ─────────────────────────────────────────────────────
app.add_middleware(ObservabilityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files ───────────────────────────────────────────────────
os.makedirs("uploads/avatars", exist_ok=True)
app.mount("/static/avatars", StaticFiles(directory="uploads/avatars"), name="static_avatars")

# ── All route modules ──────────────────────────────────────────────
_all_routers = [
    auth, attendance, admin, locations, leaves, notifications,
    analytics, reports, holidays, payroll, config, audit,
    scheduler, department, compoff, pulse, onboarding
]

# Register on root (backward compat — frontend uses /auth/login, /attendance/check-in etc.)
for module in _all_routers:
    app.include_router(module.router)

# Register under /api/v1 prefix for versioned API
v1_router = APIRouter(prefix="/api/v1")
for module in _all_routers:
    v1_router.include_router(module.router)
app.include_router(v1_router)


# ── Custom OpenAPI schema ──────────────────────────────────────────
def custom_openapi():
    app.openapi_schema = None

    openapi_schema = get_openapi(
        title="StaffOne API",
        version="1.0.0",
        description="StaffOne HR Management System API",
        routes=app.routes,
    )

    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token (get it from /auth/login)"
        },
        "BasicAuth": {
            "type": "http",
            "scheme": "basic",
            "description": "Enter your username and password"
        }
    }

    public_endpoints = ["/", "/health", "/auth/login", "/auth/register"]

    for path, path_item in openapi_schema.get("paths", {}).items():
        if any(path == public or path.startswith(public + "/") for public in public_endpoints):
            continue

        for method, operation in path_item.items():
            if method.lower() in ["get", "post", "put", "delete", "patch"]:
                if path == "/auth/me":
                    operation["security"] = [{"BearerAuth": []}]
                else:
                    operation["security"] = [{"BearerAuth": []}, {"BasicAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


# ── Root & Health endpoints ────────────────────────────────────────
@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "StaffOne API",
        "version": "2.0.0",
        "features": [
            "Timezone support", "Shift management", "Geofencing",
            "Working hours", "Admin controls", "Leave management",
            "Background scheduler"
        ],
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint with full system status."""
    from app.core.scheduler import get_scheduler_status
    from app.core.job_queue import get_queue_status

    db_status = check_db_connectivity()
    scheduler_status = get_scheduler_status()
    queue_status = get_queue_status()
    metrics = get_metrics_snapshot()

    overall = "healthy" if db_status["status"] == "connected" else "degraded"

    return {
        "status": overall,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "scheduler": scheduler_status,
        "job_queue": queue_status,
        "metrics": metrics,
    }
