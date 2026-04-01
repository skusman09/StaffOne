"""Holiday routes — CRUD for holidays."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import date

from app.models.user import User
from app.services.holiday_service import HolidayService
from app.container import get_holiday_service
from app.authorization.dependencies import require
from app.authorization.permissions import Permission
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
    current_user: User = Depends(require(Permission.VIEW_HOLIDAYS)),
    service: HolidayService = Depends(get_holiday_service)
):
    """Get list of holidays."""
    holidays = service.get_holidays(year=year, active_only=active_only, skip=skip, limit=limit)
    return HolidayListResponse(holidays=holidays, total=len(holidays), year=year)


@router.get("/{holiday_id}", response_model=HolidayResponse)
def get_holiday_by_id(
    holiday_id: int,
    current_user: User = Depends(require(Permission.VIEW_HOLIDAYS)),
    service: HolidayService = Depends(get_holiday_service)
):
    """Get a specific holiday by ID."""
    holiday = service.get_holiday(holiday_id)
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    return holiday


@router.post("", response_model=HolidayResponse, status_code=201)
def create_new_holiday(
    holiday: HolidayCreate,
    current_user: User = Depends(require(Permission.MANAGE_HOLIDAYS)),
    service: HolidayService = Depends(get_holiday_service)
):
    """Create a new holiday."""
    existing = service.get_holiday_by_date(holiday.holiday_date)
    if existing:
        raise HTTPException(status_code=400, detail=f"Holiday already exists on {holiday.holiday_date}: {existing.name}")
    return service.create_holiday(holiday)


@router.put("/{holiday_id}", response_model=HolidayResponse)
def update_existing_holiday(
    holiday_id: int,
    holiday: HolidayUpdate,
    current_user: User = Depends(require(Permission.MANAGE_HOLIDAYS)),
    service: HolidayService = Depends(get_holiday_service)
):
    """Update a holiday."""
    if holiday.holiday_date:
        existing = service.get_holiday_by_date(holiday.holiday_date)
        if existing and existing.id != holiday_id:
            raise HTTPException(status_code=400, detail=f"Holiday already exists on {holiday.holiday_date}: {existing.name}")
    updated = service.update_holiday(holiday_id, holiday)
    if not updated:
        raise HTTPException(status_code=404, detail="Holiday not found")
    return updated


@router.delete("/{holiday_id}", status_code=204)
def delete_existing_holiday(
    holiday_id: int,
    current_user: User = Depends(require(Permission.MANAGE_HOLIDAYS)),
    service: HolidayService = Depends(get_holiday_service)
):
    """Delete a holiday."""
    if not service.delete_holiday(holiday_id):
        raise HTTPException(status_code=404, detail="Holiday not found")
    return None
