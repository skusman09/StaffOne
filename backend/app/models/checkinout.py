from sqlalchemy import Column, Integer, DateTime, String, Float, ForeignKey, Boolean, Enum as SQLEnum, TypeDecorator, Index
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


class SafeShiftType(TypeDecorator):
    """Robust ShiftType handler that gracefully handles case-insensitivity from DB."""
    impl = String
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # Try to match case-insensitively
        try:
            return ShiftType(value.lower())
        except ValueError:
            # Fallback for unexpected values
            return ShiftType.REGULAR

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, ShiftType):
            return value.value
        return str(value).lower()


class CheckInOut(Base):
    """Check-in/Check-out model for attendance tracking."""
    __tablename__ = "checkinouts"
    __table_args__ = (
        Index("ix_checkinouts_user_checkin", "user_id", "check_in_time"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    check_in_time = Column(DateTime, nullable=False, index=True)
    check_out_time = Column(DateTime, nullable=True)
    
    # Shift tracking - using robust TypeDecorator
    shift_type = Column(SafeShiftType(), default=ShiftType.REGULAR, nullable=False)
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
    
    # Late arrival / Early exit tracking
    is_late_arrival = Column(Boolean, default=False, nullable=False)
    late_minutes = Column(Integer, default=0, nullable=False)  # Minutes late beyond grace
    is_early_exit = Column(Boolean, default=False, nullable=False)
    early_exit_minutes = Column(Integer, default=0, nullable=False)  # Minutes before expected end
    
    # Admin controls
    is_auto_checkout = Column(Boolean, default=False, nullable=False)  # System auto-closed
    admin_notes = Column(String, nullable=True)  # Admin remarks
    modified_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with user
    user = relationship("User", back_populates="checkinouts", foreign_keys=[user_id])


