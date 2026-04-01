"""
Dependency Injection Container — wires repositories into services.

Provides FastAPI Depends()-compatible factory functions that create
properly-wired service instances. Each factory is explicit: no magic,
no deep nesting, no auto-discovery.

Usage:
    @router.get("/admin/users")
    def get_users(service: AuthService = Depends(get_auth_service)):
        ...
"""
import logging

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db

# Repositories
from app.repositories.user_repo import UserRepository
from app.repositories.attendance_repo import AttendanceRepository
from app.repositories.leave_repo import LeaveRepository
from app.repositories.salary_repo import SalaryRepository
from app.repositories.holiday_repo import HolidayRepository
from app.repositories.notification_repo import NotificationRepository
from app.repositories.audit_repo import AuditRepository

# Services
from app.services.auth_service import AuthService
from app.services.attendance_service import AttendanceService
from app.services.leave_service import LeaveService
from app.services.payroll_service import PayrollService
from app.services.notification_service import NotificationService
from app.services.holiday_service import HolidayService
from app.services.audit_service import AuditService
from app.services.analytics_service import AnalyticsService
from app.services.location_service import LocationService
from app.services.pulse_service import PulseService
from app.services.onboarding_service import OnboardingService

logger = logging.getLogger(__name__)


# ── Service Factories ──────────────────────────────────────────────
# Each factory: Session → Repository → Service. One level deep. Explicit.

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db=db, user_repo=UserRepository(db))


def get_attendance_service(db: Session = Depends(get_db)) -> AttendanceService:
    return AttendanceService(db=db, repo=AttendanceRepository(db))


def get_leave_service(db: Session = Depends(get_db)) -> LeaveService:
    return LeaveService(db=db, repo=LeaveRepository(db))


def get_payroll_service(db: Session = Depends(get_db)) -> PayrollService:
    return PayrollService(
        db=db,
        salary_repo=SalaryRepository(db),
        attendance_repo=AttendanceRepository(db),
        user_repo=UserRepository(db),
    )


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(
        db=db,
        repo=NotificationRepository(db),
        user_repo=UserRepository(db),
    )


def get_holiday_service(db: Session = Depends(get_db)) -> HolidayService:
    return HolidayService(db=db, repo=HolidayRepository(db))


def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    return AuditService(db=db, repo=AuditRepository(db))


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db=db)


def get_location_service(db: Session = Depends(get_db)) -> LocationService:
    return LocationService(db=db)


def get_pulse_service(db: Session = Depends(get_db)) -> PulseService:
    return PulseService(db=db)


def get_onboarding_service(db: Session = Depends(get_db)) -> OnboardingService:
    return OnboardingService(db=db)
