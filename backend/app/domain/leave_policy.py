"""
Leave policy domain logic — pure functions for leave business rules.

Encodes:
- Leave overlap detection rules
- Leave cancellation eligibility
- Leave balance computation
- Status transition validation

No database access, no HTTP. Pure business rules.
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional, List


@dataclass(frozen=True)
class LeaveOverlapCheck:
    """Result of leave overlap check."""
    has_overlap: bool
    conflicting_start: Optional[date] = None
    conflicting_end: Optional[date] = None


@dataclass(frozen=True)
class LeaveCancelCheck:
    """Result of leave cancellation eligibility check."""
    can_cancel: bool
    reason: Optional[str] = None


def check_date_overlap(
    new_start: date,
    new_end: date,
    existing_start: date,
    existing_end: date,
) -> bool:
    """Check if two date ranges overlap.

    Two ranges [A_start, A_end] and [B_start, B_end] overlap if:
    A_start <= B_end AND A_end >= B_start
    """
    return new_start <= existing_end and new_end >= existing_start


def validate_cancellation(
    leave_status: str,
    leave_start_date: date,
    leave_user_id: int,
    requesting_user_id: int,
) -> LeaveCancelCheck:
    """Validate whether a leave request can be cancelled.

    Business rules:
    1. Only the requesting user can cancel their own leave
    2. Only PENDING or APPROVED leaves can be cancelled
    3. Cannot cancel leave that has already started
    """
    if leave_user_id != requesting_user_id:
        return LeaveCancelCheck(
            can_cancel=False,
            reason="You can only cancel your own leave requests",
        )

    cancellable_statuses = {"pending", "approved"}
    if leave_status not in cancellable_statuses:
        return LeaveCancelCheck(
            can_cancel=False,
            reason=f"Cannot cancel leave with status {leave_status}",
        )

    if leave_start_date <= date.today():
        return LeaveCancelCheck(
            can_cancel=False,
            reason="Cannot cancel leave that has already started",
        )

    return LeaveCancelCheck(can_cancel=True)


def validate_status_transition(
    current_status: str,
    new_status: str,
) -> bool:
    """Validate whether a leave status transition is allowed.

    Valid transitions:
    - pending → approved
    - pending → rejected
    - pending → cancelled
    - approved → cancelled
    """
    valid_transitions = {
        "pending": {"approved", "rejected", "cancelled"},
        "approved": {"cancelled"},
    }

    allowed = valid_transitions.get(current_status, set())
    return new_status in allowed


def calculate_leave_days(start_date: date, end_date: date) -> int:
    """Calculate number of leave days (inclusive of both start and end)."""
    if start_date > end_date:
        return 0
    return (end_date - start_date).days + 1


def compute_leave_balance(
    approved_leaves: List[dict],
    annual_quota: int = 0,
) -> dict:
    """Compute leave balance summary.

    Args:
        approved_leaves: List of dicts with keys: leave_type, start_date, end_date
        annual_quota: Total annual leave entitlement (0 if not configured)

    Returns:
        Dict with total_taken, total_days, remaining (if quota configured)
    """
    total_days = 0
    by_type = {}

    for leave in approved_leaves:
        days = calculate_leave_days(leave["start_date"], leave["end_date"])
        total_days += days
        leave_type = leave.get("leave_type", "other")
        by_type[leave_type] = by_type.get(leave_type, 0) + days

    result = {
        "total_leaves_taken": len(approved_leaves),
        "total_days_taken": total_days,
        "by_type": by_type,
    }

    if annual_quota > 0:
        result["annual_quota"] = annual_quota
        result["remaining"] = max(0, annual_quota - total_days)

    return result
