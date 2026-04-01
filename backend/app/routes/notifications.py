"""Notification routes — preferences, listing, read/delete."""
from fastapi import APIRouter, Depends, Query
from typing import List

from app.schemas.notification import (
    NotificationPreferencesUpdate, NotificationPreferencesResponse,
    NotificationResponse, NotificationCount
)
from app.services.notification_service import NotificationService
from app.container import get_notification_service
from app.authorization.dependencies import require
from app.authorization.permissions import Permission
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/preferences", response_model=NotificationPreferencesResponse)
def get_my_preferences(
    current_user: User = Depends(require(Permission.VIEW_OWN_NOTIFICATIONS)),
    service: NotificationService = Depends(get_notification_service)
):
    """Get my notification preferences."""
    return service.get_or_create_preferences(current_user.id)


@router.patch("/preferences", response_model=NotificationPreferencesResponse)
def update_my_preferences(
    update_data: NotificationPreferencesUpdate,
    current_user: User = Depends(require(Permission.VIEW_OWN_NOTIFICATIONS)),
    service: NotificationService = Depends(get_notification_service)
):
    """Update my notification preferences."""
    return service.update_preferences(current_user.id, update_data)


@router.get("", response_model=List[NotificationResponse])
def get_my_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(require(Permission.VIEW_OWN_NOTIFICATIONS)),
    service: NotificationService = Depends(get_notification_service)
):
    """Get my notifications."""
    return service.get_user_notifications(current_user.id, skip, limit, unread_only)


@router.get("/count", response_model=NotificationCount)
def get_notification_count(
    current_user: User = Depends(require(Permission.VIEW_OWN_NOTIFICATIONS)),
    service: NotificationService = Depends(get_notification_service)
):
    """Get unread notification count."""
    return service.get_unread_count(current_user.id)


@router.get("/unread", response_model=List[NotificationResponse])
def get_unread_notifications(
    current_user: User = Depends(require(Permission.VIEW_OWN_NOTIFICATIONS)),
    service: NotificationService = Depends(get_notification_service)
):
    """Get unread notifications only."""
    return service.get_user_notifications(current_user.id, 0, 50, unread_only=True)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(require(Permission.VIEW_OWN_NOTIFICATIONS)),
    service: NotificationService = Depends(get_notification_service)
):
    """Mark a notification as read."""
    return service.mark_as_read(notification_id, current_user.id)


@router.post("/read-all")
def mark_all_notifications_read(
    current_user: User = Depends(require(Permission.VIEW_OWN_NOTIFICATIONS)),
    service: NotificationService = Depends(get_notification_service)
):
    """Mark all notifications as read."""
    count = service.mark_all_as_read(current_user.id)
    return {"message": f"Marked {count} notifications as read"}


@router.delete("/{notification_id}")
def delete_my_notification(
    notification_id: int,
    current_user: User = Depends(require(Permission.VIEW_OWN_NOTIFICATIONS)),
    service: NotificationService = Depends(get_notification_service)
):
    """Delete a notification."""
    service.delete_notification(notification_id, current_user.id)
    return {"message": "Notification deleted"}
