"""Attendance routes — check-in/out, history, and statistics."""
from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional
from datetime import datetime, timedelta, date

from app.schemas.checkinout import (
    CheckInCreate, CheckOutCreate, CheckInOutResponse,
    CheckInOutTodayResponse, WorkingHoursSummary, MonthlyStatistics
)
from app.services.attendance_service import AttendanceService
from app.container import get_attendance_service
from app.authorization.dependencies import require
from app.authorization.permissions import Permission
from app.models.user import User

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/check-in", response_model=CheckInOutResponse, status_code=status.HTTP_201_CREATED)
def check_in(
    check_in_data: CheckInCreate,
    current_user: User = Depends(require(Permission.VIEW_OWN_ATTENDANCE)),
    service: AttendanceService = Depends(get_attendance_service)
):
    """Check in for the day."""
    return service.check_in_user(current_user, check_in_data)


@router.post("/check-out", response_model=CheckInOutResponse)
def check_out(
    check_out_data: CheckOutCreate,
    current_user: User = Depends(require(Permission.VIEW_OWN_ATTENDANCE)),
    service: AttendanceService = Depends(get_attendance_service)
):
    """Check out for the day."""
    return service.check_out_user(current_user, check_out_data)


@router.get("/my-today", response_model=CheckInOutTodayResponse)
def get_my_today_status(
    current_user: User = Depends(require(Permission.VIEW_OWN_ATTENDANCE)),
    service: AttendanceService = Depends(get_attendance_service)
):
    """Get today's check-in/out status for current user."""
    today_record = service.get_today_checkinout(current_user)
    active_shift = service.get_active_shift(current_user)

    can_check_in = active_shift is None
    can_check_out = active_shift is not None
    display_record = active_shift or today_record

    return CheckInOutTodayResponse(
        id=display_record.id if display_record else None,
        check_in_time=display_record.check_in_time if display_record else None,
        check_out_time=display_record.check_out_time if display_record else None,
        shift_type=display_record.shift_type if display_record else None,
        hours_worked=display_record.hours_worked if display_record else None,
        can_check_in=can_check_in,
        can_check_out=can_check_out,
        active_shift_id=active_shift.shift_id if active_shift else None
    )


@router.get("/history", response_model=List[CheckInOutResponse])
def get_my_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter until date"),
    current_user: User = Depends(require(Permission.VIEW_OWN_ATTENDANCE)),
    service: AttendanceService = Depends(get_attendance_service)
):
    """Get attendance history for current user."""
    start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
    end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
    return service.get_user_attendance_history(current_user.id, skip, limit, start_datetime, end_datetime)


@router.get("/working-hours", response_model=WorkingHoursSummary)
def get_my_working_hours(
    days: int = Query(30, ge=1, le=365, description="Number of days to calculate"),
    current_user: User = Depends(require(Permission.VIEW_OWN_ATTENDANCE)),
    service: AttendanceService = Depends(get_attendance_service)
):
    """Get working hours summary for the specified number of past days."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    summary = service.get_working_hours_summary(current_user.id, start_date, end_date)
    return WorkingHoursSummary(date=f"Last {days} days", **summary)


@router.get("/monthly-stats", response_model=MonthlyStatistics)
def get_my_monthly_stats(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(require(Permission.VIEW_OWN_ATTENDANCE)),
    service: AttendanceService = Depends(get_attendance_service)
):
    """Get monthly attendance statistics for current user."""
    stats = service.get_monthly_statistics(current_user.id, year, month)
    return MonthlyStatistics(**stats)
