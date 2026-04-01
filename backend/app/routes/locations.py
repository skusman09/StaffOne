"""Location routes — office location CRUD and geofence validation."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List

from app.schemas.location import (
    LocationCreate, LocationUpdate, LocationResponse, LocationValidationResult
)
from app.services.location_service import LocationService
from app.container import get_location_service
from app.authorization.dependencies import require
from app.authorization.permissions import Permission
from app.models.user import User

router = APIRouter(prefix="/locations", tags=["locations"])


@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_new_location(
    location_data: LocationCreate,
    current_user: User = Depends(require(Permission.MANAGE_LOCATIONS)),
    service: LocationService = Depends(get_location_service)
):
    """Create a new office location."""
    return service.create_location(location_data)


@router.get("", response_model=List[LocationResponse])
def list_locations(
    active_only: bool = Query(False, description="Show only active locations"),
    current_user: User = Depends(require(Permission.VIEW_LOCATIONS)),
    service: LocationService = Depends(get_location_service)
):
    """List all office locations."""
    return service.get_all_locations(active_only)


@router.get("/{location_id}", response_model=LocationResponse)
def get_single_location(
    location_id: int,
    current_user: User = Depends(require(Permission.VIEW_LOCATIONS)),
    service: LocationService = Depends(get_location_service)
):
    """Get a specific location by ID."""
    location = service.get_location(location_id)
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return location


@router.put("/{location_id}", response_model=LocationResponse)
def update_existing_location(
    location_id: int,
    location_data: LocationUpdate,
    current_user: User = Depends(require(Permission.MANAGE_LOCATIONS)),
    service: LocationService = Depends(get_location_service)
):
    """Update a location."""
    return service.update_location(location_id, location_data)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_location(
    location_id: int,
    current_user: User = Depends(require(Permission.MANAGE_LOCATIONS)),
    service: LocationService = Depends(get_location_service)
):
    """Delete a location."""
    service.delete_location(location_id)
    return None


@router.post("/validate", response_model=LocationValidationResult)
def validate_current_location(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    current_user: User = Depends(require(Permission.VIEW_LOCATIONS)),
    service: LocationService = Depends(get_location_service)
):
    """Check if coordinates are within an allowed office location."""
    return service.validate_location(latitude, longitude)
