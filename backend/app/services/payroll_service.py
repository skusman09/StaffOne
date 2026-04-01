"""
Payroll service — orchestration for salary calculation and payroll generation.

Architecture:
- Accepts repositories via constructor (DIP)
- Delegates computation to domain/salary_calculator and domain/working_days
- Uses @transactional for atomic payroll generation
- Service is orchestration only: load data → delegate to domain → persist
"""
import logging
import calendar
from typing import Optional, List, Dict
from datetime import date, datetime, timedelta
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.checkinout import CheckInOut
from app.models.salary import SalaryConfig, SalaryRecord, SalaryStatus
from app.core.config import settings
from app.core.transaction import transactional
from app.schemas.salary import (
    AttendanceMetrics, UserAttendanceReport, SalaryRecordResponse
)
from app.interfaces.repositories import ISalaryRepository, IAttendanceRepository, IUserRepository
from app.repositories.salary_repo import SalaryRepository
from app.repositories.attendance_repo import AttendanceRepository
from app.repositories.user_repo import UserRepository

# Domain layer — pure computation
from app.domain.salary_calculator import SalaryInputs, compute_net_salary
from app.domain.working_days import (
    calculate_office_working_days,
    get_office_dates,
    calculate_attendance_metrics as compute_metrics,
)
from app.services.holiday_service import HolidayService

logger = logging.getLogger(__name__)


def build_salary_response(record: SalaryRecord, user: User) -> SalaryRecordResponse:
    """Build SalaryRecordResponse from a record and user.

    Single helper eliminates 60+ lines of copy-pasted response construction.
    """
    return SalaryRecordResponse(
        id=record.id,
        user_id=record.user_id,
        user_full_name=user.full_name or user.username,
        user_email=user.email,
        year=record.year,
        month=record.month,
        office_working_days=record.office_working_days,
        days_worked=record.days_worked,
        days_absent=record.days_absent,
        total_hours_worked=record.total_hours_worked,
        average_hours_per_day=record.average_hours_per_day,
        overtime_days=record.overtime_days,
        overtime_hours=record.overtime_hours,
        undertime_hours=record.undertime_hours,
        base_salary=record.base_salary,
        hourly_rate_used=record.hourly_rate_used,
        overtime_pay=record.overtime_pay,
        deductions=record.deductions,
        absence_deductions=record.absence_deductions,
        net_salary=record.net_salary,
        status=record.status.value,
        remarks=record.remarks,
        created_at=record.created_at,
        approved_at=record.approved_at
    )


