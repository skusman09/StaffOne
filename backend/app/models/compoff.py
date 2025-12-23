from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class CompOffStatus(str, enum.Enum):
    """Status of comp-off request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    USED = "used"  # Used as leave


class CompOff(Base):
    """Compensatory Off - Converts overtime hours to leave days.
    
    Allows employees to request conversion of accumulated overtime
    hours into compensatory leave days.
    """
    __tablename__ = "comp_offs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Overtime hours being converted
    ot_hours = Column(Float, nullable=False)  # Hours being converted
    comp_off_days = Column(Float, nullable=False)  # Calculated days (e.g., 8 OT hours = 1 day)
    
    # Date range for OT accumulation
    ot_start_date = Column(DateTime, nullable=False)
    ot_end_date = Column(DateTime, nullable=False)
    
    # Request details
    status = Column(SQLEnum(CompOffStatus), default=CompOffStatus.PENDING, nullable=False)
    request_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    reason = Column(String, nullable=True)
    
    # Admin review
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_date = Column(DateTime, nullable=True)
    admin_remarks = Column(String, nullable=True)
    
    # If used, link to leave request
    leave_id = Column(Integer, ForeignKey("leaves.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="comp_offs")
    reviewer = relationship("User", foreign_keys=[reviewed_by_id])
    leave = relationship("Leave", foreign_keys=[leave_id])
