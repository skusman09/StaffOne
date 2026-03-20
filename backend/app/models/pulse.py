from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class PulseSurvey(Base):
    """Model for a pulse survey question."""
    __tablename__ = "pulse_surveys"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    responses = relationship("PulseResponse", back_populates="survey", cascade="all, delete-orphan")


class PulseResponse(Base):
    """Model for an employee's response to a pulse survey."""
    __tablename__ = "pulse_responses"

    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("pulse_surveys.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 rating
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    survey = relationship("PulseSurvey", back_populates="responses")
    user = relationship("User")
