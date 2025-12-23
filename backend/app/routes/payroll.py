from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
import calendar

from app.database import get_db
from app.models.user import User
from app.models.salary import SalaryRecord, SalaryConfig, SalaryStatus
from app.utils.dependencies import get_current_user, get_current_admin_user
from app.services.payroll_service import (
    calculate_attendance_metrics, get_user_attendance_report,
    calculate_salary, generate_monthly_payroll, get_monthly_payroll,
    get_salary_record, get_user_salary_config
)
from app.schemas.salary import (
    UserAttendanceReport, AdminAttendanceReport, AttendanceMetrics,
    SalaryConfigCreate, SalaryConfigUpdate, SalaryConfigResponse,
    SalaryRecordResponse, PayrollSummary, GeneratePayrollRequest
)

router = APIRouter(prefix="/payroll", tags=["payroll"])


# ===== User Attendance Report =====

@router.get("/my-attendance", response_model=UserAttendanceReport)
def get_my_attendance_report(
    start_date: date = Query(..., description="Report start date"),
    end_date: date = Query(..., description="Report end date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's attendance report with all metrics.
    
    Includes: office working days, days worked, absences, total hours,
    average hours, overtime days/hours, undertime hours.
    """
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")
    
    return get_user_attendance_report(db, current_user.id, start_date, end_date)


@router.get("/my-salary", response_model=SalaryRecordResponse)
def get_my_salary(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's salary record for a month."""
    record = get_salary_record(db, current_user.id, year, month)
    if not record:
        raise HTTPException(status_code=404, detail="Salary record not found for this period")
    
    return SalaryRecordResponse(
        id=record.id,
        user_id=record.user_id,
        user_full_name=current_user.full_name or current_user.username,
        user_email=current_user.email,
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


# ===== Admin Attendance Reports =====

@router.get("/admin/attendance", response_model=AdminAttendanceReport)
def get_admin_attendance_report(
    start_date: date = Query(..., description="Report start date"),
    end_date: date = Query(..., description="Report end date"),
    user_id: Optional[int] = Query(None, description="Filter by specific user"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get attendance report for all users or specific user. Admin only.
    
    Returns comprehensive attendance metrics for the specified period.
    """
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")
    
    if user_id:
        users = db.query(User).filter(User.id == user_id, User.is_active == True).all()
    else:
        users = db.query(User).filter(User.is_active == True).all()
    
    reports = []
    for user in users:
        try:
            report = get_user_attendance_report(db, user.id, start_date, end_date)
            reports.append(report)
        except Exception as e:
            print(f"Error generating report for user {user.id}: {e}")
    
    return AdminAttendanceReport(
        period_start=start_date,
        period_end=end_date,
        total_users=len(reports),
        reports=reports
    )


# ===== Salary Config Management =====

@router.get("/admin/salary-config/{user_id}", response_model=SalaryConfigResponse)
def get_user_salary_config_endpoint(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get salary configuration for a user. Admin only."""
    config = get_user_salary_config(db, user_id)
    if not config:
        raise HTTPException(status_code=404, detail="Salary config not found for this user")
    return config


@router.post("/admin/salary-config", response_model=SalaryConfigResponse, status_code=201)
def create_salary_config(
    config: SalaryConfigCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create salary configuration for a user. Admin only.
    
    This will mark previous configs as not current.
    """
    # Mark existing configs as not current
    existing = db.query(SalaryConfig).filter(
        SalaryConfig.user_id == config.user_id,
        SalaryConfig.is_current == True
    ).all()
    
    for old_config in existing:
        old_config.is_current = False
        old_config.effective_to = config.effective_from
    
    # Create new config
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

@router.post("/admin/generate", response_model=PayrollSummary)
def generate_payroll(
    request: GeneratePayrollRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Generate salary records for a month. Admin only.
    
    Calculates attendance metrics and salary for all active users
    (or specific user if user_id provided).
    """
    records = generate_monthly_payroll(db, request.year, request.month, request.user_id)
    
    # Build response
    record_responses = []
    for record in records:
        user = record.user
        record_responses.append(SalaryRecordResponse(
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
        ))
    
    return PayrollSummary(
        year=request.year,
        month=request.month,
        total_employees=len(records),
        total_base_salary=sum(r.base_salary for r in records),
        total_overtime_pay=sum(r.overtime_pay for r in records),
        total_deductions=sum(r.deductions + r.absence_deductions for r in records),
        total_net_salary=sum(r.net_salary for r in records),
        records=record_responses
    )


@router.get("/admin/payroll", response_model=PayrollSummary)
def get_payroll_summary(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get payroll summary for a month. Admin only."""
    records = get_monthly_payroll(db, year, month)
    
    if not records:
        raise HTTPException(
            status_code=404, 
            detail=f"No payroll records found for {year}-{month:02d}. Generate payroll first."
        )
    
    record_responses = []
    for record in records:
        user = record.user
        record_responses.append(SalaryRecordResponse(
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
        ))
    
    return PayrollSummary(
        year=year,
        month=month,
        total_employees=len(records),
        total_base_salary=sum(r.base_salary for r in records),
        total_overtime_pay=sum(r.overtime_pay for r in records),
        total_deductions=sum(r.deductions + r.absence_deductions for r in records),
        total_net_salary=sum(r.net_salary for r in records),
        records=record_responses
    )


@router.patch("/admin/salary/{record_id}/approve")
def approve_salary_record(
    record_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Approve a salary record. Admin only."""
    from datetime import datetime
    
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
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Export payroll report as PDF. Admin only."""
    from fastapi.responses import Response
    from app.utils.pdf_generator import generate_payroll_pdf
    
    records = get_monthly_payroll(db, year, month)
    
    if not records:
        raise HTTPException(
            status_code=404, 
            detail=f"No payroll records found for {year}-{month:02d}. Generate payroll first."
        )
    
    # Convert to dict format for PDF generator
    records_data = []
    for record in records:
        user = record.user
        records_data.append({
            'user_full_name': user.full_name or user.username,
            'days_worked': record.days_worked,
            'total_hours_worked': record.total_hours_worked,
            'overtime_hours': record.overtime_hours,
            'base_salary': record.base_salary,
            'overtime_pay': record.overtime_pay,
            'deductions': record.deductions,
            'absence_deductions': record.absence_deductions,
            'net_salary': record.net_salary
        })
    
    try:
        pdf_bytes = generate_payroll_pdf(records_data, year, month)
        
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        filename = f"Payroll_{month_names[month-1]}_{year}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail="PDF generation not available. Install reportlab: pip install reportlab"
        )

