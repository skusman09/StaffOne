from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime


class AuditLogCreate(BaseModel):
    """Schema for creating an audit log entry."""
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class AuditLogResponse(BaseModel):
    """Response schema for audit log."""
    id: int
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Response schema for listing audit logs."""
    logs: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
