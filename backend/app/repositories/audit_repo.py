"""
Audit repository — all AuditLog database queries.
"""
from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.audit import AuditLog
from app.repositories import BaseRepository


class AuditRepository(BaseRepository):
    """Data access layer for AuditLog model."""

    def __init__(self, db: Session):
        super().__init__(db)

    def get_logs(
        self, skip: int = 0, limit: int = 50,
        user_id: Optional[int] = None, action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> tuple[List[AuditLog], int]:
        """Query audit logs with filters. Returns (logs, total_count)."""
        query = self.db.query(AuditLog)

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
        self, resource_type: str, resource_id: str, limit: int = 50
    ) -> List[AuditLog]:
        """Get audit history for a specific resource."""
        return self.db.query(AuditLog).filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == str(resource_id)
        ).order_by(desc(AuditLog.timestamp)).limit(limit).all()

    def delete_older_than(self, cutoff: datetime) -> int:
        """Delete audit logs older than cutoff date. Returns count deleted."""
        deleted = self.db.query(AuditLog).filter(AuditLog.timestamp < cutoff).delete()
        self.db.flush()
        return deleted
