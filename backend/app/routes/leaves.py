"""Leaves routes — leave requests, approval, rejection."""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional

from app.schemas.leave import LeaveCreate, LeaveApproval, LeaveResponse, UserLeaveStats
from app.models.leave import LeaveStatus
from app.models.user import User
from app.services.leave_service import LeaveService
from app.container import get_leave_service
from app.authorization.dependencies import require
from app.authorization.permissions import Permission
from app.authorization import policies

router = APIRouter(prefix="/leaves", tags=["leaves"])


# ── Employee endpoints ──────────────────────────────────────────────

@router.post("", response_model=LeaveResponse, status_code=status.HTTP_201_CREATED)
def request_leave(
    leave_data: LeaveCreate,
    current_user: User = Depends(require(Permission.CREATE_OWN_LEAVE)),
    service: LeaveService = Depends(get_leave_service)
):
    """Create a new leave request."""
    return service.create_leave_request(current_user, leave_data)


@router.get("", response_model=List[LeaveResponse])
def get_my_leaves(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status_filter: Optional[LeaveStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(require(Permission.VIEW_OWN_LEAVES)),
    service: LeaveService = Depends(get_leave_service)
):
    """Get my leave requests."""
    return service.get_user_leaves(current_user.id, skip, limit, status_filter)


@router.get("/stats", response_model=UserLeaveStats)
def get_my_leave_stats(
    current_user: User = Depends(require(Permission.VIEW_OWN_LEAVES)),
    service: LeaveService = Depends(get_leave_service)
):
    """Get my leave statistics for the current year."""
    stats = service.get_leave_stats(current_user.id)
    return UserLeaveStats(**stats)


@router.get("/{leave_id}", response_model=LeaveResponse)
def get_single_leave(
    leave_id: int,
    current_user: User = Depends(require(Permission.VIEW_OWN_LEAVES)),
    service: LeaveService = Depends(get_leave_service)
):
    """Get a specific leave request."""
    leave = service.get_leave(leave_id)
    if not leave:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")

    # Policy-based ownership check
    if leave.user_id != current_user.id:
        policies.require_permission(current_user, Permission.VIEW_ANY_LEAVES)

    return leave


@router.delete("/{leave_id}", response_model=LeaveResponse)
def cancel_my_leave(
    leave_id: int,
    current_user: User = Depends(require(Permission.CREATE_OWN_LEAVE)),
    service: LeaveService = Depends(get_leave_service)
):
    """Cancel a leave request."""
    return service.cancel_leave(leave_id, current_user)


# ── Admin endpoints ─────────────────────────────────────────────────

@router.get("/admin/all", response_model=List[LeaveResponse])
def get_all_leave_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status_filter: Optional[LeaveStatus] = Query(None, description="Filter by status"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    current_user: User = Depends(require(Permission.VIEW_ANY_LEAVES)),
    service: LeaveService = Depends(get_leave_service)
):
    """Get all leave requests."""
    return service.get_all_leaves(skip, limit, status_filter, user_id)


@router.patch("/{leave_id}/approve", response_model=LeaveResponse)
def approve_leave_request(
    leave_id: int,
    approval_data: LeaveApproval,
    current_user: User = Depends(require(Permission.APPROVE_LEAVE)),
    service: LeaveService = Depends(get_leave_service)
):
    """Approve a leave request."""
    return service.approve_leave(leave_id, current_user, approval_data)


@router.patch("/{leave_id}/reject", response_model=LeaveResponse)
def reject_leave_request(
    leave_id: int,
    approval_data: LeaveApproval,
    current_user: User = Depends(require(Permission.REJECT_LEAVE)),
    service: LeaveService = Depends(get_leave_service)
):
    """Reject a leave request."""
    return service.reject_leave(leave_id, current_user, approval_data)
