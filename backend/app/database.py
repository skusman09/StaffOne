"""
Database engine, session factory, and dependency injection.

Production features:
- Connection pool sizing for PostgreSQL (pool_size, max_overflow, pool_recycle)
- pool_pre_ping for stale connection detection
- check_db_connectivity() for health check endpoint
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Handle both SQLite and PostgreSQL connection strings
database_url = settings.DATABASE_URL

connect_args = {}
engine_kwargs = {"pool_pre_ping": True}

if "sqlite" in database_url:
    connect_args = {"check_same_thread": False}
elif "postgresql" in database_url:
    # Production pool settings for PostgreSQL
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": 30,
        "pool_recycle": 1800,  # Recycle connections every 30 minutes
    })

# Create engine
engine = create_engine(database_url, connect_args=connect_args, **engine_kwargs)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connectivity() -> dict:
    """Check database connectivity by executing SELECT 1. Used by /health endpoint."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "connected"}
    except Exception as e:
        logger.error(f"Database connectivity check failed: {e}")
        return {"status": "disconnected", "error": str(type(e).__name__)}
