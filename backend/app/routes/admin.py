from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.auth import UserResponse, RoleUpdate
from app.schemas.checkinout import CheckInOutResponse, AdminManualCheckout
from app.models.user import User, Role
from app.services.attendance_service import (
    get_all_attendance,
    admin_checkout_user,
    auto_checkout_pending_records
)
from app.utils.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)."""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role_update: RoleUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update a user's role (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent demoting yourself
    if user.id == current_user.id and role_update.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself from admin role"
        )
    
    user.role = role_update.role
    db.commit()
    db.refresh(user)
    
    return user


@router.get("/attendance", response_model=List[CheckInOutResponse])
def get_all_attendance_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    pending_only: bool = Query(False, description="Show only pending (unclosed) records"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all attendance records (admin only).
    
    Use pending_only=true to see records that haven't been checked out yet.
    """
    records = get_all_attendance(db, skip, limit, user_id, pending_only)
    return records


@router.patch("/attendance/{record_id}/checkout", response_model=CheckInOutResponse)
def admin_manual_checkout(
    record_id: int,
    checkout_data: AdminManualCheckout,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Manually checkout an attendance record (admin only).
    
    Use this when an employee forgot to check out.
    Optionally specify a checkout_time, otherwise uses current time.
    """
    record = admin_checkout_user(db, record_id, current_user, checkout_data)
    return record


@router.post("/attendance/auto-checkout", response_model=List[CheckInOutResponse])
def trigger_auto_checkout(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Trigger auto-checkout for all pending records exceeding the time limit.
    
    Closes all attendance records that have been open longer than AUTO_CHECKOUT_HOURS.
    Returns list of records that were auto-closed.
    """
    closed_records = auto_checkout_pending_records(db)
    return closed_records


@router.patch("/attendance/{record_id}/notes", response_model=CheckInOutResponse)
def update_attendance_notes(
    record_id: int,
    admin_notes: str = Query(..., description="Admin notes to add"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Add or update admin notes on an attendance record."""
    from app.models.checkinout import CheckInOut
    
    record = db.query(CheckInOut).filter(CheckInOut.id == record_id).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    record.admin_notes = admin_notes
    record.modified_by_admin_id = current_user.id
    db.commit()
    db.refresh(record)
    
    return record
