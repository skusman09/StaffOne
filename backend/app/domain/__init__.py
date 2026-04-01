"""
Domain layer — pure business logic, no database, no HTTP.

This layer contains stateless functions that encode the core business rules
of the StaffOne HRMS. They receive plain data (numbers, dates, dataclasses)
and return computed results.

Benefits:
- Unit-testable in <1ms (no DB setup needed)
- Reusable across services (salary rules used by payroll and reports)
- Clearly documents business rules (what constitutes "late arrival"?)

Modules:
- salary_calculator: Net salary computation from attendance metrics
- attendance_rules: Late arrival, early exit, auto-checkout policies
- working_days: Office working day calculation (weekends, holidays)
- leave_policy: Leave overlap validation, balance computation
"""
