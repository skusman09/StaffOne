"""
Attendance rules domain logic — pure functions for attendance policy enforcement.

Encodes the business rules for:
- Late arrival detection (configurable grace period)
- Early exit detection (configurable expected end time)
- Auto-checkout eligibility
- Working hours calculation

All functions are stateless. They take timestamps and config values,
and return computed results. No database access, no HTTP.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import pytz


@dataclass(frozen=True)
class LateArrivalResult:
    """Result of late arrival check."""
    is_late: bool
    minutes_late: int


@dataclass(frozen=True)
class EarlyExitResult:
    """Result of early exit check."""
    is_early: bool
    minutes_early: int


@dataclass(frozen=True)
class AutoCheckoutResult:
    """Result of auto-checkout eligibility check."""
    should_auto_checkout: bool
    checkout_time: Optional[datetime]
    hours_worked: float


def get_user_timezone(timezone_str: str, default_timezone: str) -> pytz.timezone:
    """Get a pytz timezone object, falling back to default if invalid.

    Args:
        timezone_str: User's configured timezone (e.g., 'Asia/Kolkata')
        default_timezone: Fallback timezone from settings
    """
    try:
        return pytz.timezone(timezone_str)
    except Exception:
        return pytz.timezone(default_timezone)


def get_today_boundaries(user_tz: pytz.timezone) -> tuple[datetime, datetime]:
    """Get today's start and end times in UTC based on user's timezone.

    Returns (today_start_utc, today_end_utc) as naive datetime objects.
    """
    utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    user_now = utc_now.astimezone(user_tz)

    today_start_local = user_now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end_local = user_now.replace(hour=23, minute=59, second=59, microsecond=999999)

    today_start_utc = today_start_local.astimezone(pytz.UTC).replace(tzinfo=None)
    today_end_utc = today_end_local.astimezone(pytz.UTC).replace(tzinfo=None)

    return today_start_utc, today_end_utc


def check_late_arrival(
    user_tz: pytz.timezone,
    expected_start_hour: int = 9,
    grace_minutes: int = 15,
) -> LateArrivalResult:
    """Check if the current time constitutes a late arrival.

    Args:
        user_tz: User's timezone
        expected_start_hour: Expected work start hour (24h format)
        grace_minutes: Grace period in minutes after expected start

    Returns:
        LateArrivalResult with is_late flag and minutes late (after grace period)
    """
    utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    user_now = utc_now.astimezone(user_tz)

    expected_start = user_now.replace(
        hour=expected_start_hour, minute=0, second=0, microsecond=0
    )
    grace_deadline = expected_start + timedelta(minutes=grace_minutes)

    if user_now > grace_deadline:
        late_mins = int((user_now - grace_deadline).total_seconds() / 60)
        return LateArrivalResult(is_late=True, minutes_late=late_mins)

    return LateArrivalResult(is_late=False, minutes_late=0)


def check_early_exit(
    checkout_time_utc: datetime,
    user_tz: pytz.timezone,
    expected_end_hour: int = 18,
) -> EarlyExitResult:
    """Check if checkout time constitutes an early exit.

    Args:
        checkout_time_utc: The checkout time in UTC
        user_tz: User's timezone
        expected_end_hour: Expected work end hour (24h format)

    Returns:
        EarlyExitResult with is_early flag and minutes early
    """
    utc_checkout = checkout_time_utc.replace(tzinfo=pytz.UTC)
    user_checkout = utc_checkout.astimezone(user_tz)

    expected_end = user_checkout.replace(
        hour=expected_end_hour, minute=0, second=0, microsecond=0
    )

    if user_checkout < expected_end:
        early_mins = int((expected_end - user_checkout).total_seconds() / 60)
        return EarlyExitResult(is_early=True, minutes_early=early_mins)

    return EarlyExitResult(is_early=False, minutes_early=0)


def calculate_hours_worked(
    check_in_time: Optional[datetime],
    check_out_time: Optional[datetime],
) -> float:
    """Calculate hours worked between check-in and check-out.

    Returns 0.0 if either time is None.
    """
    if not check_in_time or not check_out_time:
        return 0.0
    delta = check_out_time - check_in_time
    return round(delta.total_seconds() / 3600, 2)


def check_auto_checkout_eligibility(
    check_in_time: datetime,
    auto_checkout_hours: float,
) -> AutoCheckoutResult:
    """Determine if a record should be auto-checked-out.

    Args:
        check_in_time: When the user checked in
        auto_checkout_hours: Maximum allowed open shift duration

    Returns:
        AutoCheckoutResult with computed checkout time and hours worked
    """
    auto_checkout_time = check_in_time + timedelta(hours=auto_checkout_hours)
    hours = calculate_hours_worked(check_in_time, auto_checkout_time)

    cutoff = datetime.utcnow() - timedelta(hours=auto_checkout_hours)
    should_checkout = check_in_time < cutoff

    return AutoCheckoutResult(
        should_auto_checkout=should_checkout,
        checkout_time=auto_checkout_time if should_checkout else None,
        hours_worked=hours,
    )


def accumulate_hours_by_shift(records_data: list[dict]) -> dict:
    """Accumulate hours by shift type from a list of record dicts.

    Args:
        records_data: List of dicts with keys: hours_worked, shift_type

    Returns:
        Dict with total_hours, regular_hours, overtime_hours, break_hours
    """
    total_hours = 0.0
    regular_hours = 0.0
    overtime_hours = 0.0
    break_hours = 0.0

    for record in records_data:
        hours = record.get("hours_worked") or 0.0
        shift_type = record.get("shift_type", "regular")

        total_hours += hours
        if shift_type == "regular":
            regular_hours += hours
        elif shift_type == "overtime":
            overtime_hours += hours
        elif shift_type == "break":
            break_hours += hours

    return {
        "total_hours": round(total_hours, 2),
        "regular_hours": round(regular_hours, 2),
        "overtime_hours": round(overtime_hours, 2),
        "break_hours": round(break_hours, 2),
    }
