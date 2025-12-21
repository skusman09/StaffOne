from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.notification import Notification, NotificationPreferences, NotificationType, NotificationStatus
from app.models.user import User
from app.schemas.notification import NotificationPreferencesUpdate
from datetime import datetime
from typing import List, Optional


def get_or_create_preferences(db: Session, user_id: int) -> NotificationPreferences:
    """Get or create notification preferences for a user."""
    prefs = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == user_id
    ).first()
    
    if not prefs:
        prefs = NotificationPreferences(user_id=user_id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    return prefs


def update_preferences(
    db: Session,
    user_id: int,
    update_data: NotificationPreferencesUpdate
) -> NotificationPreferences:
    """Update notification preferences."""
    prefs = get_or_create_preferences(db, user_id)
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(prefs, field, value)
    
    db.commit()
    db.refresh(prefs)
    return prefs


def create_notification(
    db: Session,
    user_id: int,
    notification_type: NotificationType,
    title: str,
    message: str,
    link: Optional[str] = None
) -> Notification:
    """Create a new notification for a user."""
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_user_notifications(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False
) -> List[Notification]:
    """Get notifications for a user."""
    query = db.query(Notification).filter(Notification.user_id == user_id)
    
    if unread_only:
        query = query.filter(Notification.status == NotificationStatus.UNREAD)
    
    return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()


def get_unread_count(db: Session, user_id: int) -> dict:
    """Get unread notification count."""
    unread = db.query(func.count(Notification.id)).filter(
        Notification.user_id == user_id,
        Notification.status == NotificationStatus.UNREAD
    ).scalar()
    
    total = db.query(func.count(Notification.id)).filter(
        Notification.user_id == user_id
    ).scalar()
    
    return {"unread_count": unread or 0, "total_count": total or 0}


def mark_as_read(db: Session, notification_id: int, user_id: int) -> Notification:
    """Mark a notification as read."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    notification.status = NotificationStatus.READ
    notification.read_at = datetime.utcnow()
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_as_read(db: Session, user_id: int) -> int:
    """Mark all notifications as read for a user. Returns count of updated."""
    result = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.status == NotificationStatus.UNREAD
    ).update({
        Notification.status: NotificationStatus.READ,
        Notification.read_at: datetime.utcnow()
    })
    
    db.commit()
    return result


def delete_notification(db: Session, notification_id: int, user_id: int) -> bool:
    """Delete a notification."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    db.delete(notification)
    db.commit()
    return True


# Notification creation helpers for common scenarios
def notify_forgot_checkout(db: Session, user_id: int) -> Notification:
    """Create forgot checkout notification."""
    return create_notification(
        db, user_id,
        NotificationType.FORGOT_CHECKOUT,
        "⏰ Forgot to Check Out?",
        "You checked in today but haven't checked out yet. Don't forget!",
        "/dashboard"
    )


def notify_forgot_checkin(db: Session, user_id: int) -> Notification:
    """Create forgot checkin notification."""
    return create_notification(
        db, user_id,
        NotificationType.FORGOT_CHECKIN,
        "📍 Haven't Checked In",
        "It's past your usual check-in time. Did you forget to check in?",
        "/dashboard"
    )


def notify_leave_approved(db: Session, user_id: int, leave_dates: str) -> Notification:
    """Create leave approved notification."""
    return create_notification(
        db, user_id,
        NotificationType.LEAVE_APPROVED,
        "✅ Leave Approved",
        f"Your leave request for {leave_dates} has been approved!",
        "/leaves"
    )


def notify_leave_rejected(db: Session, user_id: int, leave_dates: str, reason: str = "") -> Notification:
    """Create leave rejected notification."""
    msg = f"Your leave request for {leave_dates} has been rejected."
    if reason:
        msg += f" Reason: {reason}"
    return create_notification(
        db, user_id,
        NotificationType.LEAVE_REJECTED,
        "❌ Leave Rejected",
        msg,
        "/leaves"
    )


def notify_auto_checkout(db: Session, user_id: int, checkout_time: str) -> Notification:
    """Create auto-checkout notification."""
    return create_notification(
        db, user_id,
        NotificationType.AUTO_CHECKOUT,
        "🤖 Auto Check-Out",
        f"You were automatically checked out at {checkout_time} due to inactivity.",
        "/history"
    )
