from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate, LocationValidationResult
from app.core.config import settings
from typing import List, Optional, Tuple
import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the distance between two points on Earth using Haversine formula.
    
    Returns distance in meters.
    """
    # Earth's radius in meters
    R = 6371000
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = math.sin(delta_lat / 2) ** 2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def create_location(db: Session, location_data: LocationCreate) -> Location:
    """Create a new location."""
    location = Location(
        name=location_data.name,
        address=location_data.address,
        latitude=location_data.latitude,
        longitude=location_data.longitude,
        radius_meters=location_data.radius_meters
    )
    
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


def get_location(db: Session, location_id: int) -> Optional[Location]:
    """Get a location by ID."""
    return db.query(Location).filter(Location.id == location_id).first()


def get_all_locations(db: Session, active_only: bool = False) -> List[Location]:
    """Get all locations."""
    query = db.query(Location)
    if active_only:
        query = query.filter(Location.is_active == True)
    return query.order_by(Location.name).all()


def update_location(db: Session, location_id: int, location_data: LocationUpdate) -> Location:
    """Update a location."""
    location = get_location(db, location_id)
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    # Update only provided fields
    update_data = location_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(location, field, value)
    
    db.commit()
    db.refresh(location)
    return location


def delete_location(db: Session, location_id: int) -> bool:
    """Delete a location."""
    location = get_location(db, location_id)
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    db.delete(location)
    db.commit()
    return True


def validate_location(
    db: Session,
    latitude: float,
    longitude: float
) -> LocationValidationResult:
    """Validate if the given coordinates are within any active location's geofence.
    
    Returns validation result with nearest location and distance.
    """
    active_locations = get_all_locations(db, active_only=True)
    
    if not active_locations:
        # No locations configured - allow all
        return LocationValidationResult(
            is_valid=True,
            nearest_location=None,
            distance_meters=None,
            message="No office locations configured. Check-in allowed anywhere."
        )
    
    # Find nearest location and check if within any geofence
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
    db: Session,
    latitude: Optional[float],
    longitude: Optional[float]
) -> Tuple[bool, Optional[str]]:
    """Validate check-in location and return (is_valid, reason).
    
    Used by attendance service to flag check-ins.
    Returns (True, None) if valid or geofencing disabled.
    Returns (False, reason) if invalid.
    """
    if not settings.GEOFENCING_ENABLED:
        return True, None
    
    if latitude is None or longitude is None:
        return False, "Location not provided"
    
    result = validate_location(db, latitude, longitude)
    
    if result.is_valid:
        return True, None
    else:
        return False, result.message
