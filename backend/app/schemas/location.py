from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class LocationCreate(BaseModel):
    """Schema for creating a new location."""
    name: str = Field(..., min_length=1, max_length=255)
    address: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_meters: float = Field(default=100.0, gt=0, le=10000)


class LocationUpdate(BaseModel):
    """Schema for updating a location."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius_meters: Optional[float] = Field(None, gt=0, le=10000)
    is_active: Optional[bool] = None


class LocationResponse(BaseModel):
    """Schema for location response."""
    id: int
    name: str
    address: Optional[str]
    latitude: float
    longitude: float
    radius_meters: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LocationValidationResult(BaseModel):
    """Result of location validation."""
    is_valid: bool
    nearest_location: Optional[str]
    distance_meters: Optional[float]
    message: str
