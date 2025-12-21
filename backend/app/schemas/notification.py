from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models.notification import NotificationType, NotificationStatus


class NotificationPreferencesUpdate(BaseModel):
    """Schema for updating notification preferences."""
    email_enabled: Optional[bool] = None
    email_forgot_checkin: Optional[bool] = None
    email_forgot_checkout: Optional[bool] = None
    email_leave_updates: Optional[bool] = None
    push_enabled: Optional[bool] = None
    push_forgot_checkin: Optional[bool] = None
    push_forgot_checkout: Optional[bool] = None
    push_leave_updates: Optional[bool] = None
    checkin_reminder_time: Optional[str] = None
    checkout_reminder_time: Optional[str] = None


class NotificationPreferencesResponse(BaseModel):
    """Schema for notification preferences response."""
    id: int
    user_id: int
    email_enabled: bool
    email_forgot_checkin: bool
    email_forgot_checkout: bool
    email_leave_updates: bool
    push_enabled: bool
    push_forgot_checkin: bool
    push_forgot_checkout: bool
    push_leave_updates: bool
    checkin_reminder_time: str
    checkout_reminder_time: str

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    """Schema for notification response."""
    id: int
    user_id: int
    notification_type: NotificationType
    status: NotificationStatus
    title: str
    message: str
    link: Optional[str]
    created_at: datetime
    read_at: Optional[datetime]

    class Config:
        from_attributes = True


class NotificationCount(BaseModel):
    """Schema for unread notification count."""
    unread_count: int
    total_count: int
