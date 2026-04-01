"""Analytics routes — dashboard, user stats, trends."""
from fastapi import APIRouter, Depends, Query
from datetime import date, timedelta

from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.container import get_analytics_service
from app.authorization.dependencies import require
from app.authorization.permissions import Permission

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
def get_dashboard(
    days: int = Query(7, ge=1, le=90, description="Number of days for trends"),
    current_user: User = Depends(require(Permission.VIEW_ANALYTICS)),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get dashboard analytics."""
    return service.get_dashboard_analytics(days)


@router.get("/my-stats")
def get_my_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(require(Permission.VIEW_OWN_ATTENDANCE)),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get my attendance analytics."""
    return service.get_user_analytics(current_user.id, days)


@router.get("/user/{user_id}")
def get_user_stats(
    user_id: int,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require(Permission.VIEW_ANALYTICS)),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get analytics for a specific user."""
    return service.get_user_analytics(user_id, days)


@router.get("/trends")
def get_attendance_trends(
    days: int = Query(30, ge=1, le=90),
    current_user: User = Depends(require(Permission.VIEW_ANALYTICS)),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get attendance trends for the specified period."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    daily_stats = service.get_daily_stats(start_date, end_date)
    return {"period": f"{start_date.isoformat()} to {end_date.isoformat()}", "days": days, "trends": daily_stats}


@router.get("/leaderboard")
def get_leaderboard(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(require(Permission.VIEW_ANALYTICS)),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get top performers leaderboard."""
    performers = service.get_top_performers(days, limit)
    return {"period": f"Last {days} days", "leaderboard": performers}
