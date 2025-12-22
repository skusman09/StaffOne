from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class SalaryStatusEnum(str, Enum):
    """Salary record status."""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"


# ===== Salary Config Schemas =====

class SalaryConfigBase(BaseModel):
    """Base schema for salary configuration."""
    monthly_base_salary: float = Field(..., gt=0, description="Monthly base salary")
    hourly_rate: Optional[float] = Field(None, gt=0, description="Hourly rate (auto-calculated if not set)")
    overtime_multiplier: float = Field(1.5, gt=0, description="Overtime pay multiplier")
    deduction_rate_per_hour: float = Field(1.0, ge=0, description="Hourly deduction rate for undertime")


class SalaryConfigCreate(SalaryConfigBase):
    """Schema for creating salary config."""
    user_id: int
    effective_from: date


class SalaryConfigUpdate(BaseModel):
    """Schema for updating salary config."""
    monthly_base_salary: Optional[float] = Field(None, gt=0)
    hourly_rate: Optional[float] = Field(None, gt=0)
    overtime_multiplier: Optional[float] = Field(None, gt=0)
    deduction_rate_per_hour: Optional[float] = Field(None, ge=0)


class SalaryConfigResponse(SalaryConfigBase):
    """Schema for salary config response."""
    id: int
    user_id: int
    effective_from: date
    effective_to: Optional[date]
    is_current: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Attendance Report Schemas =====

class AttendanceMetrics(BaseModel):
    """Attendance metrics for a period."""
    office_working_days: int = Field(..., description="Working days excluding weekends & holidays")
    days_worked: int = Field(..., description="Days with attendance records")
    days_absent: int = Field(..., description="Days marked as absent")
    total_hours_worked: float = Field(..., description="Total hours worked in period")
    expected_hours: float = Field(..., description="Expected hours based on office days")
    average_hours_per_day: float = Field(..., description="Average hours worked per day")
    overtime_days: int = Field(..., description="Days with overtime (>9 hours)")
    overtime_hours: float = Field(..., description="Total overtime hours")
    undertime_hours: float = Field(..., description="Total undertime hours")


class UserAttendanceReport(BaseModel):
    """Complete attendance report for a user."""
    user_id: int
    user_full_name: str
    user_email: str
    period_start: date
    period_end: date
    metrics: AttendanceMetrics
    
    class Config:
        from_attributes = True


class AdminAttendanceReport(BaseModel):
    """Admin view of all users attendance."""
    period_start: date
    period_end: date
    total_users: int
    reports: List[UserAttendanceReport]


# ===== Salary Record Schemas =====

class SalaryBreakdown(BaseModel):
    """Salary calculation breakdown."""
    base_salary: float
    hourly_rate_used: float
    overtime_hours: float
    overtime_pay: float
    undertime_hours: float
    deductions: float
    absence_days: int
    absence_deductions: float
    net_salary: float


class SalaryRecordResponse(BaseModel):
    """Complete salary record response."""
    id: int
    user_id: int
    user_full_name: str
    user_email: str
    year: int
    month: int
    
    # Attendance summary
    office_working_days: int
    days_worked: int
    days_absent: int
    total_hours_worked: float
    average_hours_per_day: float
    
    # Overtime/Undertime
    overtime_days: int
    overtime_hours: float
    undertime_hours: float
    
    # Salary breakdown
    base_salary: float
    hourly_rate_used: float
    overtime_pay: float
    deductions: float
    absence_deductions: float
    net_salary: float
    
    # Status
    status: SalaryStatusEnum
    remarks: Optional[str]
    created_at: datetime
    approved_at: Optional[datetime]

    class Config:
        from_attributes = True


class PayrollSummary(BaseModel):
    """Monthly payroll summary for admin."""
    year: int
    month: int
    total_employees: int
    total_base_salary: float
    total_overtime_pay: float
    total_deductions: float
    total_net_salary: float
    records: List[SalaryRecordResponse]


class GeneratePayrollRequest(BaseModel):
    """Request to generate payroll for a month."""
    year: int = Field(..., ge=2020, le=2100)
    month: int = Field(..., ge=1, le=12)
    user_id: Optional[int] = Field(None, description="Generate for specific user only")
