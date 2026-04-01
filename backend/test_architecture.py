"""Quick validation that all new architectural modules import and work correctly."""
import sys
sys.path.insert(0, '.')

# ── 1. Domain Layer ────────────────────────────────────────────────
print("Testing domain layer...")

from app.domain.salary_calculator import compute_net_salary, SalaryInputs
inputs = SalaryInputs(
    base_salary=50000, office_working_days=22, standard_hours_per_day=9.0,
    overtime_multiplier=1.5, deduction_rate=1.0,
    days_worked=20, days_absent=2, total_hours_worked=178,
    overtime_hours=4.0, undertime_hours=2.0,
)
result = compute_net_salary(inputs)
assert result.net_salary > 0, "Net salary should be positive"
assert result.overtime_pay > 0, "Overtime pay should be positive"
print(f"  salary_calculator: OK (net={result.net_salary})")

from app.domain.working_days import calculate_office_working_days, get_office_dates
from datetime import date
days = calculate_office_working_days(date(2024, 1, 1), date(2024, 1, 31), [5, 6], set())
assert days == 23, f"Expected 23 working days, got {days}"
print(f"  working_days: OK ({days} working days in Jan 2024)")

from app.domain.leave_policy import validate_cancellation, validate_status_transition
cancel = validate_cancellation("pending", date(2099, 12, 31), 1, 1)
assert cancel.can_cancel, "Should be able to cancel own pending future leave"
cancel2 = validate_cancellation("pending", date(2099, 12, 31), 1, 2)
assert not cancel2.can_cancel, "Should NOT cancel someone else's leave"
assert validate_status_transition("pending", "approved")
assert not validate_status_transition("rejected", "approved")
print("  leave_policy: OK")

from app.domain.attendance_rules import calculate_hours_worked, check_auto_checkout_eligibility
from datetime import datetime
hours = calculate_hours_worked(datetime(2024, 1, 1, 9, 0), datetime(2024, 1, 1, 17, 30))
assert abs(hours - 8.5) < 0.01, f"Expected 8.5 hours, got {hours}"
print(f"  attendance_rules: OK (hours={hours})")

# ── 2. Transaction Decorator ──────────────────────────────────────
print("Testing transaction module...")
from app.core.transaction import transactional, TransactionContext
print("  transaction: OK (imported)")

# ── 3. Interfaces ─────────────────────────────────────────────────
print("Testing interfaces...")
from app.interfaces.repositories import (
    IUserRepository, IAttendanceRepository, ILeaveRepository,
    ISalaryRepository, IHolidayRepository, INotificationRepository,
    IAuditRepository
)
print(f"  repositories: OK (7 protocols defined)")

# ── 4. Authorization ──────────────────────────────────────────────
print("Testing authorization...")
from app.authorization.permissions import Permission, has_permission, get_permissions
from app.models.user import Role

assert has_permission(Role.ADMIN, Permission.GENERATE_PAYROLL)
assert not has_permission(Role.EMPLOYEE, Permission.GENERATE_PAYROLL)
assert has_permission(Role.EMPLOYEE, Permission.VIEW_OWN_ATTENDANCE)

admin_perms = get_permissions(Role.ADMIN)
employee_perms = get_permissions(Role.EMPLOYEE)
assert len(admin_perms) > len(employee_perms), "Admin should have more permissions"
print(f"  permissions: OK (admin={len(admin_perms)}, employee={len(employee_perms)})")

from app.authorization.policies import can_modify_user_role
assert not can_modify_user_role(
    type('User', (), {'id': 1, 'role': Role.ADMIN})(),
    target_user_id=1, new_role=Role.EMPLOYEE
), "Admin should not be able to demote themselves"
print("  policies: OK")

# ── 5. Container ──────────────────────────────────────────────────
print("Testing container...")
from app.container import (
    get_auth_service, get_attendance_service, get_leave_service,
    get_payroll_service, get_notification_service, get_holiday_service,
    get_audit_service
)
print("  container: OK (7 service factories)")

print("\n✅ ALL ARCHITECTURAL MODULES VERIFIED SUCCESSFULLY")
