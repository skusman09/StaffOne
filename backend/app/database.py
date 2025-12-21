from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import re

# Create database engine
# Handle both SQLite and PostgreSQL connection strings
database_url = settings.DATABASE_URL

# For PostgreSQL, ensure proper connection args
connect_args = {}
if "sqlite" in database_url:
    connect_args = {"check_same_thread": False}
elif "postgresql" in database_url:
    # psycopg2 handles SSL via sslmode parameter in URL, which is already present
    # No additional connect_args needed for standard PostgreSQL connections
    pass

# Create engine
engine = create_engine(
    database_url,
    connect_args=connect_args,
    pool_pre_ping=True  # Verify connections before using them
)

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

