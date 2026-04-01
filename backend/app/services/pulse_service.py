"""
Pulse survey service — business logic for employee engagement surveys.

Architecture:
- Class-based service
- Uses @transactional for consist transaction management
- Fixes N+1 issue on survey statistics fetching
"""
import logging
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.pulse import PulseSurvey, PulseResponse
from app.models.user import User
from app.schemas.pulse import PulseSurveyCreate, PulseResponseCreate, PulseSurveyUpdate
from app.core.transaction import transactional

logger = logging.getLogger(__name__)


class PulseService:
    """Handles all pulse survey operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_active_survey(self) -> Optional[PulseSurvey]:
        """Get the currently active pulse survey."""
        return self.db.query(PulseSurvey).filter(
            PulseSurvey.is_active == True
        ).order_by(PulseSurvey.created_at.desc()).first()

    @transactional
    def create_pulse_response(self, user: User, response_data: PulseResponseCreate) -> PulseResponse:
        """Submit a response to a pulse survey."""
        survey = self.db.query(PulseSurvey).filter(PulseSurvey.id == response_data.survey_id).first()
        if not survey:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
        if not survey.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Survey is no longer active")

        existing = self.db.query(PulseResponse).filter(
            PulseResponse.survey_id == response_data.survey_id,
            PulseResponse.user_id == user.id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already responded to this survey")

        db_response = PulseResponse(
            user_id=user.id,
            **response_data.model_dump()
        )
        self.db.add(db_response)
        self.db.flush()
        self.db.refresh(db_response)
        return db_response

    @transactional
    def create_pulse_survey(self, survey_data: PulseSurveyCreate) -> PulseSurvey:
        """Admin: Create a new pulse survey."""
        db_survey = PulseSurvey(**survey_data.model_dump())
        self.db.add(db_survey)
        self.db.flush()
        self.db.refresh(db_survey)
        return db_survey

    @transactional
    def update_pulse_survey(self, survey_id: int, survey_data: PulseSurveyUpdate) -> PulseSurvey:
        """Admin: Update/Deactivate a pulse survey."""
        db_survey = self.db.query(PulseSurvey).filter(PulseSurvey.id == survey_id).first()
        if not db_survey:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

        for key, value in survey_data.model_dump(exclude_unset=True).items():
            setattr(db_survey, key, value)

        self.db.flush()
        self.db.refresh(db_survey)
        return db_survey

    def get_survey_results(self, survey_id: int) -> dict:
        """Admin: Get survey results with stats."""
        survey = self.db.query(PulseSurvey).filter(PulseSurvey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

        stats = self.db.query(
            func.count(PulseResponse.id).label("count"),
            func.avg(PulseResponse.rating).label("average")
        ).filter(PulseResponse.survey_id == survey_id).first()

        # Eager load users for responses to avoid N+1 reading responses list
        responses = self.db.query(PulseResponse).join(User).filter(
            PulseResponse.survey_id == survey_id
        ).all()

        return {
            "id": survey.id,
            "question": survey.question,
            "is_active": survey.is_active,
            "created_at": survey.created_at,
            "updated_at": survey.updated_at,
            "response_count": stats.count or 0,
            "average_rating": float(stats.average or 0),
            "responses": responses
        }

    def get_all_surveys(self) -> List[dict]:
        """Admin: Get all pulse surveys with stats in a single query."""
        surveys = self.db.query(PulseSurvey).order_by(PulseSurvey.created_at.desc()).all()

        # Fetch stats for all surveys at once to fix N+1
        stats = self.db.query(
            PulseResponse.survey_id,
            func.count(PulseResponse.id).label("count"),
            func.avg(PulseResponse.rating).label("average")
        ).group_by(PulseResponse.survey_id).all()

        stats_map = {
            s.survey_id: {"count": s.count, "average": float(s.average or 0)} 
            for s in stats
        }

        result = []
        for survey in surveys:
            s_stats = stats_map.get(survey.id, {"count": 0, "average": 0.0})
            result.append({
                "id": survey.id,
                "question": survey.question,
                "is_active": survey.is_active,
                "created_at": survey.created_at,
                "updated_at": survey.updated_at,
                "response_count": s_stats["count"],
                "average_rating": s_stats["average"],
            })

        return result

    @transactional
    def delete_pulse_survey(self, survey_id: int) -> None:
        """Admin: Delete a pulse survey and all its responses."""
        survey = self.db.query(PulseSurvey).filter(PulseSurvey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")

        self.db.query(PulseResponse).filter(PulseResponse.survey_id == survey_id).delete()
        self.db.delete(survey)


# ── Backward-compatible module-level functions ──────────────────────

def get_active_survey(db: Session) -> Optional[PulseSurvey]:
    return PulseService(db).get_active_survey()

def create_pulse_response(db: Session, user: User, response_data: PulseResponseCreate) -> PulseResponse:
    return PulseService(db).create_pulse_response(user, response_data)

def create_pulse_survey(db: Session, survey_data: PulseSurveyCreate) -> PulseSurvey:
    return PulseService(db).create_pulse_survey(survey_data)

def update_pulse_survey(db: Session, survey_id: int, survey_data: PulseSurveyUpdate) -> PulseSurvey:
    return PulseService(db).update_pulse_survey(survey_id, survey_data)

def get_survey_results(db: Session, survey_id: int) -> dict:
    return PulseService(db).get_survey_results(survey_id)

def get_all_surveys(db: Session) -> List[dict]:
    return PulseService(db).get_all_surveys()

def delete_pulse_survey(db: Session, survey_id: int) -> None:
    return PulseService(db).delete_pulse_survey(survey_id)
