from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.database import get_db
from app.models.user import User
from app.utils.dependencies import get_current_user, get_current_admin_user
from app.services.holiday_service import (
    get_holidays, get_holiday, create_holiday, update_holiday, delete_holiday, get_holiday_by_date
)
from app.schemas.holiday import (
    HolidayCreate, HolidayUpdate, HolidayResponse, HolidayListResponse
)

router = APIRouter(prefix="/holidays", tags=["holidays"])


@router.get("", response_model=HolidayListResponse)
def list_holidays(
    year: Optional[int] = Query(None, description="Filter by year"),
    active_only: bool = Query(True, description="Show only active holidays"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of holidays.
    
    Anyone can view holidays list.
    """
    holidays = get_holidays(db, year=year, active_only=active_only, skip=skip, limit=limit)
    return HolidayListResponse(
        holidays=holidays,
        total=len(holidays),
        year=year
    )


@router.get("/{holiday_id}", response_model=HolidayResponse)
def get_holiday_by_id(
    holiday_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific holiday by ID."""
    holiday = get_holiday(db, holiday_id)
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    return holiday


@router.post("", response_model=HolidayResponse, status_code=201)
def create_new_holiday(
    holiday: HolidayCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new holiday. Admin only."""
    # Check if holiday already exists on that date
    existing = get_holiday_by_date(db, holiday.holiday_date)
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Holiday already exists on {holiday.holiday_date}: {existing.name}"
        )
    
    return create_holiday(db, holiday)


@router.put("/{holiday_id}", response_model=HolidayResponse)
def update_existing_holiday(
    holiday_id: int,
    holiday: HolidayUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update a holiday. Admin only."""
    # Check if new date conflicts
    if holiday.holiday_date:
        existing = get_holiday_by_date(db, holiday.holiday_date)
        if existing and existing.id != holiday_id:
            raise HTTPException(
                status_code=400,
                detail=f"Holiday already exists on {holiday.holiday_date}: {existing.name}"
            )
    
    updated = update_holiday(db, holiday_id, holiday)
    if not updated:
        raise HTTPException(status_code=404, detail="Holiday not found")
    return updated


@router.delete("/{holiday_id}", status_code=204)
def delete_existing_holiday(
    holiday_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a holiday. Admin only."""
    if not delete_holiday(db, holiday_id):
        raise HTTPException(status_code=404, detail="Holiday not found")
    return None
