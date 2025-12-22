from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class HolidayBase(BaseModel):
    """Base schema for holiday data."""
    holiday_date: date = Field(..., description="Date of the holiday")
    name: str = Field(..., max_length=100, description="Name of the holiday")
    description: Optional[str] = Field(None, description="Description of the holiday")


class HolidayCreate(HolidayBase):
    """Schema for creating a holiday."""
    pass


class HolidayUpdate(BaseModel):
    """Schema for updating a holiday."""
    holiday_date: Optional[date] = None
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class HolidayResponse(HolidayBase):
    """Schema for holiday response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HolidayListResponse(BaseModel):
    """Schema for list of holidays."""
    holidays: list[HolidayResponse]
    total: int
    year: Optional[int] = None
