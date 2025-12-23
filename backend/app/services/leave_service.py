from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.models.leave import Leave, LeaveType, LeaveStatus
from app.models.user import User
from app.schemas.leave import LeaveCreate, LeaveApproval
from datetime import datetime, date
from typing import List, Optional


def create_leave_request(db: Session, user: User, leave_data: LeaveCreate) -> Leave:
    """Create a new leave request."""
    # Check for overlapping leave requests
    existing = db.query(Leave).filter(
        Leave.user_id == user.id,
        Leave.status.in_([LeaveStatus.PENDING, LeaveStatus.APPROVED]),
        Leave.start_date <= leave_data.end_date,
        Leave.end_date >= leave_data.start_date
    ).first()
    
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
    
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return leave


def get_leave(db: Session, leave_id: int) -> Optional[Leave]:
    """Get a leave request by ID."""
    return db.query(Leave).filter(Leave.id == leave_id).first()


def get_user_leaves(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[LeaveStatus] = None
) -> List[Leave]:
    """Get leave requests for a user."""
    query = db.query(Leave).filter(Leave.user_id == user_id)
    
    if status_filter:
        query = query.filter(Leave.status == status_filter)
    
    return query.order_by(Leave.start_date.desc()).offset(skip).limit(limit).all()


def get_all_leaves(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[LeaveStatus] = None,
    user_id: Optional[int] = None
) -> List[Leave]:
    """Get all leave requests (admin only)."""
    query = db.query(Leave).options(joinedload(Leave.user))
    
    if status_filter:
        query = query.filter(Leave.status == status_filter)
    
    if user_id:
        query = query.filter(Leave.user_id == user_id)
    
    return query.order_by(Leave.created_at.desc()).offset(skip).limit(limit).all()


def approve_leave(
    db: Session,
    leave_id: int,
    admin_user: User,
    approval_data: LeaveApproval
) -> Leave:
    """Approve a leave request."""
    leave = get_leave(db, leave_id)
    
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    if leave.status != LeaveStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve leave with status {leave.status.value}"
        )
    
    leave.status = LeaveStatus.APPROVED
    leave.approved_by_id = admin_user.id
    leave.approved_at = datetime.utcnow()
    leave.admin_remarks = approval_data.admin_remarks
    
    db.commit()
    db.refresh(leave)
    return leave


def reject_leave(
    db: Session,
    leave_id: int,
    admin_user: User,
    approval_data: LeaveApproval
) -> Leave:
    """Reject a leave request."""
    leave = get_leave(db, leave_id)
    
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    if leave.status != LeaveStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject leave with status {leave.status.value}"
        )
    
    leave.status = LeaveStatus.REJECTED
    leave.approved_by_id = admin_user.id
    leave.approved_at = datetime.utcnow()
    leave.admin_remarks = approval_data.admin_remarks
    
    db.commit()
    db.refresh(leave)
    return leave


def cancel_leave(db: Session, leave_id: int, user: User) -> Leave:
    """Cancel a leave request (by the user who created it)."""
    leave = get_leave(db, leave_id)
    
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    if leave.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own leave requests"
        )
    
    if leave.status not in [LeaveStatus.PENDING, LeaveStatus.APPROVED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel leave with status {leave.status.value}"
        )
    
    # Don't allow cancelling if leave has already started
    if leave.start_date <= date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel leave that has already started"
        )
    
    leave.status = LeaveStatus.CANCELLED
    
    db.commit()
    db.refresh(leave)
    return leave


def get_leave_stats(db: Session, user_id: int) -> dict:
    """Get leave statistics for a user."""
    current_year = datetime.now().year
    year_start = date(current_year, 1, 1)
    year_end = date(current_year, 12, 31)
    
    # All leaves for the user
    all_leaves = db.query(Leave).filter(Leave.user_id == user_id).all()
    
    # This year's approved leaves
    approved_this_year = db.query(Leave).filter(
        Leave.user_id == user_id,
        Leave.status == LeaveStatus.APPROVED,
        Leave.start_date >= year_start,
        Leave.end_date <= year_end
    ).all()
    
    # Pending leaves
    pending = [l for l in all_leaves if l.status == LeaveStatus.PENDING]
    
    # Calculate totals
    total_days = sum(l.days_count for l in approved_this_year)
    
    return {
        "total_leaves_taken": len(approved_this_year),
        "total_days_taken": total_days,
        "pending_requests": len(pending),
        "approved_this_year": len(approved_this_year),
        "balances": []  # Leave balance would need a separate configuration for quotas
    }
