from sqlalchemy.orm import Session
from sqlalchemy import extract
from typing import Optional, List
from datetime import date
from app.models.holiday import Holiday
from app.schemas.holiday import HolidayCreate, HolidayUpdate


def get_holiday(db: Session, holiday_id: int) -> Optional[Holiday]:
    """Get a holiday by ID."""
    return db.query(Holiday).filter(Holiday.id == holiday_id).first()


def get_holiday_by_date(db: Session, holiday_date: date) -> Optional[Holiday]:
    """Get a holiday by date."""
    return db.query(Holiday).filter(Holiday.holiday_date == holiday_date).first()


def get_holidays(
    db: Session,
    year: Optional[int] = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100
) -> List[Holiday]:
    """Get all holidays, optionally filtered by year."""
    query = db.query(Holiday)
    
    if active_only:
        query = query.filter(Holiday.is_active == True)
    
    if year:
        query = query.filter(extract('year', Holiday.holiday_date) == year)
    
    return query.order_by(Holiday.holiday_date).offset(skip).limit(limit).all()


def get_holidays_in_range(
    db: Session,
    start_date: date,
    end_date: date,
    active_only: bool = True
) -> List[Holiday]:
    """Get holidays within a date range."""
    query = db.query(Holiday).filter(
        Holiday.holiday_date >= start_date,
        Holiday.holiday_date <= end_date
    )
    
    if active_only:
        query = query.filter(Holiday.is_active == True)
    
    return query.order_by(Holiday.holiday_date).all()


def count_holidays_in_range(
    db: Session,
    start_date: date,
    end_date: date,
    active_only: bool = True
) -> int:
    """Count holidays within a date range."""
    query = db.query(Holiday).filter(
        Holiday.holiday_date >= start_date,
        Holiday.holiday_date <= end_date
    )
    
    if active_only:
        query = query.filter(Holiday.is_active == True)
    
    return query.count()


def create_holiday(db: Session, holiday: HolidayCreate) -> Holiday:
    """Create a new holiday."""
    db_holiday = Holiday(
        holiday_date=holiday.holiday_date,
        name=holiday.name,
        description=holiday.description,
        is_active=True
    )
    db.add(db_holiday)
    db.commit()
    db.refresh(db_holiday)
    return db_holiday


def update_holiday(db: Session, holiday_id: int, holiday: HolidayUpdate) -> Optional[Holiday]:
    """Update an existing holiday."""
    db_holiday = get_holiday(db, holiday_id)
    if not db_holiday:
        return None
    
    update_data = holiday.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_holiday, field, value)
    
    db.commit()
    db.refresh(db_holiday)
    return db_holiday


def delete_holiday(db: Session, holiday_id: int) -> bool:
    """Delete a holiday."""
    db_holiday = get_holiday(db, holiday_id)
    if not db_holiday:
        return False
    
    db.delete(db_holiday)
    db.commit()
    return True


def is_holiday(db: Session, check_date: date) -> bool:
    """Check if a date is a holiday."""
    holiday = get_holiday_by_date(db, check_date)
    return holiday is not None and holiday.is_active
