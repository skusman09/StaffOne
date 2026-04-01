"""
Permission definitions and role-permission mapping.

This module defines what actions exist in the system and which roles
are allowed to perform them. Adding a new role or permission is a
single-location change.

Design:
- Permissions are fine-grained actions (e.g., "view_any_salary")
- Roles map to sets of permissions
- This is NOT an RBAC database — it's a code-level policy table
  that is fast, explicit, and auditable via version control

When to extend:
- New feature → add new Permission entries
- New role → add a new mapping in ROLE_PERMISSIONS
"""
import enum
from typing import Set

from app.models.user import Role


class Permission(str, enum.Enum):
    """Fine-grained permissions in the system.

    Naming convention: {action}_{scope}
    - action: view, create, update, delete, manage, approve
    - scope: own (self), any (all users)
    """

    # ── User Management ────────────────────────────────────────
    VIEW_ANY_USER = "view_any_user"
    UPDATE_ANY_USER = "update_any_user"
    UPDATE_USER_ROLE = "update_user_role"

    # ── Attendance ─────────────────────────────────────────────
    VIEW_OWN_ATTENDANCE = "view_own_attendance"
    VIEW_ANY_ATTENDANCE = "view_any_attendance"
    MANAGE_ATTENDANCE = "manage_attendance"  # admin checkout, notes

    # ── Leaves ─────────────────────────────────────────────────
    CREATE_OWN_LEAVE = "create_own_leave"
    VIEW_OWN_LEAVES = "view_own_leaves"
    VIEW_ANY_LEAVES = "view_any_leaves"
    APPROVE_LEAVE = "approve_leave"
    REJECT_LEAVE = "reject_leave"

    # ── Payroll / Salary ───────────────────────────────────────
    VIEW_OWN_SALARY = "view_own_salary"
    VIEW_ANY_SALARY = "view_any_salary"
    MANAGE_SALARY_CONFIG = "manage_salary_config"
    GENERATE_PAYROLL = "generate_payroll"
    APPROVE_SALARY = "approve_salary"
    EXPORT_PAYROLL = "export_payroll"

    # ── Holidays ───────────────────────────────────────────────
    VIEW_HOLIDAYS = "view_holidays"
    MANAGE_HOLIDAYS = "manage_holidays"

    # ── Locations ──────────────────────────────────────────────
    VIEW_LOCATIONS = "view_locations"
    MANAGE_LOCATIONS = "manage_locations"

    # ── Notifications ──────────────────────────────────────────
    VIEW_OWN_NOTIFICATIONS = "view_own_notifications"
    MANAGE_ANY_NOTIFICATIONS = "manage_any_notifications"

    # ── Analytics / Reports ────────────────────────────────────
    VIEW_ANALYTICS = "view_analytics"
    VIEW_REPORTS = "view_reports"
    EXPORT_REPORTS = "export_reports"

    # ── System Config ──────────────────────────────────────────
    VIEW_SYSTEM_CONFIG = "view_system_config"
    MANAGE_SYSTEM_CONFIG = "manage_system_config"

    # ── Audit ──────────────────────────────────────────────────
    VIEW_AUDIT_LOGS = "view_audit_logs"

    # ── Departments ────────────────────────────────────────────
    MANAGE_DEPARTMENTS = "manage_departments"

    # ── Onboarding ─────────────────────────────────────────────
    VIEW_OWN_ONBOARDING = "view_own_onboarding"
    MANAGE_ONBOARDING = "manage_onboarding"

    # ── Pulse Surveys ──────────────────────────────────────────
    RESPOND_PULSE = "respond_pulse"
    MANAGE_PULSE = "manage_pulse"

    # ── Comp Off ───────────────────────────────────────────────
    CREATE_OWN_COMPOFF = "create_own_compoff"
    VIEW_OWN_COMPOFF = "view_own_compoff"
    MANAGE_COMPOFF = "manage_compoff"

    # ── Scheduler ──────────────────────────────────────────────
    MANAGE_SCHEDULER = "manage_scheduler"


# ── Role → Permission Mapping ──────────────────────────────────────

# Employee permissions: self-service operations
_EMPLOYEE_PERMISSIONS: Set[Permission] = {
    Permission.VIEW_OWN_ATTENDANCE,
    Permission.CREATE_OWN_LEAVE,
    Permission.VIEW_OWN_LEAVES,
    Permission.VIEW_OWN_SALARY,
    Permission.VIEW_HOLIDAYS,
    Permission.VIEW_LOCATIONS,
    Permission.VIEW_OWN_NOTIFICATIONS,
    Permission.VIEW_OWN_ONBOARDING,
    Permission.RESPOND_PULSE,
    Permission.CREATE_OWN_COMPOFF,
    Permission.VIEW_OWN_COMPOFF,
}

# Admin permissions: everything an employee can do + management
_ADMIN_PERMISSIONS: Set[Permission] = _EMPLOYEE_PERMISSIONS | {
    Permission.VIEW_ANY_USER,
    Permission.UPDATE_ANY_USER,
    Permission.UPDATE_USER_ROLE,
    Permission.VIEW_ANY_ATTENDANCE,
    Permission.MANAGE_ATTENDANCE,
    Permission.VIEW_ANY_LEAVES,
    Permission.APPROVE_LEAVE,
    Permission.REJECT_LEAVE,
    Permission.VIEW_ANY_SALARY,
    Permission.MANAGE_SALARY_CONFIG,
    Permission.GENERATE_PAYROLL,
    Permission.APPROVE_SALARY,
    Permission.EXPORT_PAYROLL,
    Permission.MANAGE_HOLIDAYS,
    Permission.MANAGE_LOCATIONS,
    Permission.MANAGE_ANY_NOTIFICATIONS,
    Permission.VIEW_ANALYTICS,
    Permission.VIEW_REPORTS,
    Permission.EXPORT_REPORTS,
    Permission.VIEW_SYSTEM_CONFIG,
    Permission.MANAGE_SYSTEM_CONFIG,
    Permission.VIEW_AUDIT_LOGS,
    Permission.MANAGE_DEPARTMENTS,
    Permission.MANAGE_ONBOARDING,
    Permission.MANAGE_PULSE,
    Permission.MANAGE_COMPOFF,
    Permission.MANAGE_SCHEDULER,
}

# Master mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.EMPLOYEE: _EMPLOYEE_PERMISSIONS,
    Role.ADMIN: _ADMIN_PERMISSIONS,
}


def has_permission(role: Role, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())


def get_permissions(role: Role) -> Set[Permission]:
    """Get all permissions for a role."""
    return ROLE_PERMISSIONS.get(role, set()).copy()
