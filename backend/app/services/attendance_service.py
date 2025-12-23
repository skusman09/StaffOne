from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.models.checkinout import CheckInOut, ShiftType
from app.models.user import User
from app.schemas.checkinout import CheckInCreate, CheckOutCreate, AdminManualCheckout
from app.core.config import settings
from datetime import datetime, timedelta
from typing import Optional, List
import pytz
import uuid


def get_user_timezone(user: User) -> pytz.timezone:
    """Get the user's timezone object."""
    try:
        return pytz.timezone(user.timezone)
    except Exception:
        return pytz.timezone(settings.DEFAULT_TIMEZONE)


def get_user_today_start_end(user: User) -> tuple[datetime, datetime]:
    """Get today's start and end times in UTC based on user's timezone.
    
    This properly handles timezone boundaries so 'today' is calculated
    correctly for users in different timezones.
    """
    user_tz = get_user_timezone(user)
    
    # Get current time in user's timezone
    utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    user_now = utc_now.astimezone(user_tz)
    
    # Get start and end of today in user's timezone
    today_start_local = user_now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end_local = user_now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Convert back to UTC for database queries
    today_start_utc = today_start_local.astimezone(pytz.UTC).replace(tzinfo=None)
    today_end_utc = today_end_local.astimezone(pytz.UTC).replace(tzinfo=None)
    
    return today_start_utc, today_end_utc


def calculate_hours_worked(check_in_time: datetime, check_out_time: datetime) -> float:
    """Calculate hours worked between check-in and check-out."""
    if not check_in_time or not check_out_time:
        return 0.0
    
    delta = check_out_time - check_in_time
    hours = delta.total_seconds() / 3600
    return round(hours, 2)


def get_today_checkinout(db: Session, user: User) -> Optional[CheckInOut]:
    """Get today's check-in/out record for a user.
    
    Uses user's timezone for proper day boundary calculation.
    """
    today_start_utc, today_end_utc = get_user_today_start_end(user)
    
    return db.query(CheckInOut).filter(
        CheckInOut.user_id == user.id,
        CheckInOut.check_in_time >= today_start_utc,
        CheckInOut.check_in_time <= today_end_utc,
        CheckInOut.shift_type == ShiftType.REGULAR  # Only regular shifts for today check
    ).order_by(CheckInOut.check_in_time.desc()).first()


def get_active_shift(db: Session, user: User) -> Optional[CheckInOut]:
    """Get any active (unclosed) shift for a user.
    
    This allows checking out even if it's past midnight (for night shifts).
    """
    return db.query(CheckInOut).filter(
        CheckInOut.user_id == user.id,
        CheckInOut.check_out_time.is_(None),
        CheckInOut.shift_type == ShiftType.REGULAR
    ).order_by(CheckInOut.check_in_time.desc()).first()


def check_in_user(
    db: Session,
    user: User,
    check_in_data: CheckInCreate
) -> CheckInOut:
    """Create a check-in record for a user."""
    # Check if user has an active (unclosed) shift
    active_shift = get_active_shift(db, user)
    
    if active_shift:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have an active shift. Please check out first."
        )
    
    # Late arrival detection
    is_late = False
    late_mins = 0
    user_tz = get_user_timezone(user)
    utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    user_now = utc_now.astimezone(user_tz)
    
    # Expected start time (configurable, default 9:00 AM) + grace period (default 15 min)
    expected_hour = 9  # Can be made configurable via SystemConfig
    grace_minutes = 15  # Can be made configurable via SystemConfig
    expected_start = user_now.replace(hour=expected_hour, minute=0, second=0, microsecond=0)
    grace_deadline = expected_start + timedelta(minutes=grace_minutes)
    
    if user_now > grace_deadline:
        is_late = True
        late_mins = int((user_now - grace_deadline).total_seconds() / 60)
    
    # Create check-in record
    shift_id = str(uuid.uuid4())
    checkinout = CheckInOut(
        user_id=user.id,
        check_in_time=datetime.utcnow(),
        shift_type=check_in_data.shift_type,
        shift_id=shift_id,
        latitude=check_in_data.latitude,
        longitude=check_in_data.longitude,
        device_info=check_in_data.device_info,
        is_location_valid=True,  # Will be updated by geofencing service if enabled
        is_auto_checkout=False,
        is_late_arrival=is_late,
        late_minutes=late_mins
    )
    
    db.add(checkinout)
    db.commit()
    db.refresh(checkinout)
    return checkinout


