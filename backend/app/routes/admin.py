"""Admin routes — API handlers for admin operations."""
import logging
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.schemas.auth import UserResponse, RoleUpdate
from app.schemas.checkinout import CheckInOutResponse, AdminManualCheckout
from app.models.user import User, Role
from app.models.checkinout import CheckInOut
from app.database import get_db

from app.services.attendance_service import AttendanceService
from app.container import get_attendance_service
from app.authorization.dependencies import require, handle_policy_violation
from app.authorization.permissions import Permission
from app.authorization import policies

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require(Permission.VIEW_ANY_USER)),
    db: Session = Depends(get_db)
):
    """Get all users."""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role_update: RoleUpdate,
    current_user: User = Depends(require(Permission.UPDATE_USER_ROLE)),
    db: Session = Depends(get_db)
):
    """Update a user's role."""
    if not policies.can_modify_user_role(current_user, user_id, role_update.role):
        raise handle_policy_violation(
            policies.PolicyViolation("Cannot modify role or demote self", status_code=400)
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.role = role_update.role
    db.commit()
    db.refresh(user)
    return user


@router.get("/attendance", response_model=List[CheckInOutResponse])
def get_all_attendance_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    pending_only: bool = Query(False, description="Show only pending records"),
    current_user: User = Depends(require(Permission.VIEW_ANY_ATTENDANCE)),
    service: AttendanceService = Depends(get_attendance_service)
):
    """Get all attendance records."""
    return service.get_all_attendance(skip, limit, user_id, pending_only)


@router.patch("/attendance/{record_id}/checkout", response_model=CheckInOutResponse)
def admin_manual_checkout(
    record_id: int,
    checkout_data: AdminManualCheckout,
    current_user: User = Depends(require(Permission.MANAGE_ATTENDANCE)),
    service: AttendanceService = Depends(get_attendance_service)
):
    """Manually checkout an attendance record."""
    return service.admin_checkout_user(record_id, current_user, checkout_data)


@router.post("/attendance/auto-checkout", response_model=List[CheckInOutResponse])
def trigger_auto_checkout(
    current_user: User = Depends(require(Permission.MANAGE_ATTENDANCE)),
    service: AttendanceService = Depends(get_attendance_service)
):
    """Trigger auto-checkout for all pending records exceeding the time limit."""
    return service.auto_checkout_pending_records()


@router.patch("/attendance/{record_id}/notes", response_model=CheckInOutResponse)
def update_attendance_notes(
    record_id: int,
    admin_notes: str = Query(..., description="Admin notes to add"),
    current_user: User = Depends(require(Permission.MANAGE_ATTENDANCE)),
    db: Session = Depends(get_db)
):
    """Add or update admin notes on an attendance record. (TODO: move to service logic)"""
    record = db.query(CheckInOut).filter(CheckInOut.id == record_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")

    record.admin_notes = admin_notes
    record.modified_by_admin_id = current_user.id
    db.commit()
    db.refresh(record)
    return record
