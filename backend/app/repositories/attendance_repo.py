"""
Attendance repository — all CheckInOut-related database queries.
"""
import calendar
from typing import Optional, List
from datetime import datetime, timedelta

from sqlalchemy.orm import Session, joinedload

from app.models.checkinout import CheckInOut, ShiftType
from app.repositories import BaseRepository


class AttendanceRepository(BaseRepository):
    """Data access layer for CheckInOut (attendance) model."""

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_id(self, record_id: int) -> Optional[CheckInOut]:
        """Get attendance record by ID."""
        return self.db.query(CheckInOut).filter(CheckInOut.id == record_id).first()

    def get_today_record(self, user_id: int, today_start: datetime, today_end: datetime) -> Optional[CheckInOut]:
        """Get today's regular shift record for a user."""
        return self.db.query(CheckInOut).filter(
            CheckInOut.user_id == user_id,
            CheckInOut.check_in_time >= today_start,
            CheckInOut.check_in_time <= today_end,
            CheckInOut.shift_type == ShiftType.REGULAR
        ).order_by(CheckInOut.check_in_time.desc()).first()

    def get_active_shift(self, user_id: int) -> Optional[CheckInOut]:
        """Get any active (unclosed) regular shift for a user."""
        return self.db.query(CheckInOut).filter(
            CheckInOut.user_id == user_id,
            CheckInOut.check_out_time.is_(None),
            CheckInOut.shift_type == ShiftType.REGULAR
        ).order_by(CheckInOut.check_in_time.desc()).first()

    def get_pending_records(self, cutoff_time: datetime) -> List[CheckInOut]:
        """Get all unclosed records older than cutoff time."""
        return self.db.query(CheckInOut).filter(
            CheckInOut.check_out_time.is_(None),
            CheckInOut.check_in_time < cutoff_time
        ).all()

    def get_user_history(
        self, user_id: int, skip: int = 0, limit: int = 100,
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[CheckInOut]:
        """Get attendance history for a user with optional date range filtering."""
        query = self.db.query(CheckInOut).filter(CheckInOut.user_id == user_id)

        if start_date:
            query = query.filter(CheckInOut.check_in_time >= start_date)
        if end_date:
            end_datetime = datetime.combine(end_date.date(), datetime.max.time()) if isinstance(end_date, datetime) else end_date
            query = query.filter(CheckInOut.check_in_time <= end_datetime)

        return query.order_by(CheckInOut.check_in_time.desc()).offset(skip).limit(limit).all()

    def get_all_records(
        self, skip: int = 0, limit: int = 100,
        user_id: Optional[int] = None, pending_only: bool = False
    ) -> List[CheckInOut]:
        """Get all attendance records (admin), with optional filters."""
        query = self.db.query(CheckInOut).options(joinedload(CheckInOut.user))

        if user_id:
            query = query.filter(CheckInOut.user_id == user_id)
        if pending_only:
            query = query.filter(CheckInOut.check_out_time.is_(None))

        return query.order_by(CheckInOut.check_in_time.desc()).offset(skip).limit(limit).all()

    def get_completed_in_range(
        self, user_id: int, start_date: datetime, end_date: datetime
    ) -> List[CheckInOut]:
        """Get completed records with hours_worked in a date range."""
        return self.db.query(CheckInOut).filter(
            CheckInOut.user_id == user_id,
            CheckInOut.check_in_time >= start_date,
            CheckInOut.check_in_time <= end_date,
            CheckInOut.hours_worked.isnot(None)
        ).all()

    def get_all_in_range(
        self, user_id: int, start_date: datetime, end_date: datetime
    ) -> List[CheckInOut]:
        """Get all records (including incomplete) in a date range."""
        return self.db.query(CheckInOut).filter(
            CheckInOut.user_id == user_id,
            CheckInOut.check_in_time >= start_date,
            CheckInOut.check_in_time <= end_date
        ).all()
