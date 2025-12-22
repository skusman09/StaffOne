from pydantic import BaseModel
from typing import Optional, Dict
from datetime import date


class AdminReportUserSummary(BaseModel):
    """Summary metrics for a single user in the admin report."""
    user_id: int
    user_full_name: str
    user_email: str
    days_worked: int
    total_hours: float
    overtime_days: int
    overtime_hours: float


class AdminReportResponse(BaseModel):
    """Response model for admin attendance report."""
    start_date: date
    end_date: date
    total_users: int
    summaries: Dict[int, AdminReportUserSummary]
