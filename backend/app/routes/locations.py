from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.location import (
    LocationCreate,
    LocationUpdate,
    LocationResponse,
    LocationValidationResult
)
from app.services.location_service import (
    create_location,
    get_location,
    get_all_locations,
    update_location,
    delete_location,
    validate_location
)
from app.utils.dependencies import get_current_user, get_current_admin_user
from app.models.user import User

router = APIRouter(prefix="/locations", tags=["locations"])


# Admin endpoints for managing locations
@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_new_location(
    location_data: LocationCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new office location (admin only).
    
    The radius_meters defines the geofence - check-ins within this radius
    from the center point (latitude, longitude) are considered valid.
    """
    location = create_location(db, location_data)
    return location


@router.get("", response_model=List[LocationResponse])
def list_locations(
    active_only: bool = Query(False, description="Show only active locations"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all office locations.
    
    Available to all authenticated users.
    """
    locations = get_all_locations(db, active_only)
    return locations


@router.get("/{location_id}", response_model=LocationResponse)
def get_single_location(
    location_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific location by ID."""
    location = get_location(db, location_id)
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    return location


@router.put("/{location_id}", response_model=LocationResponse)
def update_existing_location(
    location_id: int,
    location_data: LocationUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update a location (admin only)."""
    location = update_location(db, location_id, location_data)
    return location


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_location(
    location_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a location (admin only)."""
    delete_location(db, location_id)
    return None


@router.post("/validate", response_model=LocationValidationResult)
def validate_current_location(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if the given coordinates are within an allowed office location.
    
    Returns validation result with nearest location and distance.
    """
    result = validate_location(db, latitude, longitude)
    return result
