"""
Leave service — business logic for leave management.

Architecture:
- Accepts ILeaveRepository via constructor (DIP)
- Delegates validation to domain/leave_policy (pure functions)
- Uses @transactional for consistent transaction management
"""
import logging
from typing import Optional, List
from datetime import datetime, date

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.leave import Leave, LeaveType, LeaveStatus
from app.models.user import User
from app.schemas.leave import LeaveCreate, LeaveApproval
from app.core.transaction import transactional
from app.interfaces.repositories import ILeaveRepository
from app.repositories.leave_repo import LeaveRepository
from app.domain.leave_policy import validate_cancellation, validate_status_transition

logger = logging.getLogger(__name__)


class LeaveService:
    """Handles all leave-related business logic."""

    def __init__(self, db: Session, repo: ILeaveRepository = None):
        self.db = db
        self.repo = repo or LeaveRepository(db)

    @transactional
    def create_leave_request(self, user: User, leave_data: LeaveCreate) -> Leave:
        """Create a new leave request with overlap validation."""
        existing = self.repo.get_overlapping(user.id, leave_data.start_date, leave_data.end_date)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You already have a leave request from {existing.start_date} to {existing.end_date}"
            )

        leave = Leave(
            user_id=user.id,
            leave_type=leave_data.leave_type,
            start_date=leave_data.start_date,
            end_date=leave_data.end_date,
            reason=leave_data.reason
        )

        self.repo.add(leave)
        self.db.flush()
        self.db.refresh(leave)
        return leave

    def get_leave(self, leave_id: int) -> Optional[Leave]:
        """Get a leave request by ID."""
        return self.repo.get_by_id(leave_id)

    def get_user_leaves(
        self, user_id: int, skip: int = 0, limit: int = 100,
        status_filter: Optional[LeaveStatus] = None
    ) -> List[Leave]:
        """Get leave requests for a user."""
        return self.repo.get_user_leaves(user_id, skip, limit, status_filter)

    def get_all_leaves(
        self, skip: int = 0, limit: int = 100,
        status_filter: Optional[LeaveStatus] = None,
        user_id: Optional[int] = None
    ) -> List[Leave]:
        """Get all leave requests (admin)."""
        return self.repo.get_all_leaves(skip, limit, status_filter, user_id)

    @transactional
    def approve_leave(self, leave_id: int, admin_user: User, approval_data: LeaveApproval) -> Leave:
        """Approve a leave request."""
        leave = self.repo.get_by_id(leave_id)
        if not leave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave request not found"
            )

        # Domain validation: check status transition
        if not validate_status_transition(leave.status.value, "approved"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve leave with status {leave.status.value}"
            )

        leave.status = LeaveStatus.APPROVED
        leave.approved_by_id = admin_user.id
        leave.approved_at = datetime.utcnow()
        leave.admin_remarks = approval_data.admin_remarks
        return leave

    @transactional
    def reject_leave(self, leave_id: int, admin_user: User, approval_data: LeaveApproval) -> Leave:
        """Reject a leave request."""
        leave = self.repo.get_by_id(leave_id)
        if not leave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave request not found"
            )

        if not validate_status_transition(leave.status.value, "rejected"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject leave with status {leave.status.value}"
            )

        leave.status = LeaveStatus.REJECTED
        leave.approved_by_id = admin_user.id
        leave.approved_at = datetime.utcnow()
        leave.admin_remarks = approval_data.admin_remarks
        return leave

    @transactional
    def cancel_leave(self, leave_id: int, user: User) -> Leave:
        """Cancel a leave request (by the user who created it)."""
        leave = self.repo.get_by_id(leave_id)
        if not leave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave request not found"
            )

        # Domain validation
        cancel_check = validate_cancellation(
            leave_status=leave.status.value,
            leave_start_date=leave.start_date,
            leave_user_id=leave.user_id,
            requesting_user_id=user.id,
        )

        if not cancel_check.can_cancel:
            status_code = (
                status.HTTP_403_FORBIDDEN
                if "only cancel your own" in (cancel_check.reason or "")
                else status.HTTP_400_BAD_REQUEST
            )
            raise HTTPException(status_code=status_code, detail=cancel_check.reason)

        leave.status = LeaveStatus.CANCELLED
        return leave

    def get_leave_stats(self, user_id: int) -> dict:
        """Get leave statistics for a user for the current year."""
        current_year = datetime.now().year
        year_start = date(current_year, 1, 1)
        year_end = date(current_year, 12, 31)

        all_leaves = self.repo.get_all_for_user(user_id)
        approved_this_year = self.repo.get_approved_in_range(user_id, year_start, year_end)
        pending = [l for l in all_leaves if l.status == LeaveStatus.PENDING]
        total_days = sum(l.days_count for l in approved_this_year)

        return {
            "total_leaves_taken": len(approved_this_year),
            "total_days_taken": total_days,
            "pending_requests": len(pending),
            "approved_this_year": len(approved_this_year),
            "balances": []
        }




