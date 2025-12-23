from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, Dict
from datetime import date, datetime, timedelta
from collections import defaultdict

from app.database import get_db
from app.models.checkinout import CheckInOut
from app.models.user import User
from app.schemas.reports import AdminReportUserSummary, AdminReportResponse
from app.utils.dependencies import get_current_admin_user
from app.utils.excel_generator import generate_attendance_summary_excel

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/export/excel")
def export_attendance_excel(
    user_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Export attendance summary as Excel. Admin only."""
    # Reuse the logic from summary endpoint (refactor into a helper if it were more complex)
    report = get_admin_attendance_summary(user_id, start_date, end_date, current_user, db)
    
    excel_file = generate_attendance_summary_excel(report.model_dump())
    
    filename = f"attendance_report_{report.start_date}_to_{report.end_date}.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def get_default_date_range() -> tuple[date, date]:
    """Get default date range: start of current month to today."""
    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    return start_of_month, today


@router.get("/admin-summary", response_model=AdminReportResponse)
def get_admin_attendance_summary(
    user_id: Optional[int] = Query(None, description="Filter by specific user ID"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin attendance summary report.
    
    Returns aggregate attendance statistics for all employees or a specific user
    over the selected date range. Admin only.
    
    Metrics calculated per user:
    - Days Worked: Count of completed check-ins (has check-out)
    - Total Hours: Sum of all work durations
    - Overtime Days: Days where total hours > 8
    - Overtime Hours: Sum of hours beyond 8 for each overtime day
    """
    # Set default date range if not provided
    if not start_date or not end_date:
        default_start, default_end = get_default_date_range()
        start_date = start_date or default_start
        end_date = end_date or default_end
    
    # Convert dates to datetime for query
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Build query
    query = db.query(CheckInOut).join(User, CheckInOut.user_id == User.id).filter(
        CheckInOut.check_in_time >= start_datetime,
        CheckInOut.check_in_time <= end_datetime,
        CheckInOut.check_out_time.isnot(None)  # Only completed check-ins
    )
    
    # Filter by specific user if provided
    if user_id:
        query = query.filter(CheckInOut.user_id == user_id)
    
    records = query.all()
    
    # Group records by user and date for calculations
    user_data: Dict[int, dict] = {}
    user_daily_hours: Dict[int, Dict[date, float]] = defaultdict(lambda: defaultdict(float))
    
    for record in records:
        uid = record.user_id
        
        # Initialize user data if not exists
        if uid not in user_data:
            user_obj = record.user
            user_data[uid] = {
                "user_id": uid,
                "user_full_name": user_obj.full_name or user_obj.username,
                "user_email": user_obj.email,
                "days_worked": 0,
                "total_hours": 0.0,
                "days_set": set(),  # Track unique days
            }
        
        # Add hours
        hours = record.hours_worked or 0
        user_data[uid]["total_hours"] += hours
        
        # Track daily hours for overtime calculation
        record_date = record.check_in_time.date()
        user_daily_hours[uid][record_date] += hours
        user_data[uid]["days_set"].add(record_date)
    
    # Calculate final metrics
    summaries = {}
    for uid, data in user_data.items():
        # Days worked = unique days with records
        days_worked = len(data["days_set"])
        
        # Calculate overtime
        overtime_days = 0
        overtime_hours = 0.0
        
        for day_date, day_hours in user_daily_hours[uid].items():
            if day_hours > 8:
                overtime_days += 1
                overtime_hours += day_hours - 8
        
        summaries[uid] = AdminReportUserSummary(
            user_id=uid,
            user_full_name=data["user_full_name"],
            user_email=data["user_email"],
            days_worked=days_worked,
            total_hours=round(data["total_hours"], 2),
            overtime_days=overtime_days,
            overtime_hours=round(overtime_hours, 2)
        )
    
    return AdminReportResponse(
        start_date=start_date,
        end_date=end_date,
        total_users=len(summaries),
        summaries=summaries
    )
