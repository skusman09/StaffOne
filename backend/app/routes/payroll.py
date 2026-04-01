"""Payroll routes — salary calculation, payroll generation, export."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, datetime

from app.database import get_db
from app.models.user import User
from app.models.salary import SalaryRecord, SalaryConfig, SalaryStatus
from app.services.payroll_service import PayrollService, build_salary_response
from app.container import get_payroll_service
from app.authorization.dependencies import require
from app.authorization.permissions import Permission
from app.schemas.salary import (
    UserAttendanceReport, AdminAttendanceReport, AttendanceMetrics,
    SalaryConfigCreate, SalaryConfigUpdate, SalaryConfigResponse,
    SalaryRecordResponse, PayrollSummary, GeneratePayrollRequest
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payroll", tags=["payroll"])


# ===== User Endpoints =====

@router.get("/my-attendance", response_model=UserAttendanceReport)
def get_my_attendance_report(
    start_date: date = Query(..., description="Report start date"),
    end_date: date = Query(..., description="Report end date"),
    current_user: User = Depends(require(Permission.VIEW_OWN_ATTENDANCE)),
    service: PayrollService = Depends(get_payroll_service)
):
    """Get current user's attendance report with all metrics."""
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")
    return service.get_user_attendance_report(current_user.id, start_date, end_date)


@router.get("/my-salary", response_model=SalaryRecordResponse)
def get_my_salary(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(require(Permission.VIEW_OWN_SALARY)),
    service: PayrollService = Depends(get_payroll_service)
):
    """Get current user's salary record for a month."""
    record = service.get_salary_record(current_user.id, year, month)
    if not record:
        raise HTTPException(status_code=404, detail="Salary record not found for this period")
    return build_salary_response(record, current_user)


# ===== Admin Attendance Reports =====

@router.get("/admin/attendance", response_model=AdminAttendanceReport)
def get_admin_attendance_report(
    start_date: date = Query(..., description="Report start date"),
    end_date: date = Query(..., description="Report end date"),
    user_id: Optional[int] = Query(None, description="Filter by specific user"),
    current_user: User = Depends(require(Permission.VIEW_ANY_ATTENDANCE)),
    service: PayrollService = Depends(get_payroll_service),
    db: Session = Depends(get_db)
):
    """Get attendance report for all users or specific user."""
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")

    if user_id:
        users = db.query(User).filter(User.id == user_id, User.is_active == True).all()
    else:
        users = db.query(User).filter(User.is_active == True).all()

    reports = []
    for user in users:
        try:
            report = service.get_user_attendance_report(user.id, start_date, end_date)
            reports.append(report)
        except Exception as e:
            logger.error(f"Error generating report for user {user.id}: {e}")

    return AdminAttendanceReport(
        period_start=start_date, period_end=end_date,
        total_users=len(reports), reports=reports
    )


# ===== Salary Config =====

@router.get("/admin/salary-config/{user_id}", response_model=SalaryConfigResponse)
def get_user_salary_config_endpoint(
    user_id: int,
    current_user: User = Depends(require(Permission.MANAGE_SALARY_CONFIG)),
    service: PayrollService = Depends(get_payroll_service)
):
    """Get salary configuration for a user."""
    config = service.get_user_salary_config(user_id)
    if not config:
        raise HTTPException(status_code=404, detail="Salary config not found for this user")
    return config


@router.post("/admin/salary-config", response_model=SalaryConfigResponse, status_code=201)
def create_salary_config(
    config: SalaryConfigCreate,
    current_user: User = Depends(require(Permission.MANAGE_SALARY_CONFIG)),
    db: Session = Depends(get_db)
):
    """Create salary configuration for a user."""
    existing = db.query(SalaryConfig).filter(
        SalaryConfig.user_id == config.user_id,
        SalaryConfig.is_current == True
    ).all()

    for old_config in existing:
        old_config.is_current = False
        old_config.effective_to = config.effective_from

    new_config = SalaryConfig(
        user_id=config.user_id,
        monthly_base_salary=config.monthly_base_salary,
        hourly_rate=config.hourly_rate,
        overtime_multiplier=config.overtime_multiplier,
        deduction_rate_per_hour=config.deduction_rate_per_hour,
        effective_from=config.effective_from,
        is_current=True,
        created_by_id=current_user.id
    )

    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    return new_config


# ===== Payroll Generation =====

def _build_payroll_summary(records: List[SalaryRecord], year: int, month: int) -> PayrollSummary:
    """Build PayrollSummary from salary records."""
    record_responses = [build_salary_response(r, r.user) for r in records]
    return PayrollSummary(
        year=year, month=month,
        total_employees=len(records),
        total_base_salary=sum(r.base_salary for r in records),
        total_overtime_pay=sum(r.overtime_pay for r in records),
        total_deductions=sum(r.deductions + r.absence_deductions for r in records),
        total_net_salary=sum(r.net_salary for r in records),
        records=record_responses
    )


@router.post("/admin/generate", response_model=PayrollSummary)
def generate_payroll(
    request: GeneratePayrollRequest,
    current_user: User = Depends(require(Permission.GENERATE_PAYROLL)),
    service: PayrollService = Depends(get_payroll_service)
):
    """Generate salary records for a month."""
    records = service.generate_monthly_payroll(request.year, request.month, request.user_id)
    return _build_payroll_summary(records, request.year, request.month)


@router.get("/admin/payroll", response_model=PayrollSummary)
def get_payroll_summary(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(require(Permission.VIEW_ANY_SALARY)),
    service: PayrollService = Depends(get_payroll_service)
):
    """Get payroll summary for a month."""
    records = service.get_monthly_payroll(year, month)
    if not records:
        raise HTTPException(status_code=404, detail=f"No payroll records found for {year}-{month:02d}")
    return _build_payroll_summary(records, year, month)


@router.patch("/admin/salary/{record_id}/approve")
def approve_salary_record(
    record_id: int,
    current_user: User = Depends(require(Permission.APPROVE_SALARY)),
    db: Session = Depends(get_db)
):
    """Approve a salary record."""
    record = db.query(SalaryRecord).filter(SalaryRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Salary record not found")

    record.status = SalaryStatus.APPROVED
    record.approved_by_id = current_user.id
    record.approved_at = datetime.utcnow()
    db.commit()
    return {"message": "Salary record approved", "status": "approved"}


@router.get("/admin/export/pdf")
def export_payroll_pdf(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(require(Permission.EXPORT_PAYROLL)),
    service: PayrollService = Depends(get_payroll_service)
):
    """Export payroll report as PDF."""
    from app.utils.pdf_generator import generate_payroll_pdf

    records = service.get_monthly_payroll(year, month)
    if not records:
        raise HTTPException(status_code=404, detail=f"No payroll records found for {year}-{month:02d}")

    records_data = [{
        'user_full_name': r.user.full_name or r.user.username,
        'days_worked': r.days_worked, 'total_hours_worked': r.total_hours_worked,
        'overtime_hours': r.overtime_hours, 'base_salary': r.base_salary,
        'overtime_pay': r.overtime_pay, 'deductions': r.deductions,
        'absence_deductions': r.absence_deductions, 'net_salary': r.net_salary
    } for r in records]

    try:
        pdf_bytes = generate_payroll_pdf(records_data, year, month)
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']
        filename = f"Payroll_{month_names[month-1]}_{year}.pdf"
        return Response(
            content=pdf_bytes, media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ImportError:
        raise HTTPException(status_code=500, detail="PDF generation not available")
