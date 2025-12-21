from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.checkinout import CheckInOut, ShiftType
from app.models.user import User
from app.models.leave import Leave, LeaveStatus
from datetime import datetime, timedelta, date
from typing import List, Dict, Any


def get_daily_stats(db: Session, start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """Get daily attendance statistics for a date range."""
    stats = []
    current = start_date
    
    while current <= end_date:
        day_start = datetime.combine(current, datetime.min.time())
        day_end = datetime.combine(current, datetime.max.time())
        
        # Query for this day
        records = db.query(CheckInOut).filter(
            CheckInOut.check_in_time >= day_start,
            CheckInOut.check_in_time <= day_end
        ).all()
        
        total_checkins = len(records)
        total_checkouts = len([r for r in records if r.check_out_time])
        pending = total_checkins - total_checkouts
        
        hours_list = [r.hours_worked for r in records if r.hours_worked]
        total_hours = sum(hours_list) if hours_list else 0
        avg_hours = total_hours / len(hours_list) if hours_list else 0
        
        stats.append({
            "date": current.isoformat(),
            "total_checkins": total_checkins,
            "total_checkouts": total_checkouts,
            "pending_checkouts": pending,
            "avg_hours_worked": round(avg_hours, 2),
            "total_hours": round(total_hours, 2)
        })
        
        current += timedelta(days=1)
    
    return stats


def get_today_stats(db: Session) -> Dict[str, int]:
    """Get today's attendance statistics."""
    today = date.today()
    day_start = datetime.combine(today, datetime.min.time())
    day_end = datetime.combine(today, datetime.max.time())
    
    records = db.query(CheckInOut).filter(
        CheckInOut.check_in_time >= day_start,
        CheckInOut.check_in_time <= day_end
    ).all()
    
    # Count approved leaves for today
    on_leave = db.query(func.count(Leave.id)).filter(
        Leave.status == LeaveStatus.APPROVED,
        Leave.start_date <= today,
        Leave.end_date >= today
    ).scalar() or 0
    
    return {
        "today_checkins": len(records),
        "today_checkouts": len([r for r in records if r.check_out_time]),
        "today_pending": len([r for r in records if not r.check_out_time]),
        "today_on_leave": on_leave
    }


def get_employee_stats(db: Session) -> Dict[str, int]:
    """Get employee statistics."""
    total = db.query(func.count(User.id)).scalar() or 0
    active = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    
    return {
        "total_employees": total,
        "active_employees": active
    }


def get_leave_breakdown(db: Session, days: int = 30) -> List[Dict[str, Any]]:
    """Get leave breakdown by type for the last N days."""
    start_date = date.today() - timedelta(days=days)
    
    # Group leaves by type
    results = db.query(
        Leave.leave_type,
        func.count(Leave.id).label('count')
    ).filter(
        Leave.status == LeaveStatus.APPROVED,
        Leave.start_date >= start_date
    ).group_by(Leave.leave_type).all()
    
    breakdown = []
    for leave_type, count in results:
        # Calculate total days
        leaves = db.query(Leave).filter(
            Leave.leave_type == leave_type,
            Leave.status == LeaveStatus.APPROVED,
            Leave.start_date >= start_date
        ).all()
        
        total_days = sum(l.days_count for l in leaves)
        
        breakdown.append({
            "leave_type": leave_type.value,
            "count": count,
            "total_days": total_days
        })
    
    return breakdown


def get_top_performers(db: Session, days: int = 30, limit: int = 5) -> List[Dict[str, Any]]:
    """Get top performers by working hours."""
    start_date = datetime.now() - timedelta(days=days)
    
    # Get users with most hours
    results = db.query(
        User.id,
        User.username,
        User.full_name,
        func.count(CheckInOut.id).label('total_days'),
        func.sum(CheckInOut.hours_worked).label('total_hours')
    ).join(CheckInOut, User.id == CheckInOut.user_id).filter(
        CheckInOut.check_in_time >= start_date,
        CheckInOut.hours_worked.isnot(None)
    ).group_by(User.id, User.username, User.full_name).order_by(
        func.sum(CheckInOut.hours_worked).desc()
    ).limit(limit).all()
    
    performers = []
    for user_id, username, full_name, total_days, total_hours in results:
        # Get pending checkouts
        pending = db.query(func.count(CheckInOut.id)).filter(
            CheckInOut.user_id == user_id,
            CheckInOut.check_out_time.is_(None),
            CheckInOut.check_in_time >= start_date
        ).scalar() or 0
        
        performers.append({
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
            "total_days": total_days or 0,
            "total_hours": round(float(total_hours or 0), 2),
            "avg_hours": round(float(total_hours or 0) / max(total_days or 1, 1), 2),
            "pending_checkouts": pending
        })
    
    return performers


def get_dashboard_analytics(db: Session, days: int = 7) -> Dict[str, Any]:
    """Get complete dashboard analytics."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    
    today_stats = get_today_stats(db)
    employee_stats = get_employee_stats(db)
    daily_stats = get_daily_stats(db, start_date, end_date)
    leave_breakdown = get_leave_breakdown(db, days)
    top_performers = get_top_performers(db, days)
    
    return {
        **today_stats,
        **employee_stats,
        "daily_stats": daily_stats,
        "leave_breakdown": leave_breakdown,
        "top_performers": top_performers
    }


def get_user_analytics(db: Session, user_id: int, days: int = 30) -> Dict[str, Any]:
    """Get analytics for a specific user."""
    start_date = datetime.now() - timedelta(days=days)
    
    records = db.query(CheckInOut).filter(
        CheckInOut.user_id == user_id,
        CheckInOut.check_in_time >= start_date
    ).all()
    
    hours_list = [r.hours_worked for r in records if r.hours_worked]
    total_hours = sum(hours_list) if hours_list else 0
    
    # Group by date for daily breakdown
    daily = {}
    for record in records:
        day = record.check_in_time.date().isoformat()
        if day not in daily:
            daily[day] = {"hours": 0, "count": 0}
        if record.hours_worked:
            daily[day]["hours"] += record.hours_worked
        daily[day]["count"] += 1
    
    # Calculate overtime (hours over 8 per day)
    overtime = sum(max(d["hours"] - 8, 0) for d in daily.values())
    
    return {
        "period": f"Last {days} days",
        "total_records": len(records),
        "total_hours": round(total_hours, 2),
        "avg_daily_hours": round(total_hours / max(len(daily), 1), 2),
        "overtime_hours": round(overtime, 2),
        "pending_checkouts": len([r for r in records if not r.check_out_time]),
        "daily_breakdown": [
            {"date": k, "hours": round(v["hours"], 2), "records": v["count"]}
            for k, v in sorted(daily.items())
        ]
    }