def check_out_user(
    db: Session,
    user: User,
    check_out_data: CheckOutCreate
) -> CheckInOut:
    """Update check-out time for a user's active shift."""
    # Get active shift (allows checkout even past midnight)
    active_shift = get_active_shift(db, user)
    
    if not active_shift:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active shift found. Please check in first."
        )
    
    # Update check-out time and calculate hours
    checkout_time = datetime.utcnow()
    active_shift.check_out_time = checkout_time
    active_shift.checkout_latitude = check_out_data.latitude
    active_shift.checkout_longitude = check_out_data.longitude
    
    if check_out_data.device_info:
        active_shift.device_info = check_out_data.device_info
    
    # Calculate hours worked
    active_shift.hours_worked = calculate_hours_worked(
        active_shift.check_in_time, 
        checkout_time
    )
    
    # Early exit detection
    user_tz = get_user_timezone(user)
    utc_now = checkout_time.replace(tzinfo=pytz.UTC)
    user_now = utc_now.astimezone(user_tz)
    
    # Expected end time (configurable, default 6:00 PM)
    expected_end_hour = 18  # Can be made configurable via SystemConfig
    expected_end = user_now.replace(hour=expected_end_hour, minute=0, second=0, microsecond=0)
    
    if user_now < expected_end:
        active_shift.is_early_exit = True
        active_shift.early_exit_minutes = int((expected_end - user_now).total_seconds() / 60)
    
    db.commit()
    db.refresh(active_shift)
    return active_shift


def admin_checkout_user(
    db: Session,
    record_id: int,
    admin_user: User,
    checkout_data: AdminManualCheckout
) -> CheckInOut:
    """Admin manually checks out a user's record."""
    record = db.query(CheckInOut).filter(CheckInOut.id == record_id).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    if record.check_out_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This record already has a checkout time"
        )
    
    # Set checkout time
    checkout_time = checkout_data.checkout_time or datetime.utcnow()
    record.check_out_time = checkout_time
    record.modified_by_admin_id = admin_user.id
    record.admin_notes = checkout_data.admin_notes
    record.is_auto_checkout = False
    
    # Calculate hours worked
    record.hours_worked = calculate_hours_worked(
        record.check_in_time,
        checkout_time
    )
    
    db.commit()
    db.refresh(record)
    return record


