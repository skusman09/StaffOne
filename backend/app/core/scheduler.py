"""
Background job scheduler — APScheduler as a CRON trigger, RQ as the executor.

Architecture:
- APScheduler runs in-process and fires at cron intervals
- Instead of executing job logic directly, it enqueues into RQ
- RQ workers pick up and execute the actual work
- This means: scheduler crash = missed trigger (acceptable)
                worker crash = job stays in Redis queue (durable)

For production multi-instance deployments, only ONE instance should
run the scheduler. Use an environment flag or leader election.
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.job_queue import enqueue
from app.core.jobs import job_auto_checkout, job_payroll_reminder, job_cleanup_old_logs

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = BackgroundScheduler()


def _enqueue_auto_checkout():
    """Cron callback: enqueue auto-checkout job into RQ."""
    logger.info("[Scheduler] Enqueuing auto-checkout job")
    enqueue(job_auto_checkout)


def _enqueue_payroll_reminder():
    """Cron callback: enqueue payroll reminder job into RQ."""
    logger.info("[Scheduler] Enqueuing payroll reminder job")
    enqueue(job_payroll_reminder)


def _enqueue_cleanup_logs():
    """Cron callback: enqueue audit log cleanup job into RQ."""
    logger.info("[Scheduler] Enqueuing audit log cleanup job")
    enqueue(job_cleanup_old_logs)


def init_scheduler():
    """Initialize and start the background scheduler."""
    if scheduler.running:
        logger.info("[Scheduler] Already running")
        return

    # Daily auto-checkout at 11:59 PM
    scheduler.add_job(
        _enqueue_auto_checkout,
        trigger=CronTrigger(hour=23, minute=59),
        id="auto_checkout",
        name="Auto-checkout pending records",
        replace_existing=True
    )

    # Monthly payroll reminder on 1st of month at 9 AM
    scheduler.add_job(
        _enqueue_payroll_reminder,
        trigger=CronTrigger(day=1, hour=9, minute=0),
        id="payroll_reminder",
        name="Monthly payroll reminder",
        replace_existing=True
    )

    # Weekly cleanup on Sunday at 3 AM
    scheduler.add_job(
        _enqueue_cleanup_logs,
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
