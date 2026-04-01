"""
Leave repository — all Leave-related database queries.
"""
from typing import Optional, List
from datetime import date

from sqlalchemy.orm import Session, joinedload

from app.models.leave import Leave, LeaveStatus
from app.repositories import BaseRepository


class LeaveRepository(BaseRepository):
    """Data access layer for Leave model."""

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_id(self, leave_id: int) -> Optional[Leave]:
        """Get leave request by ID."""
        return self.db.query(Leave).filter(Leave.id == leave_id).first()

    def get_overlapping(self, user_id: int, start_date: date, end_date: date) -> Optional[Leave]:
        """Check for overlapping pending/approved leave requests."""
        return self.db.query(Leave).filter(
            Leave.user_id == user_id,
            Leave.status.in_([LeaveStatus.PENDING, LeaveStatus.APPROVED]),
            Leave.start_date <= end_date,
            Leave.end_date >= start_date
        ).first()

    def get_user_leaves(
        self, user_id: int, skip: int = 0, limit: int = 100,
        status_filter: Optional[LeaveStatus] = None
    ) -> List[Leave]:
        """Get leave requests for a user."""
        query = self.db.query(Leave).filter(Leave.user_id == user_id)
        if status_filter:
            query = query.filter(Leave.status == status_filter)
        return query.order_by(Leave.start_date.desc()).offset(skip).limit(limit).all()

    def get_all_leaves(
        self, skip: int = 0, limit: int = 100,
        status_filter: Optional[LeaveStatus] = None,
        user_id: Optional[int] = None
    ) -> List[Leave]:
        """Get all leave requests (admin)."""
        query = self.db.query(Leave).options(joinedload(Leave.user))
        if status_filter:
            query = query.filter(Leave.status == status_filter)
        if user_id:
            query = query.filter(Leave.user_id == user_id)
        return query.order_by(Leave.created_at.desc()).offset(skip).limit(limit).all()

    def get_all_for_user(self, user_id: int) -> List[Leave]:
        """Get all leave records for a user (all statuses)."""
        return self.db.query(Leave).filter(Leave.user_id == user_id).all()

    def get_approved_in_range(self, user_id: int, start: date, end: date) -> List[Leave]:
        """Get approved leaves in a date range."""
        return self.db.query(Leave).filter(
            Leave.user_id == user_id,
            Leave.status == LeaveStatus.APPROVED,
            Leave.start_date >= start,
            Leave.end_date <= end
        ).all()
