"""
Background job scheduler for automated tasks.

Handles:
- Daily auto-checkout of pending records
- Monthly payroll generation reminders
- Cleanup tasks
"""
import logging
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.attendance_service import auto_checkout_pending_records
from app.services.audit_service import log_action

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = BackgroundScheduler()


def get_db_session() -> Session:
    """Create a database session for background jobs."""
    return SessionLocal()


def job_auto_checkout():
    """
    Daily job: Auto-checkout all pending attendance records.
    
    Runs at 11:59 PM daily to close any open check-ins.
    """
    logger.info("[Scheduler] Running auto-checkout job...")
    db = get_db_session()
    try:
        count = auto_checkout_pending_records(db)
        logger.info(f"[Scheduler] Auto-checkout completed: {count} records closed")
        
        # Log the action
        if count > 0:
            log_action(
                db=db,
                action="AUTO_CHECKOUT",
                resource_type="attendance",
                description=f"Auto-checkout job closed {count} pending records",
            )
    except Exception as e:
        logger.error(f"[Scheduler] Auto-checkout job failed: {e}")
    finally:
        db.close()


def job_payroll_reminder():
    """
    Monthly job: Log reminder for payroll generation.
    
    Runs on the 1st of each month to remind about generating payroll.
    """
    logger.info("[Scheduler] Running payroll reminder job...")
    db = get_db_session()
    try:
        today = date.today()
        prev_month = today.month - 1 if today.month > 1 else 12
        prev_year = today.year if today.month > 1 else today.year - 1
        
        log_action(
            db=db,
            action="REMINDER",
            resource_type="payroll",
            description=f"Monthly payroll reminder: Generate payroll for {prev_year}-{prev_month:02d}",
        )
        logger.info(f"[Scheduler] Payroll reminder logged for {prev_year}-{prev_month:02d}")
    except Exception as e:
        logger.error(f"[Scheduler] Payroll reminder job failed: {e}")
    finally:
        db.close()


def job_cleanup_old_logs():
    """
    Weekly job: Cleanup old audit logs (older than 90 days).
    
    Runs every Sunday at 3 AM.
    """
    logger.info("[Scheduler] Running audit log cleanup job...")
    db = get_db_session()
    try:
        from datetime import timedelta
        from app.models.audit import AuditLog
        
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        deleted = db.query(AuditLog).filter(AuditLog.timestamp < cutoff_date).delete()
        db.commit()
        
        if deleted > 0:
            logger.info(f"[Scheduler] Cleaned up {deleted} old audit logs")
    except Exception as e:
        logger.error(f"[Scheduler] Audit log cleanup failed: {e}")
        db.rollback()
    finally:
        db.close()


def init_scheduler():
    """Initialize and start the background scheduler."""
    if scheduler.running:
        logger.info("[Scheduler] Already running")
        return
    
    # Daily auto-checkout at 11:59 PM
    scheduler.add_job(
        job_auto_checkout,
        trigger=CronTrigger(hour=23, minute=59),
        id="auto_checkout",
        name="Auto-checkout pending records",
        replace_existing=True
    )
    
    # Monthly payroll reminder on 1st of month at 9 AM
    scheduler.add_job(
        job_payroll_reminder,
        trigger=CronTrigger(day=1, hour=9, minute=0),
        id="payroll_reminder",
        name="Monthly payroll reminder",
        replace_existing=True
    )
    
    # Weekly cleanup on Sunday at 3 AM
    scheduler.add_job(
        job_cleanup_old_logs,
        trigger=CronTrigger(day_of_week="sun", hour=3, minute=0),
        id="cleanup_logs",
        name="Cleanup old audit logs",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("[Scheduler] Background scheduler started with jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name} ({job.id})")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Scheduler shutdown complete")


def get_scheduler_status():
    """Get current status of all scheduled jobs."""
    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": next_run.isoformat() if next_run else None,
            "trigger": str(job.trigger)
        })
    return {
        "running": scheduler.running,
        "jobs": jobs
    }