class PayrollService:
    """Orchestrates payroll operations. Computation delegated to domain layer."""

    def __init__(
        self,
        db: Session,
        salary_repo: ISalaryRepository = None,
        attendance_repo: IAttendanceRepository = None,
        user_repo: IUserRepository = None,
    ):
        self.db = db
        self.salary_repo = salary_repo or SalaryRepository(db)
        self.attendance_repo = attendance_repo or AttendanceRepository(db)
        self.user_repo = user_repo or UserRepository(db)

    # ── Working Days (delegates to domain) ──────────────────────────

    def get_office_working_days(
        self, start_date: date, end_date: date, weekend_days: List[int] = None
    ) -> int:
        """Calculate office working days excluding weekends and holidays."""
        if weekend_days is None:
            weekend_days = settings.weekend_days_list

        holidays = HolidayService(self.db).get_holidays_in_range(start_date, end_date)
        holiday_dates = {h.holiday_date for h in holidays}

        return calculate_office_working_days(start_date, end_date, weekend_days, holiday_dates)

    # ── Daily Hours ─────────────────────────────────────────────────

    @staticmethod
    def _get_daily_hours(records: List[CheckInOut]) -> Dict[date, float]:
        """Group attendance records by date and sum hours."""
        daily_hours = defaultdict(float)
        for record in records:
            if record.hours_worked is not None:
                record_date = record.check_in_time.date()
                daily_hours[record_date] += record.hours_worked
        return dict(daily_hours)

    # ── Attendance Metrics (delegates to domain) ────────────────────

    def calculate_attendance_metrics(
        self, user_id: int, start_date: date, end_date: date,
        standard_hours: float = None
    ) -> AttendanceMetrics:
        """Calculate comprehensive attendance metrics for a user."""
        if standard_hours is None:
            standard_hours = settings.OFFICE_STANDARD_HOURS

        # Get holiday dates for domain computation
        weekend_days = settings.weekend_days_list
        holidays = HolidayService(self.db).get_holidays_in_range(start_date, end_date)
        holiday_dates = {h.holiday_date for h in holidays}

        # Delegate to domain layer
        office_working_days = calculate_office_working_days(
            start_date, end_date, weekend_days, holiday_dates
        )
        office_dates = get_office_dates(start_date, end_date, weekend_days, holiday_dates)

        # Load attendance data
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        records = self.attendance_repo.get_completed_in_range(user_id, start_dt, end_dt)
        daily_hours = self._get_daily_hours(records)

        # Delegate metric computation to domain
        metrics = compute_metrics(daily_hours, office_working_days, office_dates, standard_hours)

        return AttendanceMetrics(
            office_working_days=metrics["office_working_days"],
            days_worked=metrics["days_worked"],
            days_absent=metrics["days_absent"],
            total_hours_worked=metrics["total_hours_worked"],
            expected_hours=metrics["expected_hours"],
            average_hours_per_day=metrics["average_hours_per_day"],
            overtime_days=metrics["overtime_days"],
            overtime_hours=metrics["overtime_hours"],
            undertime_hours=metrics["undertime_hours"],
        )

    # ── Attendance Report ───────────────────────────────────────────

    def get_user_attendance_report(
        self, user_id: int, start_date: date, end_date: date
    ) -> UserAttendanceReport:
        """Generate attendance report for a user."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        metrics = self.calculate_attendance_metrics(user_id, start_date, end_date)

        return UserAttendanceReport(
            user_id=user.id,
            user_full_name=user.full_name or user.username,
            user_email=user.email,
            period_start=start_date,
            period_end=end_date,
            metrics=metrics
        )

    # ── Salary Config ───────────────────────────────────────────────

    def get_user_salary_config(self, user_id: int) -> Optional[SalaryConfig]:
        """Get current salary configuration for a user."""
        return self.salary_repo.get_current_config(user_id)

    # ── Salary Calculation (delegates to domain) ────────────────────

    def calculate_salary(self, user_id: int, year: int, month: int) -> SalaryRecord:
        """Calculate salary for a user. Uses domain/salary_calculator for computation."""
        _, last_day = calendar.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        salary_config = self.salary_repo.get_current_config(user_id)

        if salary_config:
            base_salary = salary_config.monthly_base_salary
            overtime_multiplier = salary_config.overtime_multiplier
            deduction_rate = salary_config.deduction_rate_per_hour
        else:
            base_salary = user.monthly_base_salary or 0.0
            overtime_multiplier = settings.OVERTIME_MULTIPLIER
            deduction_rate = settings.DEDUCTION_RATE

        metrics = self.calculate_attendance_metrics(user_id, start_date, end_date)

        # Delegate to domain layer for pure salary computation
        salary_inputs = SalaryInputs(
            base_salary=base_salary,
            office_working_days=metrics.office_working_days,
            standard_hours_per_day=settings.OFFICE_STANDARD_HOURS,
            overtime_multiplier=overtime_multiplier,
            deduction_rate=deduction_rate,
            days_worked=metrics.days_worked,
            days_absent=metrics.days_absent,
            total_hours_worked=metrics.total_hours_worked,
            overtime_hours=metrics.overtime_hours,
            undertime_hours=metrics.undertime_hours,
        )
        breakdown = compute_net_salary(salary_inputs)

        # Upsert record
        existing = self.salary_repo.get_record(user_id, year, month)
        if existing:
            record = existing
        else:
            record = SalaryRecord(user_id=user_id, year=year, month=month)
            self.db.add(record)

        record.office_working_days = metrics.office_working_days
        record.days_worked = metrics.days_worked
        record.days_absent = metrics.days_absent
        record.total_hours_worked = metrics.total_hours_worked
        record.expected_hours = metrics.expected_hours
        record.average_hours_per_day = metrics.average_hours_per_day
        record.overtime_days = metrics.overtime_days
        record.overtime_hours = metrics.overtime_hours
        record.undertime_hours = metrics.undertime_hours
        record.base_salary = breakdown.base_salary
        record.hourly_rate_used = breakdown.hourly_rate
        record.overtime_pay = breakdown.overtime_pay
        record.deductions = breakdown.undertime_deductions
        record.absence_deductions = breakdown.absence_deductions
        record.net_salary = breakdown.net_salary
        record.status = SalaryStatus.DRAFT

        self.db.flush()
        return record

    @transactional
    def generate_monthly_payroll(
        self, year: int, month: int, user_id: Optional[int] = None
    ) -> List[SalaryRecord]:
        """Generate salary records for all (or specific) users. Atomic transaction."""
        users = self.salary_repo.get_active_users(user_id)

        records = []
        for user in users:
            try:
                record = self.calculate_salary(user.id, year, month)
                records.append(record)
            except Exception as e:
                logger.error(f"Error calculating salary for user {user.id}: {e}")

        # Flush all, @transactional will commit
        self.db.flush()
        for record in records:
            self.db.refresh(record)

        return records

    # ── Salary Records ──────────────────────────────────────────────

    def get_salary_record(self, user_id: int, year: int, month: int) -> Optional[SalaryRecord]:
        """Get salary record for a user for a specific month."""
        return self.salary_repo.get_record(user_id, year, month)

    def get_monthly_payroll(self, year: int, month: int) -> List[SalaryRecord]:
        """Get all salary records for a month."""
        return self.salary_repo.get_monthly_records(year, month)


# ── Backward-compatible module-level functions ──────────────────────

def calculate_attendance_metrics(db, user_id, start_date, end_date, standard_hours=None):
    return PayrollService(db).calculate_attendance_metrics(user_id, start_date, end_date, standard_hours)

def get_user_attendance_report(db, user_id, start_date, end_date):
    return PayrollService(db).get_user_attendance_report(user_id, start_date, end_date)

def calculate_salary(db, user_id, year, month):
    return PayrollService(db).calculate_salary(user_id, year, month)

def generate_monthly_payroll(db, year, month, user_id=None):
    return PayrollService(db).generate_monthly_payroll(year, month, user_id)

def get_salary_record(db, user_id, year, month):
    return PayrollService(db).get_salary_record(user_id, year, month)

def get_monthly_payroll(db, year, month):
    return PayrollService(db).get_monthly_payroll(year, month)

def get_user_salary_config(db, user_id):
    return PayrollService(db).get_user_salary_config(user_id)
