"""
Salary calculation domain logic — pure functions, no database, no HTTP.

Encodes the core salary computation rules:
- Hourly rate derivation from monthly salary
- Overtime pay calculation with configurable multiplier
- Undertime deduction calculation
- Absence-based deduction calculation
- Net salary computation

All functions are stateless and take plain data as input.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SalaryInputs:
    """Immutable input data for salary calculation."""
    base_salary: float
    office_working_days: int
    standard_hours_per_day: float
    overtime_multiplier: float
    deduction_rate: float

    # Attendance metrics
    days_worked: int
    days_absent: int
    total_hours_worked: float
    overtime_hours: float
    undertime_hours: float


@dataclass(frozen=True)
class SalaryBreakdown:
    """Immutable output of salary calculation."""
    base_salary: float
    hourly_rate: float
    overtime_pay: float
    undertime_deductions: float
    absence_deductions: float
    net_salary: float

    @property
    def total_deductions(self) -> float:
        return round(self.undertime_deductions + self.absence_deductions, 2)


def calculate_hourly_rate(
    base_salary: float,
    office_working_days: int,
    standard_hours_per_day: float,
) -> float:
    """Derive hourly rate from monthly salary.

    Formula: monthly_salary / (working_days × standard_hours)

    Returns 0.0 if working_days is 0 (safeguard for edge case months).
    """
    total_expected_hours = office_working_days * standard_hours_per_day
    if total_expected_hours <= 0:
        return 0.0
    return base_salary / total_expected_hours


def calculate_overtime_pay(
    overtime_hours: float,
    hourly_rate: float,
    overtime_multiplier: float,
) -> float:
    """Calculate overtime pay.

    Formula: overtime_hours × hourly_rate × multiplier
    Common multiplier: 1.5x (time-and-a-half)
    """
    return round(overtime_hours * hourly_rate * overtime_multiplier, 2)


def calculate_undertime_deductions(
    undertime_hours: float,
    hourly_rate: float,
    deduction_rate: float,
) -> float:
    """Calculate deductions for undertime (worked less than standard hours).

    Formula: undertime_hours × hourly_rate × deduction_rate
    Deduction rate of 1.0 means 1:1 with hourly rate.
    """
    return round(undertime_hours * hourly_rate * deduction_rate, 2)


def calculate_absence_deductions(
    days_absent: int,
    base_salary: float,
    office_working_days: int,
) -> float:
    """Calculate deductions for full-day absences.

    Formula: absent_days × (monthly_salary / working_days)
    This is a per-diem deduction.
    """
    if office_working_days <= 0:
        return 0.0
    daily_rate = base_salary / office_working_days
    return round(days_absent * daily_rate, 2)


def compute_net_salary(inputs: SalaryInputs) -> SalaryBreakdown:
    """Compute full salary breakdown from attendance metrics and salary config.

    This is the single entry point for salary calculation. It orchestrates
    all sub-calculations and returns an immutable breakdown.

    Pure function: same inputs → same outputs. No side effects.
    """
    hourly_rate = calculate_hourly_rate(
        inputs.base_salary,
        inputs.office_working_days,
        inputs.standard_hours_per_day,
    )

    overtime_pay = calculate_overtime_pay(
        inputs.overtime_hours,
        hourly_rate,
        inputs.overtime_multiplier,
    )

    undertime_deductions = calculate_undertime_deductions(
        inputs.undertime_hours,
        hourly_rate,
        inputs.deduction_rate,
    )

    absence_deductions = calculate_absence_deductions(
        inputs.days_absent,
        inputs.base_salary,
        inputs.office_working_days,
    )

    net_salary = round(
        inputs.base_salary + overtime_pay - undertime_deductions - absence_deductions,
        2,
    )

    return SalaryBreakdown(
        base_salary=round(inputs.base_salary, 2),
        hourly_rate=round(hourly_rate, 2),
        overtime_pay=overtime_pay,
        undertime_deductions=undertime_deductions,
        absence_deductions=absence_deductions,
        net_salary=net_salary,
    )
