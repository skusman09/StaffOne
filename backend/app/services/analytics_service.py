"""
Analytics service — business logic for dashboard charts and metrics.

Architecture:
- Class-based service
- Optimized SQL aggregation to fix N+1 query patterns
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta, date

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.checkinout import CheckInOut
from app.models.user import User
from app.models.leave import Leave, LeaveStatus

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Handles all dashboard and performance metric aggregations."""

    def __init__(self, db: Session):
        self.db = db

    def get_daily_stats(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get daily attendance statistics for a date range (Optimized).

        Replaces 30 queries/month with a single GROUP BY query.
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        # Postgres 'func.date()' extracts just the date from a datetime
        # fallback string coercion for cross-database:
        date_expr = func.date(CheckInOut.check_in_time)

        results = self.db.query(
            date_expr.label("day"),
            func.count(CheckInOut.id).label("total_checkins"),
            func.count(CheckInOut.check_out_time).label("total_checkouts"),
            func.sum(CheckInOut.hours_worked).label("total_hours")
        ).filter(
            CheckInOut.check_in_time >= start_dt,
            CheckInOut.check_in_time <= end_dt
        ).group_by(
            date_expr
        ).all()

        # Build map of result days
        stats_map = {}
        for row in results:
            day_iso = row.day.isoformat() if isinstance(row.day, date) else str(row.day)
            total_hours = float(row.total_hours or 0)
            checkouts = row.total_checkouts or 0
            stats_map[day_iso] = {
                "date": day_iso,
                "total_checkins": row.total_checkins,
                "total_checkouts": checkouts,
                "pending_checkouts": row.total_checkins - checkouts,
                "avg_hours_worked": round(total_hours / max(checkouts, 1), 2),
                "total_hours": round(total_hours, 2)
            }

        # Fill in zero days
        stats = []
        current = start_date
        while current <= end_date:
            day_str = current.isoformat()
            if day_str in stats_map:
                stats.append(stats_map[day_str])
            else:
                stats.append({
                    "date": day_str,
                    "total_checkins": 0,
                    "total_checkouts": 0,
                    "pending_checkouts": 0,
                    "avg_hours_worked": 0.0,
                    "total_hours": 0.0
                })
            current += timedelta(days=1)

        return stats

    def get_today_stats(self) -> Dict[str, int]:
        """Get today's attendance statistics."""
        today = date.today()
        day_start = datetime.combine(today, datetime.min.time())
        day_end = datetime.combine(today, datetime.max.time())

        # Consolidate basic checkin/out counts
        stats = self.db.query(
            func.count(CheckInOut.id).label("checkins"),
            func.count(CheckInOut.check_out_time).label("checkouts")
        ).filter(
            CheckInOut.check_in_time >= day_start,
            CheckInOut.check_in_time <= day_end
        ).first()

        checkins = stats.checkins or 0
        checkouts = stats.checkouts or 0

        on_leave = self.db.query(func.count(Leave.id)).filter(
            Leave.status == LeaveStatus.APPROVED,
            Leave.start_date <= today,
            Leave.end_date >= today
        ).scalar() or 0

        return {
            "today_checkins": checkins,
            "today_checkouts": checkouts,
            "today_pending": checkins - checkouts,
            "today_on_leave": on_leave
        }

    def get_employee_stats(self) -> Dict[str, int]:
        """Get employee statistics."""
        stats = self.db.query(
            func.count(User.id).label("total"),
            func.sum(func.cast(User.is_active, func.Integer)).label("active")
        ).first()

        return {
            "total_employees": stats.total or 0,
            "active_employees": int(stats.active or 0)
        }

    def get_leave_breakdown(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get leave breakdown by type for the last N days."""
        start_date = date.today() - timedelta(days=days)

        # Single pass query grouping by type
        # Sums the difference in days directly in DB for Postgres.
        # SQLite lacks native duration parsing easily in func., doing Python compute 
        # is safe here since approved leaves are sparse.
        leaves = self.db.query(Leave).filter(
            Leave.status == LeaveStatus.APPROVED,
            Leave.start_date >= start_date
        ).all()

        breakdown_map = {}
        for leave in leaves:
            l_type = leave.leave_type.value
            if l_type not in breakdown_map:
                breakdown_map[l_type] = {"count": 0, "days": 0}
            breakdown_map[l_type]["count"] += 1
            breakdown_map[l_type]["days"] += leave.days_count

        return [
            {
                "leave_type": l_type,
                "count": data["count"],
                "total_days": data["days"]
            }
            for l_type, data in breakdown_map.items()
        ]

    def get_top_performers(self, days: int = 30, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performers by working hours (Optimized).

        Fixes N+1 issue where it fetched top Users, then queried checkout status for each.
        Now performed in a single aggregation.
        """
        start_date = datetime.now() - timedelta(days=days)

        # Build one aggregate view
        results = self.db.query(
            User.id,
            User.username,
            User.full_name,
            func.count(CheckInOut.id).label('total_days'),
            func.sum(CheckInOut.hours_worked).label('total_hours'),
            # Postgres supports filter inside func.count, but fallback for sqlite:
            # count where check_out_time is null
            func.sum(func.case((CheckInOut.check_out_time.is_(None), 1), else_=0)).label('pending_checkouts')
        ).join(
            CheckInOut, User.id == CheckInOut.user_id
        ).filter(
            CheckInOut.check_in_time >= start_date,
        ).group_by(
            User.id, User.username, User.full_name
        ).order_by(
            # Sort by actual total hours
            func.sum(CheckInOut.hours_worked).desc().nulls_last()
        ).limit(limit).all()

        performers = []
        for row in results:
            total_hours = float(row.total_hours or 0)
            total_days = row.total_days or 0
            # Ignore users with 0 hours in the top list
            if total_hours <= 0:
                continue

            performers.append({
                "user_id": row.id,
                "username": row.username,
                "full_name": row.full_name,
                "total_days": total_days,
                "total_hours": round(total_hours, 2),
                "avg_hours": round(total_hours / max(total_days, 1), 2),
                "pending_checkouts": int(row.pending_checkouts or 0)
            })

        return performers

    def get_dashboard_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get complete dashboard analytics."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        return {
            **self.get_today_stats(),
            **self.get_employee_stats(),
            "daily_stats": self.get_daily_stats(start_date, end_date),
            "leave_breakdown": self.get_leave_breakdown(days),
            "top_performers": self.get_top_performers(days)
        }

    def get_user_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get analytics for a specific user."""
        start_date = datetime.now() - timedelta(days=days)

        records = self.db.query(CheckInOut).filter(
            CheckInOut.user_id == user_id,
            CheckInOut.check_in_time >= start_date
        ).all()

        hours_list = [r.hours_worked for r in records if r.hours_worked]
        total_hours = sum(hours_list) if hours_list else 0

        daily = {}
        for record in records:
            day = record.check_in_time.date().isoformat()
            if day not in daily:
                daily[day] = {"hours": 0, "count": 0}
            if record.hours_worked:
                daily[day]["hours"] += record.hours_worked
            daily[day]["count"] += 1

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


# ── Backward-compatible module-level functions ──────────────────────

def get_daily_stats(db: Session, start_date: date, end_date: date) -> List[Dict[str, Any]]:
    return AnalyticsService(db).get_daily_stats(start_date, end_date)

def get_today_stats(db: Session) -> Dict[str, int]:
    return AnalyticsService(db).get_today_stats()

def get_employee_stats(db: Session) -> Dict[str, int]:
    return AnalyticsService(db).get_employee_stats()

def get_leave_breakdown(db: Session, days: int = 30) -> List[Dict[str, Any]]:
    return AnalyticsService(db).get_leave_breakdown(days)

def get_top_performers(db: Session, days: int = 30, limit: int = 5) -> List[Dict[str, Any]]:
    return AnalyticsService(db).get_top_performers(days, limit)

def get_dashboard_analytics(db: Session, days: int = 7) -> Dict[str, Any]:
    return AnalyticsService(db).get_dashboard_analytics(days)

def get_user_analytics(db: Session, user_id: int, days: int = 30) -> Dict[str, Any]:
    return AnalyticsService(db).get_user_analytics(user_id, days)
