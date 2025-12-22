from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, Text
from datetime import datetime
from app.database import Base


class Holiday(Base):
    """Holiday model for tracking company-wide holidays.
    
    Holidays are excluded from office working days calculation.
    """
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    holiday_date = Column(Date, unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Holiday {self.name} on {self.holiday_date}>"
