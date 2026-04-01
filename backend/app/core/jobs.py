"""
Background job definitions — pure, serializable functions for RQ workers.

RULES:
1. Every function here MUST be importable by a separate worker process.
2. No FastAPI request objects or DB sessions as parameters — jobs create their own.
3. Each job manages its own DB session lifecycle (open → use → close).
4. Jobs must be idempotent where possible.

Worker command:
    cd backend && .venv/Scripts/rq worker staffone --with-scheduler

If Redis is not available in development, these functions can also be
called directly (synchronous fallback via job_queue.enqueue).
"""
import logging
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)


# ── Email Jobs ──────────────────────────────────────────────────────

def job_send_email(to_email: str, subject: str, message: str) -> bool:
    """Send an email via SMTP. Fully self-contained — no DB session needed."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from app.core.config import settings

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


# ── Attendance Jobs ─────────────────────────────────────────────────

def job_auto_checkout() -> int:
    """
    Auto-checkout all pending attendance records.

    Scheduled: Daily at 11:59 PM.
    Creates its own DB session. Fully standalone.
    """
    logger.info("[Job] Running auto-checkout...")
    from app.database import SessionLocal
    from app.services.attendance_service import AttendanceService
    from app.services.audit_service import AuditService

    db = SessionLocal()
    try:
        count = AttendanceService(db).auto_checkout_pending_records()
        logger.info(f"[Job] Auto-checkout completed: {count} records closed")

        if count > 0:
            AuditService(db).log_action(
                action="AUTO_CHECKOUT",
                resource_type="attendance",
                description=f"Auto-checkout job closed {count} pending records",
            )
        return count
    except Exception as e:
        logger.error(f"[Job] Auto-checkout failed: {e}")
        raise
    finally:
        db.close()


# ── Payroll Jobs ────────────────────────────────────────────────────

def job_payroll_reminder() -> None:
    """
    Log a payroll generation reminder for the previous month.

    Scheduled: 1st of each month at 9 AM.
    """
    logger.info("[Job] Running payroll reminder...")
    from app.database import SessionLocal
    from app.services.audit_service import AuditService

    db = SessionLocal()
    try:
        today = date.today()
        prev_month = today.month - 1 if today.month > 1 else 12
        prev_year = today.year if today.month > 1 else today.year - 1

        AuditService(db).log_action(
            action="REMINDER",
            resource_type="payroll",
            description=f"Monthly payroll reminder: Generate payroll for {prev_year}-{prev_month:02d}",
        )
        logger.info(f"[Job] Payroll reminder logged for {prev_year}-{prev_month:02d}")
    except Exception as e:
        logger.error(f"[Job] Payroll reminder failed: {e}")
        raise
    finally:
        db.close()


# ── Cleanup Jobs ────────────────────────────────────────────────────

def job_cleanup_old_logs() -> int:
    """
    Delete audit logs older than 90 days.

    Scheduled: Every Sunday at 3 AM.
    """
    logger.info("[Job] Running audit log cleanup...")
    from app.database import SessionLocal
    from app.models.audit import AuditLog

    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        deleted = db.query(AuditLog).filter(AuditLog.timestamp < cutoff_date).delete()
        db.commit()

        if deleted > 0:
            logger.info(f"[Job] Cleaned up {deleted} old audit logs")
        return deleted
    except Exception as e:
        logger.error(f"[Job] Audit log cleanup failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# ── Notification Jobs ───────────────────────────────────────────────

def job_send_notification_email(user_id: int, title: str, message: str) -> bool:
    """
    Look up user email and send notification email.

    Called when a notification is created and user preferences allow email.
    """
    logger.info(f"[Job] Sending notification email for user_id={user_id}")
    from app.database import SessionLocal
    from app.models.user import User

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.email:
            logger.warning(f"[Job] User {user_id} not found or has no email")
            return False
        return job_send_email(user.email, title, message)
    finally:
        db.close()
