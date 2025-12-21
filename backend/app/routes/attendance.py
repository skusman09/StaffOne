from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.schemas.checkinout import (
    CheckInCreate,
    CheckOutCreate,
    CheckInOutResponse,
    CheckInOutTodayResponse,
    WorkingHoursSummary
)
from app.services.attendance_service import (
    check_in_user,
    check_out_user,
    get_today_checkinout,
    get_active_shift,
    get_user_attendance_history,
    get_working_hours_summary
)
from app.utils.dependencies import get_current_user
from app.models.user import User
from app.models.checkinout import ShiftType

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/check-in", response_model=CheckInOutResponse, status_code=status.HTTP_201_CREATED)
def check_in(
    check_in_data: CheckInCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check in for the day.
    
    Creates a new attendance record. User must not have an active (unclosed) shift.
    Supports shift types: REGULAR, BREAK, OVERTIME.
    """
    checkinout = check_in_user(db, current_user, check_in_data)
    return checkinout


@router.post("/check-out", response_model=CheckInOutResponse)
def check_out(
    check_out_data: CheckOutCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check out for the day.
    
    Closes the active shift and calculates hours worked.
    Works even if checkout is on a different day (for night shifts).
    """
    checkinout = check_out_user(db, current_user, check_out_data)
    return checkinout


@router.get("/my-today", response_model=CheckInOutTodayResponse)
def get_my_today_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's check-in/out status for current user.
    
    Uses user's timezone for proper 'today' calculation.
    Also checks for any active (unclosed) shifts.
    """
    today_record = get_today_checkinout(db, current_user)
    active_shift = get_active_shift(db, current_user)
    
    # Determine if user can check in/out
    can_check_in = active_shift is None
    can_check_out = active_shift is not None
    
    # Use active shift for display if exists
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get attendance history for current user."""
    history = get_user_attendance_history(db, current_user.id, skip, limit)
    return history


@router.get("/working-hours", response_model=WorkingHoursSummary)
def get_my_working_hours(
    days: int = Query(30, ge=1, le=365, description="Number of days to calculate"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get working hours summary for the specified number of past days."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    summary = get_working_hours_summary(db, current_user.id, start_date, end_date)
    
    return WorkingHoursSummary(
        date=f"Last {days} days",
        **summary
    )