def auto_checkout_pending_records(db: Session) -> List[CheckInOut]:
    """Auto-checkout all records that have been open for too long.
    
    Uses the AUTO_CHECKOUT_HOURS setting to determine cutoff.
    Returns list of auto-closed records.
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=settings.AUTO_CHECKOUT_HOURS)
    
    # Find all unclosed records older than cutoff
    pending_records = db.query(CheckInOut).filter(
        CheckInOut.check_out_time.is_(None),
        CheckInOut.check_in_time < cutoff_time
    ).all()
    
    closed_records = []
    for record in pending_records:
        # Auto-checkout at the configured hours after check-in
        auto_checkout_time = record.check_in_time + timedelta(hours=settings.AUTO_CHECKOUT_HOURS)
        record.check_out_time = auto_checkout_time
        record.is_auto_checkout = True
        record.admin_notes = f"Auto-checked out after {settings.AUTO_CHECKOUT_HOURS} hours"
        record.hours_worked = calculate_hours_worked(record.check_in_time, auto_checkout_time)
        closed_records.append(record)
    
    if closed_records:
        db.commit()
        for record in closed_records:
            db.refresh(record)
    
    return closed_records


def get_user_attendance_history(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> list[CheckInOut]:
    """Get attendance history for a user with optional date range filtering."""
    query = db.query(CheckInOut).filter(CheckInOut.user_id == user_id)
    
    if start_date:
        query = query.filter(CheckInOut.check_in_time >= start_date)
    if end_date:
        # Add one day to include the entire end date
        end_datetime = datetime.combine(end_date.date(), datetime.max.time()) if isinstance(end_date, datetime) else end_date
        query = query.filter(CheckInOut.check_in_time <= end_datetime)
    
    return query.order_by(CheckInOut.check_in_time.desc()).offset(skip).limit(limit).all()


def get_all_attendance(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    pending_only: bool = False
) -> list[CheckInOut]:
    """Get all attendance records (admin only)."""
    query = db.query(CheckInOut).options(joinedload(CheckInOut.user))
    
    if user_id:
        query = query.filter(CheckInOut.user_id == user_id)
    
    if pending_only:
        query = query.filter(CheckInOut.check_out_time.is_(None))
    
    return query.order_by(CheckInOut.check_in_time.desc()).offset(skip).limit(limit).all()


def get_working_hours_summary(
    db: Session,
    user_id: int,
    start_date: datetime,
    end_date: datetime
) -> dict:
    """Get working hours summary for a user within a date range."""
    records = db.query(CheckInOut).filter(
        CheckInOut.user_id == user_id,
        CheckInOut.check_in_time >= start_date,
        CheckInOut.check_in_time <= end_date,
        CheckInOut.hours_worked.isnot(None)
    ).all()
    
    total_hours = 0.0
    regular_hours = 0.0
    overtime_hours = 0.0
    break_hours = 0.0
    
    for record in records:
        if record.hours_worked:
            total_hours += record.hours_worked
            if record.shift_type == ShiftType.REGULAR:
                regular_hours += record.hours_worked
            elif record.shift_type == ShiftType.OVERTIME:
                overtime_hours += record.hours_worked
            elif record.shift_type == ShiftType.BREAK:
                break_hours += record.hours_worked
    
    return {
        "total_hours": round(total_hours, 2),
        "regular_hours": round(regular_hours, 2),
        "overtime_hours": round(overtime_hours, 2),
        "break_hours": round(break_hours, 2),
        "records_count": len(records)
    }


def get_monthly_statistics(
    db: Session,
    user_id: int,
    year: int,
    month: int
) -> dict:
    """Get monthly attendance statistics for a user.
    
    Calculates total days, days worked, absences, hours breakdown,
    and attendance percentage for the specified month.
    """
    import calendar
    
    # Get month boundaries
    _, days_in_month = calendar.monthrange(year, month)
    month_start = datetime(year, month, 1, 0, 0, 0)
    month_end = datetime(year, month, days_in_month, 23, 59, 59)
    
    # Calculate working days (excluding weekends)
    working_days = 0
    for day in range(1, days_in_month + 1):
        date_obj = datetime(year, month, day)
        if date_obj.weekday() < 5:  # Monday = 0, Friday = 4
            working_days += 1
    
    # Get all records for the month
    records = db.query(CheckInOut).filter(
        CheckInOut.user_id == user_id,
        CheckInOut.check_in_time >= month_start,
        CheckInOut.check_in_time <= month_end
    ).all()
    
    # Count unique days worked
    days_with_records = set()
    total_hours = 0.0
    regular_hours = 0.0
    overtime_hours = 0.0
    break_hours = 0.0
    
    for record in records:
        days_with_records.add(record.check_in_time.date())
        if record.hours_worked:
            total_hours += record.hours_worked
            if record.shift_type == ShiftType.REGULAR:
                regular_hours += record.hours_worked
            elif record.shift_type == ShiftType.OVERTIME:
                overtime_hours += record.hours_worked
            elif record.shift_type == ShiftType.BREAK:
                break_hours += record.hours_worked
    
    days_worked = len(days_with_records)
    days_absent = max(0, working_days - days_worked)
    avg_hours = total_hours / days_worked if days_worked > 0 else 0
    attendance_pct = (days_worked / working_days * 100) if working_days > 0 else 0
    
    return {
        "year": year,
        "month": month,
        "month_name": calendar.month_name[month],
        "total_days_in_month": days_in_month,
        "working_days_in_month": working_days,
        "days_worked": days_worked,
        "days_absent": days_absent,
        "total_hours": round(total_hours, 2),
        "regular_hours": round(regular_hours, 2),
        "overtime_hours": round(overtime_hours, 2),
        "break_hours": round(break_hours, 2),
        "avg_hours_per_day": round(avg_hours, 2),
        "attendance_percentage": round(attendance_pct, 1)
    }

