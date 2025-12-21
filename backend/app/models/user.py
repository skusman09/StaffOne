from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base
from app.core.config import settings


class Role(str, enum.Enum):
    """User roles enum."""
    ADMIN = "admin"
    EMPLOYEE = "employee"


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(SQLEnum(Role), default=Role.EMPLOYEE, nullable=False)
    is_active = Column(Boolean, default=True)
    timezone = Column(String, default=settings.DEFAULT_TIMEZONE, nullable=False)  # User's timezone
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with check-in/out records
    # Relationship with check-in/out records
    checkinouts = relationship("CheckInOut", back_populates="user", cascade="all, delete-orphan", foreign_keys="[CheckInOut.user_id]")


