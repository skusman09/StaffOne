from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.analytics import DashboardAnalytics
from app.services.analytics_service import (
    get_dashboard_analytics,
    get_user_analytics,
    get_daily_stats,
    get_top_performers
)
from app.utils.dependencies import get_current_user, get_current_admin_user
from app.models.user import User
from datetime import date, timedelta

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
def get_dashboard(
    days: int = Query(7, ge=1, le=90, description="Number of days for trends"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get dashboard analytics (admin only).
    
    Returns today's stats, employee counts, daily trends, leave breakdown, and top performers.
    """
    analytics = get_dashboard_analytics(db, days)
    return analytics


@router.get("/my-stats")
def get_my_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get my attendance analytics."""
    stats = get_user_analytics(db, current_user.id, days)
    return stats


@router.get("/user/{user_id}")
def get_user_stats(
    user_id: int,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get analytics for a specific user (admin only)."""
    stats = get_user_analytics(db, user_id, days)
    return stats


@router.get("/trends")
def get_attendance_trends(
    days: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get attendance trends for the specified period (admin only)."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    
    daily_stats = get_daily_stats(db, start_date, end_date)
    
    return {
        "period": f"{start_date.isoformat()} to {end_date.isoformat()}",
        "days": days,
        "trends": daily_stats
    }


@router.get("/leaderboard")
def get_leaderboard(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get top performers leaderboard (admin only)."""
    performers = get_top_performers(db, days, limit)
    
    return {
        "period": f"Last {days} days",
        "leaderboard": performers
    }
