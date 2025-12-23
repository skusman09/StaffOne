"""
Audit log routes for admin access.

Provides endpoints for viewing system audit trail.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.schemas.audit import AuditLogResponse, AuditLogListResponse
from app.services.audit_service import get_audit_logs, get_resource_history
from app.utils.dependencies import get_current_admin_user

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/", response_model=AuditLogListResponse)
def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action (CREATE, UPDATE, DELETE, etc.)"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type (user, attendance, payroll, etc.)"),
    start_date: Optional[datetime] = Query(None, description="Filter logs after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter logs before this date"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit logs with optional filters. Admin only.
    
    Returns paginated list of audit log entries.
    """
    logs, total = get_audit_logs(
        db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date
    )
    
    # Add user names to responses
    log_responses = []
    for log in logs:
        user_name = None
        if log.user:
            user_name = log.user.full_name or log.user.username
        
        log_responses.append(AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_name=user_name,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            old_values=log.old_values,
            new_values=log.new_values,
            description=log.description,
            ip_address=log.ip_address,
            timestamp=log.timestamp
        ))
    
    return AuditLogListResponse(
        logs=log_responses,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/resource/{resource_type}/{resource_id}", response_model=list[AuditLogResponse])
def get_resource_audit_history(
    resource_type: str,
    resource_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit history for a specific resource. Admin only.
    
    Useful for seeing all changes made to a specific record.
    """
    logs = get_resource_history(db, resource_type, resource_id, limit)
    
    return [
        AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_name=log.user.full_name or log.user.username if log.user else None,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            old_values=log.old_values,
            new_values=log.new_values,
            description=log.description,
            ip_address=log.ip_address,
            timestamp=log.timestamp
        )
        for log in logs
    ]


@router.get("/actions", response_model=list[str])
def get_action_types(
    current_user: User = Depends(get_current_admin_user),
):
    """Get list of available action types. Admin only."""
    return [
        "CREATE",
        "UPDATE", 
        "DELETE",
        "LOGIN",
        "LOGOUT",
        "CHECK_IN",
        "CHECK_OUT",
        "APPROVE",
        "REJECT",
        "GENERATE",
        "EXPORT"
    ]


@router.get("/resource-types", response_model=list[str])
def get_resource_types(
    current_user: User = Depends(get_current_admin_user),
):
    """Get list of available resource types. Admin only."""
    return [
        "user",
        "attendance",
        "payroll",
        "salary_config",
        "salary_record",
        "holiday",
        "leave",
        "config",
        "location"
    ]
