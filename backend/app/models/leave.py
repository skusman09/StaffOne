from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime, date
import enum
from app.database import Base


class LeaveType(str, enum.Enum):
    """Types of leave."""
    ANNUAL = "annual"  # Annual/vacation leave
    SICK = "sick"  # Sick leave
    CASUAL = "casual"  # Casual leave
    UNPAID = "unpaid"  # Unpaid leave
    MATERNITY = "maternity"  # Maternity leave
    PATERNITY = "paternity"  # Paternity leave
    BEREAVEMENT = "bereavement"  # Bereavement leave
    OTHER = "other"  # Other types


class LeaveStatus(str, enum.Enum):
    """Status of leave request."""
    PENDING = "pending"  # Awaiting approval
    APPROVED = "approved"  # Approved by admin
    REJECTED = "rejected"  # Rejected by admin
    CANCELLED = "cancelled"  # Cancelled by employee


class Leave(Base):
    """Leave request model."""
    __tablename__ = "leaves"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Leave details
    leave_type = Column(SQLEnum(LeaveType), nullable=False)
    status = Column(SQLEnum(LeaveStatus), default=LeaveStatus.PENDING, nullable=False)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False)
    
    # Reason and remarks
    reason = Column(Text, nullable=True)  # Employee's reason
    admin_remarks = Column(Text, nullable=True)  # Admin's remarks
    
    # Approval tracking
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="leaves")
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    
    @property
    def days_count(self) -> int:
        """Calculate number of leave days."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
