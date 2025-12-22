from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List, Dict
from datetime import date, datetime, timedelta
from collections import defaultdict
import calendar

from app.models.user import User
from app.models.checkinout import CheckInOut
from app.models.holiday import Holiday
from app.models.salary import SalaryConfig, SalaryRecord, SalaryStatus
from app.services.holiday_service import get_holidays_in_range, count_holidays_in_range
from app.core.config import settings
from app.schemas.salary import (
    AttendanceMetrics, UserAttendanceReport, SalaryRecordResponse
)


def get_office_working_days(
    db: Session,
    start_date: date,
    end_date: date,
    weekend_days: List[int] = None
) -> int:
    """Calculate office working days excluding weekends and holidays.
    
    Args:
        db: Database session
        start_date: Start of period
        end_date: End of period
        weekend_days: List of weekday numbers (0=Monday, 6=Sunday). Default from config.
    
    Returns:
        Number of working days
    """
    if weekend_days is None:
        weekend_days = settings.weekend_days_list
    
    # Count total days excluding weekends
    working_days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() not in weekend_days:
            working_days += 1
        current += timedelta(days=1)
    
    # Subtract holidays
    holidays_count = count_holidays_in_range(db, start_date, end_date)
    
    # Only subtract holidays that fall on working days
    holidays = get_holidays_in_range(db, start_date, end_date)
    holiday_working_days = sum(1 for h in holidays if h.holiday_date.weekday() not in weekend_days)
    
    return working_days - holiday_working_days


def get_daily_hours(records: List[CheckInOut]) -> Dict[date, float]:
    """Group attendance records by date and sum hours.
    
    Returns dict of date -> total hours worked that day.
    """
    daily_hours = defaultdict(float)
    
    for record in records:
        if record.hours_worked is not None:
            record_date = record.check_in_time.date()
            daily_hours[record_date] += record.hours_worked
    
    return dict(daily_hours)


def calculate_attendance_metrics(
    db: Session,
    user_id: int,
    start_date: date,
    end_date: date,
    standard_hours: float = None
) -> AttendanceMetrics:
    """Calculate comprehensive attendance metrics for a user.
    
    Args:
        db: Database session
        user_id: User ID
        start_date: Report start date
        end_date: Report end date
        standard_hours: Standard working hours per day (default from config)
    
    Returns:
        AttendanceMetrics with all calculated values
    """
    if standard_hours is None:
        standard_hours = settings.OFFICE_STANDARD_HOURS
    
    # Get office working days
    office_working_days = get_office_working_days(db, start_date, end_date)
    expected_hours = office_working_days * standard_hours
    
    # Get attendance records
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    records = db.query(CheckInOut).filter(
        CheckInOut.user_id == user_id,
        CheckInOut.check_in_time >= start_datetime,
        CheckInOut.check_in_time <= end_datetime,
        CheckInOut.check_out_time.isnot(None)  # Only completed records
    ).all()
    
    # Calculate daily hours
    daily_hours = get_daily_hours(records)
    
    # Get set of worked dates
    worked_dates = set(daily_hours.keys())
    
    # Calculate days worked (unique dates with records)
    days_worked = len(worked_dates)
    
    # Calculate days absent (office days without any record)
    # Build set of office working days
    weekend_days = settings.weekend_days_list
    holidays = get_holidays_in_range(db, start_date, end_date)
    holiday_dates = {h.holiday_date for h in holidays}
    
    office_dates = set()
    current = start_date
    while current <= end_date:
        if current.weekday() not in weekend_days and current not in holiday_dates:
            office_dates.add(current)
        current += timedelta(days=1)
    
    days_absent = len(office_dates - worked_dates)
    
    # Calculate total hours
    total_hours_worked = sum(daily_hours.values())
    
    # Calculate average hours per day (only for days worked)
    average_hours_per_day = total_hours_worked / days_worked if days_worked > 0 else 0.0
    
    # Calculate overtime and undertime
    overtime_days = 0
    overtime_hours = 0.0
    undertime_hours = 0.0
    
    for day_date, hours in daily_hours.items():
        if hours > standard_hours:
            overtime_days += 1
            overtime_hours += hours - standard_hours
        elif hours < standard_hours:
            undertime_hours += standard_hours - hours
    
    return AttendanceMetrics(
        office_working_days=office_working_days,
        days_worked=days_worked,
        days_absent=days_absent,
        total_hours_worked=round(total_hours_worked, 2),
        expected_hours=round(expected_hours, 2),
        average_hours_per_day=round(average_hours_per_day, 2),
        overtime_days=overtime_days,
        overtime_hours=round(overtime_hours, 2),
        undertime_hours=round(undertime_hours, 2)
    )


