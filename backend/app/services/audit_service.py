"""
Audit service — business logic for audit logging and querying.

Architecture:
- Accepts IAuditRepository via constructor (DIP)
- Uses @transactional for consistent transaction management
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.core.transaction import transactional
from app.interfaces.repositories import IAuditRepository
from app.repositories.audit_repo import AuditRepository

logger = logging.getLogger(__name__)


class AuditService:
    """Handles all audit log operations."""

    def __init__(self, db: Session, repo: IAuditRepository = None):
        self.db = db
        self.repo = repo or AuditRepository(db)

    @transactional
    def log_action(
        self, action: str, resource_type: str,
        resource_id: Optional[str] = None, user_id: Optional[int] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None, user_agent: Optional[str] = None
    ) -> AuditLog:
        """Create an audit log entry."""
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
        self.repo.add(log)
        self.db.flush()
        self.db.refresh(log)
        return log

    def get_audit_logs(
        self, skip: int = 0, limit: int = 50,
        user_id: Optional[int] = None, action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> tuple[List[AuditLog], int]:
        """Query audit logs with filters."""
        return self.repo.get_logs(skip, limit, user_id, action, resource_type, start_date, end_date)

    def get_resource_history(self, resource_type: str, resource_id: str, limit: int = 50) -> List[AuditLog]:
        """Get audit history for a specific resource."""
        return self.repo.get_resource_history(resource_type, resource_id, limit)

    @transactional
    def cleanup_old_logs(self, cutoff: datetime) -> int:
        """Delete audit logs older than cutoff. Returns count deleted."""
        deleted = self.repo.delete_older_than(cutoff)
        return deleted




