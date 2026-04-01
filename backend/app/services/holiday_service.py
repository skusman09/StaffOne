"""
Holiday service — business logic for holiday management.

Architecture:
- Accepts IHolidayRepository via constructor (DIP)
- Uses @transactional for consistent transaction management
"""
import logging
from typing import Optional, List
from datetime import date

from sqlalchemy.orm import Session

from app.models.holiday import Holiday
from app.schemas.holiday import HolidayCreate, HolidayUpdate
from app.core.transaction import transactional
from app.interfaces.repositories import IHolidayRepository
from app.repositories.holiday_repo import HolidayRepository

logger = logging.getLogger(__name__)


class HolidayService:
    """Handles all holiday-related business logic."""

    def __init__(self, db: Session, repo: IHolidayRepository = None):
        self.db = db
        self.repo = repo or HolidayRepository(db)

    def get_holiday(self, holiday_id: int) -> Optional[Holiday]:
        """Get a holiday by ID."""
        return self.repo.get_by_id(holiday_id)

    def get_holiday_by_date(self, holiday_date: date) -> Optional[Holiday]:
        """Get a holiday by date."""
        return self.repo.get_by_date(holiday_date)

    def get_holidays(
        self, year: Optional[int] = None, active_only: bool = True,
        skip: int = 0, limit: int = 100
    ) -> List[Holiday]:
        """Get all holidays, optionally filtered by year."""
        return self.repo.get_all(year, active_only, skip, limit)

    def get_holidays_in_range(self, start_date: date, end_date: date, active_only: bool = True) -> List[Holiday]:
        """Get holidays within a date range."""
        return self.repo.get_in_range(start_date, end_date, active_only)

    def count_holidays_in_range(self, start_date: date, end_date: date, active_only: bool = True) -> int:
        """Count holidays within a date range."""
        return self.repo.count_in_range(start_date, end_date, active_only)

    @transactional
    def create_holiday(self, holiday: HolidayCreate) -> Holiday:
        """Create a new holiday."""
        db_holiday = Holiday(
            holiday_date=holiday.holiday_date,
            name=holiday.name,
            description=holiday.description,
            is_active=True
        )
        self.repo.add(db_holiday)
        self.db.flush()
        self.db.refresh(db_holiday)
        return db_holiday

    @transactional
    def update_holiday(self, holiday_id: int, holiday: HolidayUpdate) -> Optional[Holiday]:
        """Update an existing holiday."""
        db_holiday = self.repo.get_by_id(holiday_id)
        if not db_holiday:
            return None
        update_data = holiday.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_holiday, field, value)
        self.db.flush()
        self.db.refresh(db_holiday)
        return db_holiday

    @transactional
    def delete_holiday(self, holiday_id: int) -> bool:
        """Delete a holiday."""
        db_holiday = self.repo.get_by_id(holiday_id)
        if not db_holiday:
            return False
        self.repo.delete(db_holiday)
        return True

    def is_holiday(self, check_date: date) -> bool:
        """Check if a date is a holiday."""
        holiday = self.repo.get_by_date(check_date)
        return holiday is not None and holiday.is_active


# ── Backward-compatible module-level functions ──────────────────────

def get_holiday(db: Session, holiday_id: int):
    return HolidayService(db).get_holiday(holiday_id)

def get_holiday_by_date(db: Session, holiday_date: date):
    return HolidayService(db).get_holiday_by_date(holiday_date)

def get_holidays(db: Session, year=None, active_only=True, skip=0, limit=100):
    return HolidayService(db).get_holidays(year, active_only, skip, limit)

def get_holidays_in_range(db: Session, start_date: date, end_date: date, active_only=True):
    return HolidayService(db).get_holidays_in_range(start_date, end_date, active_only)

def count_holidays_in_range(db: Session, start_date: date, end_date: date, active_only=True):
    return HolidayService(db).count_holidays_in_range(start_date, end_date, active_only)

def create_holiday(db: Session, holiday: HolidayCreate):
    return HolidayService(db).create_holiday(holiday)

def update_holiday(db: Session, holiday_id: int, holiday: HolidayUpdate):
    return HolidayService(db).update_holiday(holiday_id, holiday)

def delete_holiday(db: Session, holiday_id: int):
    return HolidayService(db).delete_holiday(holiday_id)

def is_holiday(db: Session, check_date: date):
    return HolidayService(db).is_holiday(check_date)
