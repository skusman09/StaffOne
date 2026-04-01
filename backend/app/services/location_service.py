"""
Location service — business logic for geofencing and office locations.

Architecture:
- Class-based service with Dependency Injection
- Uses @transactional for consistent transaction management
"""
import logging
import math
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate, LocationValidationResult
from app.core.config import settings
from app.core.transaction import transactional

logger = logging.getLogger(__name__)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the distance between two points on Earth using Haversine formula."""
    R = 6371000  # Earth's radius in meters
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat / 2) ** 2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


class LocationService:
    """Handles all location and geofencing operations."""

    def __init__(self, db: Session):
        self.db = db

    @transactional
    def create_location(self, location_data: LocationCreate) -> Location:
        """Create a new office location."""
        location = Location(
            name=location_data.name,
            address=location_data.address,
            latitude=location_data.latitude,
            longitude=location_data.longitude,
            radius_meters=location_data.radius_meters,
            is_active=True
        )
        self.db.add(location)
        self.db.flush()
        self.db.refresh(location)
        return location

    def get_location(self, location_id: int) -> Optional[Location]:
        """Get a specific location by ID."""
        return self.db.query(Location).filter(Location.id == location_id).first()

    def get_all_locations(self, active_only: bool = False) -> List[Location]:
        """Get all configured office locations."""
        query = self.db.query(Location)
        if active_only:
            query = query.filter(Location.is_active == True)
        return query.order_by(Location.name).all()

    @transactional
    def update_location(self, location_id: int, location_data: LocationUpdate) -> Location:
        """Update an existing office location."""
        location = self.get_location(location_id)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found"
            )

        update_data = location_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(location, field, value)

        self.db.flush()
        self.db.refresh(location)
        return location

    @transactional
    def delete_location(self, location_id: int) -> bool:
        """Delete an office location."""
        location = self.get_location(location_id)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found"
            )

        self.db.delete(location)
        return True

    def validate_location(self, latitude: float, longitude: float) -> LocationValidationResult:
        """Check if coordinates fall within any active geofence."""
        active_locations = self.get_all_locations(active_only=True)

        if not active_locations:
            return LocationValidationResult(
                is_valid=True,
                nearest_location=None,
                distance_meters=None,
                message="No office locations configured. Check-in allowed anywhere."
            )

        nearest_location: Optional[Location] = None
        min_distance: float = float('inf')
        is_within_any = False

        for location in active_locations:
            distance = haversine_distance(
                latitude, longitude,
                location.latitude, location.longitude
            )
            if distance < min_distance:
                min_distance = distance
                nearest_location = location

            if distance <= location.radius_meters:
                is_within_any = True

        if is_within_any:
            return LocationValidationResult(
                is_valid=True,
                nearest_location=nearest_location.name if nearest_location else None,
                distance_meters=round(min_distance, 2),
                message=f"Within {nearest_location.name} geofence."
            )
        else:
            return LocationValidationResult(
                is_valid=False,
                nearest_location=nearest_location.name if nearest_location else None,
                distance_meters=round(min_distance, 2),
                message=f"Outside allowed area. Nearest: {nearest_location.name} ({round(min_distance)}m away)."
            )

    def validate_checkin_location(
        self, latitude: Optional[float], longitude: Optional[float]
    ) -> Tuple[bool, Optional[str]]:
        """Validate check-in payload location against active geofences."""
        if not settings.GEOFENCING_ENABLED:
            return True, None

        if latitude is None or longitude is None:
            return False, "Location not provided"

        result = self.validate_location(latitude, longitude)
        if result.is_valid:
            return True, None
        else:
            return False, result.message


# ── Backward-compatible module-level functions ──────────────────────

def create_location(db: Session, location_data: LocationCreate) -> Location:
    return LocationService(db).create_location(location_data)

def get_location(db: Session, location_id: int) -> Optional[Location]:
    return LocationService(db).get_location(location_id)

def get_all_locations(db: Session, active_only: bool = False) -> List[Location]:
    return LocationService(db).get_all_locations(active_only)

def update_location(db: Session, location_id: int, location_data: LocationUpdate) -> Location:
    return LocationService(db).update_location(location_id, location_data)

def delete_location(db: Session, location_id: int) -> bool:
    return LocationService(db).delete_location(location_id)

def validate_location(db: Session, latitude: float, longitude: float) -> LocationValidationResult:
    return LocationService(db).validate_location(latitude, longitude)

def validate_checkin_location(db: Session, latitude: Optional[float], longitude: Optional[float]) -> Tuple[bool, Optional[str]]:
    return LocationService(db).validate_checkin_location(latitude, longitude)
