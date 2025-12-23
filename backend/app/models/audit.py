"""
Audit log model for tracking changes.

Provides enterprise-grade audit trail for compliance.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class AuditLog(Base):
    """Audit log for tracking system changes.
    
    Records all significant actions for compliance and debugging.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Who performed the action
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # What action was performed
    action = Column(String(50), nullable=False, index=True)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.
    
    # What resource was affected
    resource_type = Column(String(50), nullable=False, index=True)  # user, attendance, payroll, holiday, config, etc.
    resource_id = Column(String(100), nullable=True)  # ID of the affected resource
    
    # What changed
    old_values = Column(JSON, nullable=True)  # Previous state (for UPDATE/DELETE)
    new_values = Column(JSON, nullable=True)  # New state (for CREATE/UPDATE)
    
    # Additional context
    description = Column(Text, nullable=True)  # Human-readable description
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # When
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} {self.resource_type} by user={self.user_id}>"
