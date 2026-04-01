"""
Attendance service — business logic for check-in/out, working hours, and statistics.

Architecture:
- Accepts IAttendanceRepository via constructor (Dependency Inversion)
- Delegates business rules to domain/attendance_rules (pure functions)
- Uses @transactional for consistent commit/rollback
- Services are orchestration only: load → compute → persist
"""
import logging
import uuid
import calendar
from typing import Optional, List
from datetime import datetime, timedelta

import pytz
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.checkinout import CheckInOut, ShiftType
from app.models.user import User
from app.core.config import settings
from app.core.transaction import transactional
from app.schemas.checkinout import CheckInCreate, CheckOutCreate, AdminManualCheckout
from app.interfaces.repositories import IAttendanceRepository
from app.repositories.attendance_repo import AttendanceRepository

# Domain layer — pure business rules
from app.domain.attendance_rules import (
    get_user_timezone,
    get_today_boundaries,
    check_late_arrival,
    check_early_exit,
    calculate_hours_worked,
    accumulate_hours_by_shift,
)

logger = logging.getLogger(__name__)


class AttendanceService:
    """Handles all attendance-related business logic."""

    def __init__(self, db: Session, repo: IAttendanceRepository = None):
        self.db = db
        self.repo = repo or AttendanceRepository(db)

    # ── Check-in / Check-out ────────────────────────────────────────

    def get_today_checkinout(self, user: User) -> Optional[CheckInOut]:
        """Get today's check-in/out record for a user."""
        user_tz = get_user_timezone(user.timezone, settings.DEFAULT_TIMEZONE)
        today_start, today_end = get_today_boundaries(user_tz)
        return self.repo.get_today_record(user.id, today_start, today_end)

    def get_active_shift(self, user: User) -> Optional[CheckInOut]:
        """Get any active (unclosed) shift for a user."""
        return self.repo.get_active_shift(user.id)

    @transactional
    def check_in_user(self, user: User, check_in_data: CheckInCreate) -> CheckInOut:
        """Create a check-in record for a user."""
        active_shift = self.repo.get_active_shift(user.id)
        if active_shift:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have an active shift. Please check out first."
            )

        # Late arrival detection — delegated to domain layer
        user_tz = get_user_timezone(user.timezone, settings.DEFAULT_TIMEZONE)
        late_result = check_late_arrival(user_tz, expected_start_hour=9, grace_minutes=15)

        shift_id = str(uuid.uuid4())
        checkinout = CheckInOut(
            user_id=user.id,
            check_in_time=datetime.utcnow(),
            shift_type=check_in_data.shift_type,
            shift_id=shift_id,
            latitude=check_in_data.latitude,
            longitude=check_in_data.longitude,
            device_info=check_in_data.device_info,
            is_location_valid=True,
            is_auto_checkout=False,
            is_late_arrival=late_result.is_late,
            late_minutes=late_result.minutes_late
        )

        self.repo.add(checkinout)
        self.db.flush()
        self.db.refresh(checkinout)
        return checkinout

    @transactional
    def check_out_user(self, user: User, check_out_data: CheckOutCreate) -> CheckInOut:
        """Update check-out time for a user's active shift."""
        active_shift = self.repo.get_active_shift(user.id)
        if not active_shift:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active shift found. Please check in first."
            )

        checkout_time = datetime.utcnow()
        active_shift.check_out_time = checkout_time
        active_shift.checkout_latitude = check_out_data.latitude
        active_shift.checkout_longitude = check_out_data.longitude

        if check_out_data.device_info:
            active_shift.device_info = check_out_data.device_info

        active_shift.hours_worked = calculate_hours_worked(
            active_shift.check_in_time, checkout_time
        )

        # Early exit detection — delegated to domain layer
        user_tz = get_user_timezone(user.timezone, settings.DEFAULT_TIMEZONE)
        early_result = check_early_exit(checkout_time, user_tz, expected_end_hour=18)

        if early_result.is_early:
            active_shift.is_early_exit = True
            active_shift.early_exit_minutes = early_result.minutes_early

        self.db.flush()
        self.db.refresh(active_shift)
        return active_shift

    # ── Admin operations ────────────────────────────────────────────

    @transactional
    def admin_checkout_user(
        self, record_id: int, admin_user: User, checkout_data: AdminManualCheckout
    ) -> CheckInOut:
        """Admin manually checks out a user's record."""
        record = self.repo.get_by_id(record_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance record not found"
            )
        if record.check_out_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This record already has a checkout time"
            )

        checkout_time = checkout_data.checkout_time or datetime.utcnow()
        record.check_out_time = checkout_time
        record.modified_by_admin_id = admin_user.id
        record.admin_notes = checkout_data.admin_notes
        record.is_auto_checkout = False
        record.hours_worked = calculate_hours_worked(record.check_in_time, checkout_time)

        self.db.flush()
        self.db.refresh(record)
        return record

    @transactional
    def auto_checkout_pending_records(self) -> List[CheckInOut]:
        """Auto-checkout all records that have been open too long. Atomic operation."""
        cutoff_time = datetime.utcnow() - timedelta(hours=settings.AUTO_CHECKOUT_HOURS)
        pending_records = self.repo.get_pending_records(cutoff_time)

        closed_records = []
        for record in pending_records:
            auto_checkout_time = record.check_in_time + timedelta(hours=settings.AUTO_CHECKOUT_HOURS)
            record.check_out_time = auto_checkout_time
            record.is_auto_checkout = True
            record.admin_notes = f"Auto-checked out after {settings.AUTO_CHECKOUT_HOURS} hours"
            record.hours_worked = calculate_hours_worked(record.check_in_time, auto_checkout_time)
            closed_records.append(record)

        return closed_records

    # ── History & Reports ───────────────────────────────────────────

    def get_user_attendance_history(
        self, user_id: int, skip: int = 0, limit: int = 100,
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> list[CheckInOut]:
        """Get attendance history for a user."""
        return self.repo.get_user_history(user_id, skip, limit, start_date, end_date)

    def get_all_attendance(
        self, skip: int = 0, limit: int = 100,
        user_id: Optional[int] = None, pending_only: bool = False
    ) -> list[CheckInOut]:
        """Get all attendance records (admin)."""
        return self.repo.get_all_records(skip, limit, user_id, pending_only)

    def get_working_hours_summary(
        self, user_id: int, start_date: datetime, end_date: datetime
    ) -> dict:
        """Get working hours summary for a user within a date range."""
        records = self.repo.get_completed_in_range(user_id, start_date, end_date)
        records_data = [
            {"hours_worked": r.hours_worked, "shift_type": r.shift_type.value if r.shift_type else "regular"}
            for r in records
        ]
        hours = accumulate_hours_by_shift(records_data)
        hours["records_count"] = len(records)
        return hours

    def get_monthly_statistics(self, user_id: int, year: int, month: int) -> dict:
        """Get monthly attendance statistics for a user."""
        _, days_in_month = calendar.monthrange(year, month)
        month_start = datetime(year, month, 1, 0, 0, 0)
        month_end = datetime(year, month, days_in_month, 23, 59, 59)

        # Working days (excluding weekends)
        working_days = sum(
            1 for day in range(1, days_in_month + 1)
            if datetime(year, month, day).weekday() < 5
        )

        records = self.repo.get_all_in_range(user_id, month_start, month_end)

        # Unique days worked
        days_with_records = {r.check_in_time.date() for r in records}
        records_data = [
            {"hours_worked": r.hours_worked, "shift_type": r.shift_type.value if r.shift_type else "regular"}
            for r in records
        ]
        hours = accumulate_hours_by_shift(records_data)

        days_worked = len(days_with_records)
        days_absent = max(0, working_days - days_worked)
        avg_hours = hours["total_hours"] / days_worked if days_worked > 0 else 0
        attendance_pct = (days_worked / working_days * 100) if working_days > 0 else 0

        return {
            "year": year,
            "month": month,
            "month_name": calendar.month_name[month],
            "total_days_in_month": days_in_month,
            "working_days_in_month": working_days,
            "days_worked": days_worked,
            "days_absent": days_absent,
            **hours,
            "avg_hours_per_day": round(avg_hours, 2),
            "attendance_percentage": round(attendance_pct, 1)
        }




