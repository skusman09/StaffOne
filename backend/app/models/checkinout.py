from sqlalchemy import Column, Integer, DateTime, String, Float, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from app.database import Base


class ShiftType(str, enum.Enum):
    """Type of shift/check-in."""
    REGULAR = "regular"  # Normal work shift
    BREAK = "break"  # Break period
    OVERTIME = "overtime"  # Overtime work


class CheckInOut(Base):
    """Check-in/Check-out model for attendance tracking."""
    __tablename__ = "checkinouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    check_in_time = Column(DateTime, nullable=False, index=True)
    check_out_time = Column(DateTime, nullable=True)
    
    # Shift tracking
    shift_type = Column(SQLEnum(ShiftType), default=ShiftType.REGULAR, nullable=False)
    shift_id = Column(String, default=lambda: str(uuid.uuid4()), nullable=False)  # Groups related entries
    
    # Location data
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    checkout_latitude = Column(Float, nullable=True)  # Location at checkout
    checkout_longitude = Column(Float, nullable=True)
    device_info = Column(String, nullable=True)
    
    # Geofencing flags
    is_location_valid = Column(Boolean, default=True, nullable=False)  # True if within geofence
    location_flag_reason = Column(String, nullable=True)  # Reason if flagged
    
    # Working hours
    hours_worked = Column(Float, nullable=True)  # Calculated on checkout
    
    # Admin controls
    is_auto_checkout = Column(Boolean, default=False, nullable=False)  # System auto-closed
    admin_notes = Column(String, nullable=True)  # Admin remarks
    modified_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with user
    user = relationship("User", back_populates="checkinouts", foreign_keys=[user_id])


