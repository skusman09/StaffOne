from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models.compoff import CompOff, CompOffStatus
from app.models.checkinout import CheckInOut
from app.models.user import User
from app.schemas.compoff import CompOffCreate, CompOffResponse, CompOffReview, CompOffListResponse
from app.utils.dependencies import get_current_user, get_current_admin_user
from app.core.config import settings

router = APIRouter(prefix="/compoff", tags=["comp-off"])


def calculate_ot_hours(db: Session, user_id: int, start_date: datetime, end_date: datetime) -> float:
    """Calculate total overtime hours for a user in a date range."""
    records = db.query(CheckInOut).filter(
        CheckInOut.user_id == user_id,
        CheckInOut.check_in_time >= start_date,
        CheckInOut.check_in_time <= end_date,
        CheckInOut.check_out_time.isnot(None)
    ).all()
    
    total_ot_hours = 0.0
    standard_hours = settings.OFFICE_STANDARD_HOURS
    
    for record in records:
        if record.hours_worked and record.hours_worked > standard_hours:
            total_ot_hours += record.hours_worked - standard_hours
            
    return round(total_ot_hours, 2)


@router.post("/request", response_model=CompOffResponse, status_code=201)
def request_compoff(
    data: CompOffCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request comp-off conversion for overtime hours."""
    # Calculate OT hours in the range
    ot_hours = calculate_ot_hours(db, current_user.id, data.ot_start_date, data.ot_end_date)
    
    if ot_hours < 4:  # Minimum 4 hours OT required
        raise HTTPException(status_code=400, detail="Minimum 4 overtime hours required for comp-off")
    
    # Calculate comp-off days (8 hours = 1 day)
    comp_off_days = round(ot_hours / settings.OFFICE_STANDARD_HOURS, 2)
    
    compoff = CompOff(
        user_id=current_user.id,
        ot_hours=ot_hours,
        comp_off_days=comp_off_days,
        ot_start_date=data.ot_start_date,
        ot_end_date=data.ot_end_date,
        reason=data.reason
    )
    db.add(compoff)
    db.commit()
    db.refresh(compoff)
    return compoff


@router.get("/my-requests", response_model=CompOffListResponse)
def get_my_compoff_requests(
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's comp-off requests."""
    query = db.query(CompOff).filter(CompOff.user_id == current_user.id)
    
    if status:
        query = query.filter(CompOff.status == status)
    
    items = query.order_by(CompOff.request_date.desc()).all()
    return CompOffListResponse(comp_offs=items, total=len(items))


@router.get("/admin/all", response_model=CompOffListResponse)
def get_all_compoff_requests(
    status: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all comp-off requests. Admin only."""
    query = db.query(CompOff).options(joinedload(CompOff.user))
    
    if status:
        query = query.filter(CompOff.status == status)
    if user_id:
        query = query.filter(CompOff.user_id == user_id)
    
    items = query.order_by(CompOff.request_date.desc()).all()
    return CompOffListResponse(comp_offs=items, total=len(items))


@router.patch("/{compoff_id}/review", response_model=CompOffResponse)
def review_compoff(
    compoff_id: int,
    review: CompOffReview,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Approve or reject comp-off request. Admin only."""
    compoff = db.query(CompOff).filter(CompOff.id == compoff_id).first()
    if not compoff:
        raise HTTPException(status_code=404, detail="Comp-off request not found")
    
    if compoff.status != CompOffStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending requests can be reviewed")
    
    compoff.status = review.status
    compoff.admin_remarks = review.admin_remarks
    compoff.reviewed_by_id = current_user.id
    compoff.review_date = datetime.utcnow()
    
    db.commit()
    db.refresh(compoff)
    return compoff


@router.get("/balance")
def get_compoff_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's available comp-off balance."""
    approved = db.query(func.sum(CompOff.comp_off_days)).filter(
        CompOff.user_id == current_user.id,
        CompOff.status == CompOffStatus.APPROVED
    ).scalar() or 0
    
    used = db.query(func.sum(CompOff.comp_off_days)).filter(
        CompOff.user_id == current_user.id,
        CompOff.status == CompOffStatus.USED
    ).scalar() or 0
    
    return {
        "approved_days": float(approved),
        "used_days": float(used),
        "available_days": float(approved) - float(used)
    }
