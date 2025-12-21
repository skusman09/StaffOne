from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.leave import LeaveCreate, LeaveApproval, LeaveResponse, UserLeaveStats
from app.models.leave import LeaveStatus
from app.services.leave_service import (
    create_leave_request,
    get_leave,
    get_user_leaves,
    get_all_leaves,
    approve_leave,
    reject_leave,
    cancel_leave,
    get_leave_stats
)
from app.utils.dependencies import get_current_user, get_current_admin_user
from app.models.user import User

router = APIRouter(prefix="/leaves", tags=["leaves"])


# Employee endpoints
@router.post("", response_model=LeaveResponse, status_code=status.HTTP_201_CREATED)
def request_leave(
    leave_data: LeaveCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new leave request.
    
    Leave types: annual, sick, casual, unpaid, maternity, paternity, bereavement, other
    """
    leave = create_leave_request(db, current_user, leave_data)
    return leave


@router.get("", response_model=List[LeaveResponse])
def get_my_leaves(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status_filter: Optional[LeaveStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get my leave requests."""
    leaves = get_user_leaves(db, current_user.id, skip, limit, status_filter)
    return leaves


@router.get("/stats", response_model=UserLeaveStats)
def get_my_leave_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get my leave statistics for the current year."""
    stats = get_leave_stats(db, current_user.id)
    return UserLeaveStats(**stats)


@router.get("/{leave_id}", response_model=LeaveResponse)
def get_single_leave(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific leave request."""
    leave = get_leave(db, leave_id)
    
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    # Users can only view their own leaves (unless admin)
    if leave.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own leave requests"
        )
    
    return leave


@router.delete("/{leave_id}", response_model=LeaveResponse)
def cancel_my_leave(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a leave request.
    
    Can only cancel pending or approved leaves that haven't started yet.
    """
    leave = cancel_leave(db, leave_id, current_user)
    return leave


# Admin endpoints
@router.get("/admin/all", response_model=List[LeaveResponse])
def get_all_leave_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status_filter: Optional[LeaveStatus] = Query(None, description="Filter by status"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all leave requests (admin only)."""
    leaves = get_all_leaves(db, skip, limit, status_filter, user_id)
    return leaves


@router.patch("/{leave_id}/approve", response_model=LeaveResponse)
def approve_leave_request(
    leave_id: int,
    approval_data: LeaveApproval,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Approve a leave request (admin only)."""
    leave = approve_leave(db, leave_id, current_user, approval_data)
    return leave


@router.patch("/{leave_id}/reject", response_model=LeaveResponse)
def reject_leave_request(
    leave_id: int,
    approval_data: LeaveApproval,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Reject a leave request (admin only)."""
    leave = reject_leave(db, leave_id, current_user, approval_data)
    return leave
