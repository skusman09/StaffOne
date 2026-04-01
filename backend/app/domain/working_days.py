"""
Working days calculation domain logic — pure functions for office day computation.

Determines the number of working days in a period, accounting for:
- Weekends (configurable — not all cultures use Sat/Sun)
- Public holidays (passed as date sets)

Pure functions: no database access, no side effects.
"""
from datetime import date, timedelta
from typing import Set, List


def calculate_office_working_days(
    start_date: date,
    end_date: date,
    weekend_days: List[int],
    holiday_dates: Set[date],
) -> int:
    """Calculate the number of office working days in a date range.

    Args:
        start_date: First day of the period (inclusive)
        end_date: Last day of the period (inclusive)
        weekend_days: List of weekday integers that are weekends
                      (0=Monday, 6=Sunday). E.g., [5, 6] for Sat/Sun.
        holiday_dates: Set of dates that are public holidays

    Returns:
        Number of working days (excludes weekends and holidays)
    """
    working_days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() not in weekend_days and current not in holiday_dates:
            working_days += 1
        current += timedelta(days=1)
    return working_days


def get_office_dates(
    start_date: date,
    end_date: date,
    weekend_days: List[int],
    holiday_dates: Set[date],
) -> Set[date]:
    """Get the set of actual office dates (working days) in a range.

    Useful for calculating absences: office_dates - worked_dates = absent_dates.

    Args:
        start_date: First day of the period (inclusive)
        end_date: Last day of the period (inclusive)
        weekend_days: List of weekend day integers
        holiday_dates: Set of holiday dates

    Returns:
        Set of dates that are working days
    """
    office_dates = set()
    current = start_date
    while current <= end_date:
        if current.weekday() not in weekend_days and current not in holiday_dates:
            office_dates.add(current)
        current += timedelta(days=1)
    return office_dates


def calculate_attendance_metrics(
    daily_hours: dict[date, float],
    office_working_days: int,
    office_dates: Set[date],
    standard_hours_per_day: float,
) -> dict:
    """Calculate comprehensive attendance metrics from daily hours data.

    Args:
        daily_hours: Dict mapping date -> total hours worked that day
        office_working_days: Total number of office working days in the period
        office_dates: Set of dates that are working days
        standard_hours_per_day: Expected hours per day (e.g., 9.0)

    Returns:
        Dict with: days_worked, days_absent, total_hours_worked,
        expected_hours, average_hours_per_day, overtime_days,
        overtime_hours, undertime_hours
    """
    worked_dates = set(daily_hours.keys())
    days_worked = len(worked_dates)
    days_absent = len(office_dates - worked_dates)

    total_hours_worked = sum(daily_hours.values())
    expected_hours = office_working_days * standard_hours_per_day
    average_hours = total_hours_worked / days_worked if days_worked > 0 else 0.0

    overtime_days = 0
    overtime_hours = 0.0
    undertime_hours = 0.0

    for _, hours in daily_hours.items():
        if hours > standard_hours_per_day:
            overtime_days += 1
            overtime_hours += hours - standard_hours_per_day
        elif hours < standard_hours_per_day:
            undertime_hours += standard_hours_per_day - hours

    return {
        "office_working_days": office_working_days,
        "days_worked": days_worked,
        "days_absent": days_absent,
        "total_hours_worked": round(total_hours_worked, 2),
        "expected_hours": round(expected_hours, 2),
        "average_hours_per_day": round(average_hours, 2),
        "overtime_days": overtime_days,
        "overtime_hours": round(overtime_hours, 2),
        "undertime_hours": round(undertime_hours, 2),
    }
