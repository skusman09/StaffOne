"""
Scheduler admin routes for viewing and managing background jobs.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.models.user import User
from app.utils.dependencies import get_current_admin_user
from app.core.scheduler import get_scheduler_status, job_auto_checkout

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.get("/status")
def get_status(
    current_user: User = Depends(get_current_admin_user)
):
    """Get scheduler status and list of jobs. Admin only."""
    return get_scheduler_status()


@router.post("/trigger/auto-checkout")
def trigger_auto_checkout(
    current_user: User = Depends(get_current_admin_user)
):
    """Manually trigger auto-checkout job. Admin only."""
    try:
        job_auto_checkout()
        return {"message": "Auto-checkout job triggered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
