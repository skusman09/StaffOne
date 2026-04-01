"""Scheduler admin routes — viewing and triggering background jobs."""
from fastapi import APIRouter, Depends, HTTPException

from app.models.user import User
from app.core.scheduler import get_scheduler_status, job_auto_checkout
from app.authorization.dependencies import require
from app.authorization.permissions import Permission

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.get("/status")
def get_status(current_user: User = Depends(require(Permission.MANAGE_SCHEDULER))):
    """Get scheduler status and list of jobs."""
    return get_scheduler_status()


@router.post("/trigger/auto-checkout")
def trigger_auto_checkout(current_user: User = Depends(require(Permission.MANAGE_SCHEDULER))):
    """Manually trigger auto-checkout job."""
    try:
        job_auto_checkout()
        return {"message": "Auto-checkout job triggered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
