from sqlalchemy import Column, Integer, String, Float, Date, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class SalaryStatus(str, enum.Enum):
    """Status of salary record."""
    DRAFT = "draft"           # Calculated but not finalized
    PENDING = "pending"       # Awaiting approval
    APPROVED = "approved"     # Approved by admin
    PAID = "paid"             # Salary disbursed
    CANCELLED = "cancelled"   # Cancelled/voided


class SalaryConfig(Base):
    """Salary configuration per user.
    
    Stores salary settings that can change over time.
    Only one config per user should be marked as is_current=True.
    """
    __tablename__ = "salary_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Salary settings
    monthly_base_salary = Column(Float, nullable=False)
    hourly_rate = Column(Float, nullable=True)  # Auto-calculated if not set
    overtime_multiplier = Column(Float, default=1.5, nullable=False)  # 1.5x default
    deduction_rate_per_hour = Column(Float, default=1.0, nullable=False)  # 1x hourly rate
    
    # Effective period
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)  # Null = still active
    is_current = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="salary_configs")

    def __repr__(self):
        return f"<SalaryConfig user_id={self.user_id} base={self.monthly_base_salary}>"


class SalaryRecord(Base):
    """Monthly salary record for each employee.
    
    Contains calculated attendance metrics and salary breakdown.
    Generated monthly based on attendance data.
    """
    __tablename__ = "salary_records"
    __table_args__ = (
        Index("ix_salary_user_period", "user_id", "year", "month"),
        UniqueConstraint("user_id", "year", "month", name="uq_salary_user_period"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Period
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)
    
    # Attendance Metrics
    office_working_days = Column(Integer, nullable=False)  # Excludes weekends & holidays
    days_worked = Column(Integer, nullable=False, default=0)
    days_absent = Column(Integer, nullable=False, default=0)
    
    # Hours Metrics
    total_hours_worked = Column(Float, nullable=False, default=0.0)
    expected_hours = Column(Float, nullable=False, default=0.0)  # office_days * standard_hours
    average_hours_per_day = Column(Float, nullable=False, default=0.0)
    
    # Overtime Metrics
    overtime_days = Column(Integer, nullable=False, default=0)
    overtime_hours = Column(Float, nullable=False, default=0.0)
    
    # Undertime/Deduction Metrics
    undertime_hours = Column(Float, nullable=False, default=0.0)
    
    # Salary Breakdown
    base_salary = Column(Float, nullable=False, default=0.0)
    hourly_rate_used = Column(Float, nullable=False, default=0.0)
    overtime_pay = Column(Float, nullable=False, default=0.0)
    deductions = Column(Float, nullable=False, default=0.0)
    absence_deductions = Column(Float, nullable=False, default=0.0)
    net_salary = Column(Float, nullable=False, default=0.0)
    
    # Status
    status = Column(SQLEnum(SalaryStatus), default=SalaryStatus.DRAFT, nullable=False)
    remarks = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="salary_records")
    approved_by = relationship("User", foreign_keys=[approved_by_id])

    def __repr__(self):
        return f"<SalaryRecord user_id={self.user_id} {self.year}-{self.month} net={self.net_salary}>"


class SystemConfig(Base):
    """System-wide configuration settings.
    
    Key-value store for configurable business rules.
    """
    __tablename__ = "system_configs"

    key = Column(String(100), primary_key=True)
    value = Column(String(500), nullable=False)
    description = Column(String(500), nullable=True)
    value_type = Column(String(20), default="string", nullable=False)  # string, int, float, bool
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SystemConfig {self.key}={self.value}>"
    
    @property
    def typed_value(self):
        """Return value converted to appropriate type."""
        if self.value_type == "int":
            return int(self.value)
        elif self.value_type == "float":
            return float(self.value)
        elif self.value_type == "bool":
            return self.value.lower() in ("true", "1", "yes")
        return self.value
