"""
Notification service — business logic for notifications and email sending.

Architecture:
- Accepts repositories via constructor (DIP)
- Uses @transactional for consistent transaction management
- Email sending is a separate concern (can be moved to background job)
"""
import logging
import smtplib
from typing import Optional, List
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.notification import Notification, NotificationPreferences, NotificationType, NotificationStatus
from app.models.user import User
from app.schemas.notification import NotificationPreferencesUpdate
from app.core.config import settings
from app.core.transaction import transactional
from app.core.job_queue import enqueue
from app.core.jobs import job_send_email
from app.interfaces.repositories import INotificationRepository, IUserRepository
from app.repositories.notification_repo import NotificationRepository
from app.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


# ── Email sending (standalone, can be used with BackgroundTasks) ─────

def send_email(to_email: str, subject: str, message: str) -> bool:
    """Send an email using SMTP. Logs content if SMTP is not configured."""
    if not settings.SMTP_HOST:
        logger.info(f"[Email Sim] To: {to_email} | Subject: {subject}")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"[Email] Sent to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"[Email] Failed to send to {to_email}: {e}")
        return False


class NotificationService:
    """Handles all notification-related business logic."""

    def __init__(
        self, db: Session,
        repo: INotificationRepository = None,
        user_repo: IUserRepository = None,
    ):
        self.db = db
        self.repo = repo or NotificationRepository(db)
        self.user_repo = user_repo or UserRepository(db)

    # ── Preferences ─────────────────────────────────────────────────

    @transactional
    def get_or_create_preferences(self, user_id: int) -> NotificationPreferences:
        """Get or create notification preferences for a user."""
        prefs = self.repo.get_preferences(user_id)
        if not prefs:
            prefs = self.repo.create_preferences(user_id)
            self.db.flush()
            self.db.refresh(prefs)
        return prefs

    @transactional
    def update_preferences(self, user_id: int, update_data: NotificationPreferencesUpdate) -> NotificationPreferences:
        """Update notification preferences."""
        prefs = self.repo.get_preferences(user_id)
        if not prefs:
            prefs = self.repo.create_preferences(user_id)
            self.db.flush()
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(prefs, field, value)
        self.db.flush()
        self.db.refresh(prefs)
        return prefs

    # ── CRUD ────────────────────────────────────────────────────────

    @transactional
    def create_notification(
        self, user_id: int, notification_type: NotificationType,
        title: str, message: str, link: Optional[str] = None
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link
        )
        self.repo.create_notification(notification)
        self.db.flush()
        self.db.refresh(notification)
        return notification

    def get_user_notifications(
        self, user_id: int, skip: int = 0, limit: int = 50, unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user."""
        return self.repo.get_for_user(user_id, skip, limit, unread_only)

    def get_unread_count(self, user_id: int) -> dict:
        """Get unread notification count."""
        return self.repo.get_unread_count(user_id)

    @transactional
    def mark_as_read(self, notification_id: int, user_id: int) -> Notification:
        """Mark a notification as read."""
        notification = self.repo.get_by_id(notification_id, user_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        notification.status = NotificationStatus.READ
        notification.read_at = datetime.utcnow()
        return notification

    @transactional
    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read. Returns count updated."""
        result = self.repo.mark_all_read(user_id)
        return result

    @transactional
    def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete a notification."""
        notification = self.repo.get_by_id(notification_id, user_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        self.repo.delete(notification)
        return True

    # ── Notification + Email helpers (DRY — single helper) ──────────

    def _send_notification_with_email(
        self, user_id: int, notification_type: NotificationType,
        title: str, message: str, link: str, pref_field: str
    ) -> Notification:
        """Create notification and send email if user prefs allow."""
        notif = self.create_notification(user_id, notification_type, title, message, link)

        user = self.user_repo.get_by_id(user_id)
        prefs = self.repo.get_preferences(user_id)
        if user and prefs and prefs.email_enabled and getattr(prefs, pref_field, False):
            enqueue(job_send_email, user.email, notif.title, notif.message)

        return notif

    def notify_forgot_checkout(self, user_id: int) -> Notification:
        """Create forgot checkout notification and send email."""
        return self._send_notification_with_email(
            user_id, NotificationType.FORGOT_CHECKOUT,
            "⏰ Forgot to Check Out?",
            "You checked in today but haven't checked out yet. Don't forget!",
            "/dashboard", "email_forgot_checkout"
        )

    def notify_forgot_checkin(self, user_id: int) -> Notification:
        """Create forgot checkin notification and send email."""
        return self._send_notification_with_email(
            user_id, NotificationType.FORGOT_CHECKIN,
            "📍 Haven't Checked In",
            "It's past your usual check-in time. Did you forget to check in?",
            "/dashboard", "email_forgot_checkin"
        )

    def notify_leave_approved(self, user_id: int, leave_dates: str) -> Notification:
        """Create leave approved notification and send email."""
        return self._send_notification_with_email(
            user_id, NotificationType.LEAVE_APPROVED,
            "✅ Leave Approved",
            f"Your leave request for {leave_dates} has been approved!",
            "/leaves", "email_leave_updates"
        )

    def notify_leave_rejected(self, user_id: int, leave_dates: str, reason: str = "") -> Notification:
        """Create leave rejected notification and send email."""
        msg = f"Your leave request for {leave_dates} has been rejected."
        if reason:
            msg += f" Reason: {reason}"
        return self._send_notification_with_email(
            user_id, NotificationType.LEAVE_REJECTED,
            "❌ Leave Rejected", msg,
            "/leaves", "email_leave_updates"
        )

    def notify_auto_checkout(self, user_id: int, checkout_time: str) -> Notification:
        """Create auto-checkout notification and send email."""
        return self._send_notification_with_email(
            user_id, NotificationType.AUTO_CHECKOUT,
            "🤖 Auto Check-Out",
            f"You were automatically checked out at {checkout_time} due to inactivity.",
            "/history", "email_forgot_checkout"
        )


# ── Backward-compatible module-level functions ──────────────────────

def get_or_create_preferences(db: Session, user_id: int):
    return NotificationService(db).get_or_create_preferences(user_id)

def update_preferences(db: Session, user_id: int, update_data):
    return NotificationService(db).update_preferences(user_id, update_data)

def create_notification(db, user_id, notification_type, title, message, link=None):
    return NotificationService(db).create_notification(user_id, notification_type, title, message, link)

def get_user_notifications(db, user_id, skip=0, limit=50, unread_only=False):
    return NotificationService(db).get_user_notifications(user_id, skip, limit, unread_only)

def get_unread_count(db, user_id):
    return NotificationService(db).get_unread_count(user_id)

def mark_as_read(db, notification_id, user_id):
    return NotificationService(db).mark_as_read(notification_id, user_id)

def mark_all_as_read(db, user_id):
    return NotificationService(db).mark_all_as_read(user_id)

def delete_notification(db, notification_id, user_id):
    return NotificationService(db).delete_notification(notification_id, user_id)

def notify_forgot_checkout(db, user_id):
    return NotificationService(db).notify_forgot_checkout(user_id)

def notify_forgot_checkin(db, user_id):
    return NotificationService(db).notify_forgot_checkin(user_id)

def notify_leave_approved(db, user_id, leave_dates):
    return NotificationService(db).notify_leave_approved(user_id, leave_dates)

def notify_leave_rejected(db, user_id, leave_dates, reason=""):
    return NotificationService(db).notify_leave_rejected(user_id, leave_dates, reason)

def notify_auto_checkout(db, user_id, checkout_time):
    return NotificationService(db).notify_auto_checkout(user_id, checkout_time)
