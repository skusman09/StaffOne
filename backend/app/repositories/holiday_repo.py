"""
Holiday repository — all Holiday-related database queries.
"""
from typing import Optional, List
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import extract

from app.models.holiday import Holiday
from app.repositories import BaseRepository


class HolidayRepository(BaseRepository):
    """Data access layer for Holiday model."""

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_id(self, holiday_id: int) -> Optional[Holiday]:
        """Get a holiday by ID."""
        return self.db.query(Holiday).filter(Holiday.id == holiday_id).first()

    def get_by_date(self, holiday_date: date) -> Optional[Holiday]:
        """Get a holiday by date."""
        return self.db.query(Holiday).filter(Holiday.holiday_date == holiday_date).first()

    def get_all(
        self, year: Optional[int] = None, active_only: bool = True,
        skip: int = 0, limit: int = 100
    ) -> List[Holiday]:
        """Get holidays, optionally filtered by year."""
        query = self.db.query(Holiday)
        if active_only:
            query = query.filter(Holiday.is_active == True)
        if year:
            query = query.filter(extract('year', Holiday.holiday_date) == year)
        return query.order_by(Holiday.holiday_date).offset(skip).limit(limit).all()

    def get_in_range(self, start_date: date, end_date: date, active_only: bool = True) -> List[Holiday]:
        """Get holidays within a date range."""
        query = self.db.query(Holiday).filter(
            Holiday.holiday_date >= start_date,
            Holiday.holiday_date <= end_date
        )
        if active_only:
            query = query.filter(Holiday.is_active == True)
        return query.order_by(Holiday.holiday_date).all()

    def count_in_range(self, start_date: date, end_date: date, active_only: bool = True) -> int:
        """Count holidays within a date range."""
        query = self.db.query(Holiday).filter(
            Holiday.holiday_date >= start_date,
            Holiday.holiday_date <= end_date
        )
        if active_only:
            query = query.filter(Holiday.is_active == True)
        return query.count()
