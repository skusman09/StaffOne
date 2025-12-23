from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import Optional
from app.models.leave import LeaveType, LeaveStatus
from app.schemas.auth import UserResponse


class LeaveCreate(BaseModel):
    """Schema for creating a leave request."""
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: Optional[str] = Field(None, max_length=1000)
    
    @field_validator('end_date')
    @classmethod
    def end_date_must_be_after_start(cls, v, info):
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError('end_date must be on or after start_date')
        return v


class LeaveApproval(BaseModel):
    """Schema for approving/rejecting a leave request."""
    admin_remarks: Optional[str] = Field(None, max_length=500)


class LeaveResponse(BaseModel):
    """Schema for leave response."""
    id: int
    user_id: int
    leave_type: LeaveType
    status: LeaveStatus
    start_date: date
    end_date: date
    days_count: int
    reason: Optional[str]
    admin_remarks: Optional[str]
    approved_by_id: Optional[int]
    approved_at: Optional[datetime]
    user: Optional[UserResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeaveBalanceSummary(BaseModel):
    """Summary of leave balance."""
    leave_type: LeaveType
    total_days: int
    used_days: int
    pending_days: int
    available_days: int


class UserLeaveStats(BaseModel):
    """User's leave statistics."""
    total_leaves_taken: int
    total_days_taken: int
    pending_requests: int
    approved_this_year: int
    balances: list[LeaveBalanceSummary]
