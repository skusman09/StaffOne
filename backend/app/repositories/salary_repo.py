"""
Salary repository — all SalaryConfig and SalaryRecord database queries.
"""
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.salary import SalaryConfig, SalaryRecord
from app.repositories import BaseRepository


class SalaryRepository(BaseRepository):
    """Data access layer for SalaryConfig and SalaryRecord models."""

    def __init__(self, db: Session):
        super().__init__(db)

    # ── SalaryConfig ────────────────────────────────────────────────

    def get_current_config(self, user_id: int) -> Optional[SalaryConfig]:
        """Get current salary configuration for a user."""
        return self.db.query(SalaryConfig).filter(
            SalaryConfig.user_id == user_id,
            SalaryConfig.is_current == True
        ).first()

    def get_active_configs(self, user_id: int) -> List[SalaryConfig]:
        """Get all current configs for a user (for deactivation)."""
        return self.db.query(SalaryConfig).filter(
            SalaryConfig.user_id == user_id,
            SalaryConfig.is_current == True
        ).all()

    # ── SalaryRecord ────────────────────────────────────────────────

    def get_record(self, user_id: int, year: int, month: int) -> Optional[SalaryRecord]:
        """Get salary record for a user for a specific month."""
        return self.db.query(SalaryRecord).filter(
            SalaryRecord.user_id == user_id,
            SalaryRecord.year == year,
            SalaryRecord.month == month
        ).first()

    def get_record_by_id(self, record_id: int) -> Optional[SalaryRecord]:
        """Get salary record by ID."""
        return self.db.query(SalaryRecord).filter(SalaryRecord.id == record_id).first()

    def get_monthly_records(self, year: int, month: int) -> List[SalaryRecord]:
        """Get all salary records for a month."""
        return self.db.query(SalaryRecord).filter(
            SalaryRecord.year == year,
            SalaryRecord.month == month
        ).order_by(SalaryRecord.user_id).all()

    # ── User queries used by payroll ────────────────────────────────

    def get_active_users(self, user_id: Optional[int] = None) -> List[User]:
        """Get active users, optionally filtered by user_id."""
        if user_id:
            users = [self.db.query(User).filter(User.id == user_id, User.is_active == True).first()]
            return [u for u in users if u is not None]
        return self.db.query(User).filter(User.is_active == True).all()
