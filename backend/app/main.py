from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.core.config import settings
from app.routes import auth, attendance, admin, locations, leaves, notifications, analytics, reports, holidays, payroll, config, audit, scheduler, department, compoff
from app.database import Base, engine

# Create database tables on startup (only if using SQLite or for development)
# For production with PostgreSQL, use Alembic migrations instead
# This ensures tables exist for development/testing
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    # If tables already exist or migration system is used, this is fine
    # Log but don't fail startup
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not create tables automatically: {e}")
    logger.info("If using Alembic migrations, this is expected. Run 'alembic upgrade head' to create tables.")

# Create FastAPI app
app = FastAPI(
    title="Check-In/Check-Out API",
    description="Attendance tracking system API",
    version="1.0.0"
)

# Custom OpenAPI schema to add Bearer and Basic Auth support
def custom_openapi():
    # Force regeneration by clearing cache
    app.openapi_schema = None
    
    openapi_schema = get_openapi(
        title="Check-In/Check-Out API",
        version="1.0.0",
        description="Attendance tracking system API",
        routes=app.routes,
    )
    
    # Ensure components exist
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    # Add both Bearer and Basic Auth security schemes
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
    
    # List of public endpoints that don't require authentication
    public_endpoints = ["/", "/health", "/auth/login", "/auth/register"]
    
    # Set security for protected endpoints
    for path, path_item in openapi_schema.get("paths", {}).items():
        # Skip public endpoints
        if any(path == public or path.startswith(public + "/") for public in public_endpoints):
            continue
            
        for method, operation in path_item.items():
            if method.lower() in ["get", "post", "put", "delete", "patch"]:
                # For /auth/me, use Bearer token (preferred)
                if path == "/auth/me":
                    operation["security"] = [{"BearerAuth": []}]
                else:
                    # For other endpoints, allow both Bearer and Basic Auth
                    operation["security"] = [{"BearerAuth": []}, {"BasicAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(attendance.router)
app.include_router(admin.router)
app.include_router(locations.router)
app.include_router(leaves.router)
app.include_router(notifications.router)
app.include_router(analytics.router)
app.include_router(reports.router)
app.include_router(holidays.router)
app.include_router(payroll.router)
app.include_router(config.router)
app.include_router(audit.router)
app.include_router(scheduler.router)
app.include_router(department.router)
app.include_router(compoff.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Check-In/Check-Out API",
        "version": "2.0.0",
        "features": ["Timezone support", "Shift management", "Geofencing", "Working hours", "Admin controls", "Leave management", "Background scheduler"],
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    from app.core.scheduler import get_scheduler_status
    scheduler_status = get_scheduler_status()
    return {
        "status": "healthy",
        "scheduler": scheduler_status
    }


@app.on_event("startup")
def startup_event():
    """Initialize background scheduler on startup."""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        from app.core.scheduler import init_scheduler
        init_scheduler()
        logger.info("Background scheduler initialized successfully")
    except Exception as e:
        logger.warning(f"Could not initialize scheduler: {e}")


@app.on_event("shutdown")
def shutdown_event():
    """Shutdown scheduler gracefully."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from app.core.scheduler import shutdown_scheduler
        shutdown_scheduler()
        logger.info("Background scheduler shutdown complete")
    except Exception as e:
        logger.warning(f"Error shutting down scheduler: {e}")
