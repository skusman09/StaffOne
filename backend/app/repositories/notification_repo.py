"""
Notification repository — all Notification and NotificationPreferences database queries.
"""
from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.notification import Notification, NotificationPreferences, NotificationStatus
from app.repositories import BaseRepository


class NotificationRepository(BaseRepository):
    """Data access layer for Notification and NotificationPreferences models."""

    def __init__(self, db: Session):
        super().__init__(db)

    # ── Preferences ─────────────────────────────────────────────────

    def get_preferences(self, user_id: int) -> Optional[NotificationPreferences]:
        """Get notification preferences for a user."""
        return self.db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == user_id
        ).first()

    def create_preferences(self, user_id: int) -> NotificationPreferences:
        """Create default notification preferences for a user."""
        prefs = NotificationPreferences(user_id=user_id)
        self.db.add(prefs)
        self.db.flush()
        return prefs

    # ── Notifications ───────────────────────────────────────────────

    def create_notification(self, notification: Notification) -> Notification:
        """Create a new notification."""
        self.db.add(notification)
        self.db.flush()
        return notification

    def get_by_id(self, notification_id: int, user_id: int) -> Optional[Notification]:
        """Get a notification by ID ensuring it belongs to the user."""
        return self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()

    def get_for_user(
        self, user_id: int, skip: int = 0, limit: int = 50,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user."""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.status == NotificationStatus.UNREAD)
        return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    def get_unread_count(self, user_id: int) -> dict:
        """Get unread and total notification counts."""
        unread = self.db.query(func.count(Notification.id)).filter(
            Notification.user_id == user_id,
            Notification.status == NotificationStatus.UNREAD
        ).scalar()

        total = self.db.query(func.count(Notification.id)).filter(
            Notification.user_id == user_id
        ).scalar()

        return {"unread_count": unread or 0, "total_count": total or 0}

    def mark_all_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user. Returns count updated."""
        result = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.status == NotificationStatus.UNREAD
        ).update({
            Notification.status: NotificationStatus.READ,
            Notification.read_at: datetime.utcnow()
        })
        self.db.flush()
        return result
