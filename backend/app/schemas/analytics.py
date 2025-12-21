from pydantic import BaseModel
from datetime import date
from typing import List, Optional


class DailyAttendanceStat(BaseModel):
    """Daily attendance statistics."""
    date: str
    total_checkins: int
    total_checkouts: int
    pending_checkouts: int
    avg_hours_worked: float
    total_hours: float


class WeeklyAttendanceStat(BaseModel):
    """Weekly attendance statistics."""
    week_start: str
    week_end: str
    total_days_worked: int
    total_hours: float
    avg_daily_hours: float
    overtime_hours: float


class MonthlyAttendanceStat(BaseModel):
    """Monthly attendance statistics."""
    month: str
    year: int
    total_days_worked: int
    total_hours: float
    avg_daily_hours: float
    overtime_hours: float
    late_arrivals: int
    early_departures: int


class UserAttendanceSummary(BaseModel):
    """User attendance summary for analytics."""
    user_id: int
    username: str
    full_name: Optional[str]
    total_days: int
    total_hours: float
    avg_hours: float
    pending_checkouts: int


class LeaveAnalytics(BaseModel):
    """Leave analytics."""
    leave_type: str
    count: int
    total_days: int


class DashboardAnalytics(BaseModel):
    """Complete dashboard analytics response."""
    # Today's stats
    today_checkins: int
    today_checkouts: int
    today_pending: int
    today_on_leave: int
    
    # Period stats
    total_employees: int
    active_employees: int
    
    # Trends
    daily_stats: List[DailyAttendanceStat]
    leave_breakdown: List[LeaveAnalytics]
    
    # Top performers (by hours)
    top_performers: List[UserAttendanceSummary]


class AttendanceTrend(BaseModel):
    """Attendance trend data point."""
    date: str
    checkins: int
    hours: float


class AnalyticsResponse(BaseModel):
    """General analytics response."""
    period: str
    data: dict