def get_user_attendance_report(
    db: Session,
    user_id: int,
    start_date: date,
    end_date: date
) -> UserAttendanceReport:
    """Generate attendance report for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    metrics = calculate_attendance_metrics(db, user_id, start_date, end_date)
    
    return UserAttendanceReport(
        user_id=user.id,
        user_full_name=user.full_name or user.username,
        user_email=user.email,
        period_start=start_date,
        period_end=end_date,
        metrics=metrics
    )


def get_user_salary_config(db: Session, user_id: int) -> Optional[SalaryConfig]:
    """Get current salary configuration for a user."""
    return db.query(SalaryConfig).filter(
        SalaryConfig.user_id == user_id,
        SalaryConfig.is_current == True
    ).first()


def calculate_salary(
    db: Session,
    user_id: int,
    year: int,
    month: int
) -> SalaryRecord:
    """Calculate salary for a user for a specific month.
    
    Uses attendance data to calculate overtime, deductions, and net salary.
    """
    # Get month date range
    _, last_day = calendar.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    # Get salary config (or use user's base salary)
    salary_config = get_user_salary_config(db, user_id)
    
    if salary_config:
        base_salary = salary_config.monthly_base_salary
        overtime_multiplier = salary_config.overtime_multiplier
        deduction_rate = salary_config.deduction_rate_per_hour
    else:
        # Fallback to user's base salary or default
        base_salary = user.monthly_base_salary or 0.0
        overtime_multiplier = settings.OVERTIME_MULTIPLIER
        deduction_rate = settings.DEDUCTION_RATE
    
    # Calculate attendance metrics
    metrics = calculate_attendance_metrics(db, user_id, start_date, end_date)
    
    # Calculate hourly rate
    standard_hours = settings.OFFICE_STANDARD_HOURS
    hourly_rate = base_salary / (metrics.office_working_days * standard_hours) if metrics.office_working_days > 0 else 0
    
    # Calculate overtime pay
    overtime_pay = metrics.overtime_hours * hourly_rate * overtime_multiplier
    
    # Calculate undertime deductions  
    deductions = metrics.undertime_hours * hourly_rate * deduction_rate
    
    # Calculate absence deductions (full day rate per absent day)
    daily_rate = base_salary / metrics.office_working_days if metrics.office_working_days > 0 else 0
    absence_deductions = metrics.days_absent * daily_rate
    
    # Calculate net salary
    net_salary = base_salary + overtime_pay - deductions - absence_deductions
    
    # Create or update salary record
    existing = db.query(SalaryRecord).filter(
        SalaryRecord.user_id == user_id,
        SalaryRecord.year == year,
        SalaryRecord.month == month
    ).first()
    
    if existing:
        record = existing
    else:
        record = SalaryRecord(user_id=user_id, year=year, month=month)
        db.add(record)
    
    # Update record with calculated values
    record.office_working_days = metrics.office_working_days
    record.days_worked = metrics.days_worked
    record.days_absent = metrics.days_absent
    record.total_hours_worked = metrics.total_hours_worked
    record.expected_hours = metrics.expected_hours
    record.average_hours_per_day = metrics.average_hours_per_day
    record.overtime_days = metrics.overtime_days
    record.overtime_hours = metrics.overtime_hours
    record.undertime_hours = metrics.undertime_hours
    record.base_salary = round(base_salary, 2)
    record.hourly_rate_used = round(hourly_rate, 2)
    record.overtime_pay = round(overtime_pay, 2)
    record.deductions = round(deductions, 2)
    record.absence_deductions = round(absence_deductions, 2)
    record.net_salary = round(net_salary, 2)
    record.status = SalaryStatus.DRAFT
    
    db.commit()
    db.refresh(record)
    
    return record


def generate_monthly_payroll(
    db: Session,
    year: int,
    month: int,
    user_id: Optional[int] = None
) -> List[SalaryRecord]:
    """Generate salary records for all (or specific) users for a month.
    
    Args:
        db: Database session
        year: Payroll year
        month: Payroll month (1-12)
        user_id: Optional specific user ID
    
    Returns:
        List of generated SalaryRecord objects
    """
    if user_id:
        users = [db.query(User).filter(User.id == user_id, User.is_active == True).first()]
        users = [u for u in users if u is not None]
    else:
        users = db.query(User).filter(User.is_active == True).all()
    
    records = []
    for user in users:
        try:
            record = calculate_salary(db, user.id, year, month)
            records.append(record)
        except Exception as e:
            print(f"Error calculating salary for user {user.id}: {e}")
    
    return records


def get_salary_record(
    db: Session,
    user_id: int,
    year: int,
    month: int
) -> Optional[SalaryRecord]:
    """Get salary record for a user for a specific month."""
    return db.query(SalaryRecord).filter(
        SalaryRecord.user_id == user_id,
        SalaryRecord.year == year,
        SalaryRecord.month == month
    ).first()


def get_monthly_payroll(
    db: Session,
    year: int,
    month: int
) -> List[SalaryRecord]:
    """Get all salary records for a month."""
    return db.query(SalaryRecord).filter(
        SalaryRecord.year == year,
        SalaryRecord.month == month
    ).order_by(SalaryRecord.user_id).all()
