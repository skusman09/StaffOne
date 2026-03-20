from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.pulse import PulseSurvey, PulseResponse
from app.schemas.pulse import PulseSurveyCreate, PulseResponseCreate, PulseSurveyUpdate
from app.models.user import User
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime

def get_active_survey(db: Session) -> Optional[PulseSurvey]:
    """Get the currently active pulse survey."""
    return db.query(PulseSurvey).filter(PulseSurvey.is_active == True).order_by(PulseSurvey.created_at.desc()).first()


def create_pulse_response(db: Session, user: User, response_data: PulseResponseCreate) -> PulseResponse:
    """Submit a response to a pulse survey."""
    # Check if survey exists and is active
    survey = db.query(PulseSurvey).filter(PulseSurvey.id == response_data.survey_id).first()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    if not survey.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Survey is no longer active")

    # Check if user already responded
    existing = db.query(PulseResponse).filter(
        PulseResponse.survey_id == response_data.survey_id,
        PulseResponse.user_id == user.id
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already responded to this survey")

    db_response = PulseResponse(
        user_id=user.id,
        **response_data.model_dump()
    )
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response


def create_pulse_survey(db: Session, survey_data: PulseSurveyCreate) -> PulseSurvey:
    """Admin: Create a new pulse survey."""
    # Deactivate other surveys if needed? For now, just allow multiple but the 'get_active' gets the latest.
    db_survey = PulseSurvey(**survey_data.model_dump())
    db.add(db_survey)
    db.commit()
    db.refresh(db_survey)
    return db_survey


def update_pulse_survey(db: Session, survey_id: int, survey_data: PulseSurveyUpdate) -> PulseSurvey:
    """Admin: Update/Deactivate a pulse survey."""
    db_survey = db.query(PulseSurvey).filter(PulseSurvey.id == survey_id).first()
    if not db_survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    
    for key, value in survey_data.model_dump(exclude_unset=True).items():
        setattr(db_survey, key, value)
    
    db.commit()
    db.refresh(db_survey)
    return db_survey


def get_survey_results(db: Session, survey_id: int):
    """Admin: Get survey results with stats."""
    survey = db.query(PulseSurvey).filter(PulseSurvey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    stats = db.query(
        func.count(PulseResponse.id).label("count"),
        func.avg(PulseResponse.rating).label("average")
    ).filter(PulseResponse.survey_id == survey_id).first()

    return {
        "id": survey.id,
        "question": survey.question,
        "is_active": survey.is_active,
        "created_at": survey.created_at,
        "updated_at": survey.updated_at,
        "response_count": stats.count or 0,
        "average_rating": float(stats.average or 0),
        "responses": survey.responses
    }


def get_all_surveys(db: Session) -> List[dict]:
    """Admin: Get all pulse surveys with stats."""
    surveys = db.query(PulseSurvey).order_by(PulseSurvey.created_at.desc()).all()
    
    result = []
    for survey in surveys:
        # Get stats for each survey
        stats = db.query(
            func.count(PulseResponse.id).label("count"),
            func.avg(PulseResponse.rating).label("average")
        ).filter(PulseResponse.survey_id == survey.id).first()
        
        result.append({
            "id": survey.id,
            "question": survey.question,
            "is_active": survey.  is_active,
            "created_at": survey.created_at,
            "updated_at": survey.updated_at,
            "response_count": stats.count or 0,
            "average_rating": float(stats.average or 0),
        })
    
    return result


def delete_pulse_survey(db: Session, survey_id: int) -> None:
    """Admin: Delete a pulse survey and all its responses."""
    survey = db.query(PulseSurvey).filter(PulseSurvey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    # Delete all responses first (due to foreign key constraint)
    db.query(PulseResponse).filter(PulseResponse.survey_id == survey_id).delete()
    
    # Delete the survey
    db.delete(survey)
    db.commit()
