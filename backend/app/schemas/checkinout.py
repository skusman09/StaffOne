from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.schemas.auth import UserResponse
from app.models.checkinout import ShiftType


class CheckInCreate(BaseModel):
    """Schema for check-in creation."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_info: Optional[str] = None
    shift_type: ShiftType = ShiftType.REGULAR


class CheckOutCreate(BaseModel):
    """Schema for check-out creation."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_info: Optional[str] = None


class AdminManualCheckout(BaseModel):
    """Schema for admin manual checkout."""
    checkout_time: Optional[datetime] = None  # If None, use current time
    admin_notes: Optional[str] = None


class CheckInOutResponse(BaseModel):
    """Schema for check-in/out response."""
    id: int
    user_id: int
    check_in_time: datetime
    check_out_time: Optional[datetime]
    shift_type: ShiftType
    shift_id: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    checkout_latitude: Optional[float]
    checkout_longitude: Optional[float]
    device_info: Optional[str]
    is_location_valid: bool
    location_flag_reason: Optional[str]
    hours_worked: Optional[float]
    is_auto_checkout: bool
    admin_notes: Optional[str]
    created_at: datetime
    user: UserResponse

    class Config:
        from_attributes = True


class CheckInOutTodayResponse(BaseModel):
    """Schema for today's check-in/out status."""
    id: Optional[int]
    check_in_time: Optional[datetime]
    check_out_time: Optional[datetime]
    shift_type: Optional[ShiftType]
    hours_worked: Optional[float]
    can_check_in: bool
    can_check_out: bool
    active_shift_id: Optional[str]


class WorkingHoursSummary(BaseModel):
    """Summary of working hours."""
    date: str
    total_hours: float
    regular_hours: float
    overtime_hours: float
    break_hours: float
    records_count: int


class MonthlyStatistics(BaseModel):
    """Monthly attendance statistics."""
    year: int
    month: int
    month_name: str
    total_days_in_month: int
    working_days_in_month: int  # Excludes weekends
    days_worked: int
    days_absent: int
    total_hours: float
    regular_hours: float
    overtime_hours: float
    break_hours: float
    avg_hours_per_day: float
    attendance_percentage: float


