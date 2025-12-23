"""
Audit log service for tracking changes.

Provides functions for logging and querying audit entries.
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.models.audit import AuditLog
from app.models.user import User


def log_action(
    db: Session,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    user_id: Optional[int] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AuditLog:
    """Create an audit log entry.
    
    Args:
        db: Database session
        action: Action type (CREATE, UPDATE, DELETE, etc.)
        resource_type: Type of resource affected
        resource_id: ID of the affected resource
        user_id: ID of user who performed the action
        old_values: Previous state (for UPDATE/DELETE)
        new_values: New state (for CREATE/UPDATE)
        description: Human-readable description
        ip_address: Client IP address
        user_agent: Client user agent
    
    Returns:
        Created AuditLog entry
    """
    log = AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        user_id=user_id,
        old_values=old_values,
        new_values=new_values,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_audit_logs(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> tuple[List[AuditLog], int]:
    """Query audit logs with filters.
    
    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum records to return
        user_id: Filter by user ID
        action: Filter by action type
        resource_type: Filter by resource type
        start_date: Filter logs after this date
        end_date: Filter logs before this date
    
    Returns:
        Tuple of (logs list, total count)
    """
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    
    total = query.count()
    logs = query.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit).all()
    
    return logs, total


def get_resource_history(
    db: Session,
    resource_type: str,
    resource_id: str,
    limit: int = 50
) -> List[AuditLog]:
    """Get audit history for a specific resource.
    
    Args:
        db: Database session
        resource_type: Type of resource
        resource_id: ID of the resource
        limit: Maximum records to return
    
    Returns:
        List of audit logs for the resource
    """
    return db.query(AuditLog).filter(
        AuditLog.resource_type == resource_type,
        AuditLog.resource_id == str(resource_id)
    ).order_by(desc(AuditLog.timestamp)).limit(limit).all()
