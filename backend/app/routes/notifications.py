from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.notification import (
    NotificationPreferencesUpdate,
    NotificationPreferencesResponse,
    NotificationResponse,
    NotificationCount
)
from app.services.notification_service import (
    get_or_create_preferences,
    update_preferences,
    get_user_notifications,
    get_unread_count,
    mark_as_read,
    mark_all_as_read,
    delete_notification
)
from app.utils.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/preferences", response_model=NotificationPreferencesResponse)
def get_my_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get my notification preferences."""
    prefs = get_or_create_preferences(db, current_user.id)
    return prefs


@router.patch("/preferences", response_model=NotificationPreferencesResponse)
def update_my_preferences(
    update_data: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update my notification preferences."""
    prefs = update_preferences(db, current_user.id, update_data)
    return prefs


@router.get("", response_model=List[NotificationResponse])
def get_my_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get my notifications."""
    notifications = get_user_notifications(db, current_user.id, skip, limit, unread_only)
    return notifications


@router.get("/count", response_model=NotificationCount)
def get_notification_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get unread notification count."""
    count = get_unread_count(db, current_user.id)
    return count


@router.get("/unread", response_model=List[NotificationResponse])
def get_unread_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get unread notifications only."""
    notifications = get_user_notifications(db, current_user.id, 0, 50, unread_only=True)
    return notifications


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read."""
    notification = mark_as_read(db, notification_id, current_user.id)
    return notification


@router.post("/read-all")
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read."""
    count = mark_all_as_read(db, current_user.id)
    return {"message": f"Marked {count} notifications as read"}


@router.delete("/{notification_id}")
def delete_my_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a notification."""
    delete_notification(db, notification_id, current_user.id)
    return {"message": "Notification deleted"}
