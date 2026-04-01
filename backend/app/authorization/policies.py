"""
Authorization policies — higher-level access control checks.

Policies combine permissions with business context (e.g., "can this user
view this specific salary record?") to make authorization decisions.

Unlike raw permission checks, policies can consider:
- Resource ownership (is this the user's own record?)
- Department membership (is target in same department?)
- Business rules (can't demote yourself)
"""
import logging
from typing import Optional

from app.models.user import User, Role
from app.authorization.permissions import Permission, has_permission

logger = logging.getLogger(__name__)


class PolicyViolation(Exception):
    """Raised when an authorization policy is violated."""

    def __init__(self, message: str, status_code: int = 403):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def require_permission(user: User, permission: Permission) -> None:
    """Enforce that a user has a specific permission.

    Raises PolicyViolation if the user lacks the permission.
    """
    if not has_permission(user.role, permission):
        logger.warning(
            f"Authorization denied: user={user.id} role={user.role.value} "
            f"permission={permission.value}"
        )
        raise PolicyViolation(
            f"Insufficient permissions: requires {permission.value}"
        )


def can_view_user_salary(actor: User, target_user_id: int) -> bool:
    """Check if actor can view a specific user's salary.

    Rules:
    - Users can always view their own salary
    - Admins can view any user's salary
    """
    if actor.id == target_user_id:
        return has_permission(actor.role, Permission.VIEW_OWN_SALARY)
    return has_permission(actor.role, Permission.VIEW_ANY_SALARY)


def can_view_user_attendance(actor: User, target_user_id: int) -> bool:
    """Check if actor can view a specific user's attendance.

    Rules:
    - Users can always view their own attendance
    - Admins can view any user's attendance
    """
    if actor.id == target_user_id:
        return has_permission(actor.role, Permission.VIEW_OWN_ATTENDANCE)
    return has_permission(actor.role, Permission.VIEW_ANY_ATTENDANCE)


def can_modify_user_role(actor: User, target_user_id: int, new_role: Role) -> bool:
    """Check if actor can modify a user's role.

    Rules:
    - Must have UPDATE_USER_ROLE permission
    - Cannot demote yourself from admin (safety guard)
    """
    if not has_permission(actor.role, Permission.UPDATE_USER_ROLE):
        return False

    # Self-demotion guard
    if actor.id == target_user_id and new_role != Role.ADMIN:
        return False

    return True


def can_manage_leave(actor: User, leave_user_id: int, action: str) -> bool:
    """Check if actor can perform a leave management action.

    Args:
        actor: The user performing the action
        leave_user_id: The user whose leave is being managed
        action: 'approve', 'reject', or 'cancel'

    Rules:
    - Approve/reject: requires APPROVE_LEAVE/REJECT_LEAVE permission
    - Cancel: user can cancel their own, admin can cancel any
    """
    if action == "approve":
        return has_permission(actor.role, Permission.APPROVE_LEAVE)
    elif action == "reject":
        return has_permission(actor.role, Permission.REJECT_LEAVE)
    elif action == "cancel":
        if actor.id == leave_user_id:
            return True  # Users can cancel their own
        return has_permission(actor.role, Permission.VIEW_ANY_LEAVES)
    return False
