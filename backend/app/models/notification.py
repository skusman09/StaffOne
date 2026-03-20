from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class NotificationType(str, enum.Enum):
    """Types of notifications."""
    FORGOT_CHECKIN = "forgot_checkin"
    FORGOT_CHECKOUT = "forgot_checkout"
    LEAVE_APPROVED = "leave_approved"
    LEAVE_REJECTED = "leave_rejected"
    LATE_ARRIVAL = "late_arrival"
    AUTO_CHECKOUT = "auto_checkout"
    GENERAL = "general"
    ONBOARDING_ASSIGNED = "onboarding_assigned"
    ONBOARDING_REMINDER = "onboarding_reminder"
    ONBOARDING_NOTE_ADDED = "onboarding_note_added"
    ONBOARDING_COMPLETED = "onboarding_completed"


class NotificationStatus(str, enum.Enum):
    """Status of notification."""
    UNREAD = "unread"
    READ = "read"


class NotificationPreferences(Base):
    """User notification preferences."""
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Email notifications
    email_enabled = Column(Boolean, default=True)
    email_forgot_checkin = Column(Boolean, default=True)
    email_forgot_checkout = Column(Boolean, default=True)
    email_leave_updates = Column(Boolean, default=True)
    
    # Push/In-app notifications
    push_enabled = Column(Boolean, default=True)
    push_forgot_checkin = Column(Boolean, default=True)
    push_forgot_checkout = Column(Boolean, default=True)
    push_leave_updates = Column(Boolean, default=True)
    
    # Timing preferences
    checkin_reminder_time = Column(String, default="09:00")  # Time to remind if not checked in
    checkout_reminder_time = Column(String, default="18:00")  # Time to remind if not checked out
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="notification_preferences")


class Notification(Base):
    """In-app notification model."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.UNREAD)
    
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    link = Column(String, nullable=True)  # Optional link to relevant page
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    read_at = Column(DateTime, nullable=True)

    user = relationship("User", backref="notifications")
