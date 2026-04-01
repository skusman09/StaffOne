"""Reports routes — admin attendance summaries and Excel export."""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict
from datetime import date, datetime, timedelta
from collections import defaultdict

from app.database import get_db
from app.models.checkinout import CheckInOut
from app.models.user import User
from app.schemas.reports import AdminReportUserSummary, AdminReportResponse
from app.utils.excel_generator import generate_attendance_summary_excel
from app.authorization.dependencies import require
from app.authorization.permissions import Permission

router = APIRouter(prefix="/reports", tags=["reports"])


def get_default_date_range() -> tuple[date, date]:
    today = date.today()
    return date(today.year, today.month, 1), today


@router.get("/export/excel")
def export_attendance_excel(
    user_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(require(Permission.EXPORT_REPORTS)),
    db: Session = Depends(get_db)
):
    """Export attendance summary as Excel."""
    report = get_admin_attendance_summary(user_id, start_date, end_date, current_user, db)
    excel_file = generate_attendance_summary_excel(report.model_dump())
    filename = f"attendance_report_{report.start_date}_to_{report.end_date}.xlsx"
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/admin-summary", response_model=AdminReportResponse)
def get_admin_attendance_summary(
    user_id: Optional[int] = Query(None, description="Filter by specific user ID"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(require(Permission.VIEW_REPORTS)),
    db: Session = Depends(get_db)
):
    """Get admin attendance summary report."""
    if not start_date or not end_date:
        default_start, default_end = get_default_date_range()
        start_date = start_date or default_start
        end_date = end_date or default_end

    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    query = db.query(CheckInOut).join(User, CheckInOut.user_id == User.id).filter(
        CheckInOut.check_in_time >= start_datetime,
        CheckInOut.check_in_time <= end_datetime,
        CheckInOut.check_out_time.isnot(None)
    )
    if user_id:
        query = query.filter(CheckInOut.user_id == user_id)

    records = query.all()

    user_data: Dict[int, dict] = {}
    user_daily_hours: Dict[int, Dict[date, float]] = defaultdict(lambda: defaultdict(float))

    for record in records:
        uid = record.user_id
        if uid not in user_data:
            user_obj = record.user
            user_data[uid] = {
                "user_id": uid,
                "user_full_name": user_obj.full_name or user_obj.username,
                "user_email": user_obj.email,
                "total_hours": 0.0,
                "days_set": set(),
            }

        hours = record.hours_worked or 0
        user_data[uid]["total_hours"] += hours
        record_date = record.check_in_time.date()
        user_daily_hours[uid][record_date] += hours
        user_data[uid]["days_set"].add(record_date)

    summaries = {}
    for uid, data in user_data.items():
        days_worked = len(data["days_set"])
        overtime_days = 0
        overtime_hours = 0.0
        for day_date, day_hours in user_daily_hours[uid].items():
            if day_hours > 8:
                overtime_days += 1
                overtime_hours += day_hours - 8

        summaries[uid] = AdminReportUserSummary(
            user_id=uid, user_full_name=data["user_full_name"],
            user_email=data["user_email"], days_worked=days_worked,
            total_hours=round(data["total_hours"], 2),
            overtime_days=overtime_days, overtime_hours=round(overtime_hours, 2)
        )

    return AdminReportResponse(
        start_date=start_date, end_date=end_date,
        total_users=len(summaries), summaries=summaries
    )
