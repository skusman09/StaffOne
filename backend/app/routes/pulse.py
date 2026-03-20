from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User, Role
from app.utils.dependencies import get_current_user, require_role
from app.schemas.pulse import PulseSurvey, PulseSurveyCreate, PulseSurveyUpdate, PulseResponse, PulseResponseCreate, PulseSurveyWithStats
from app.services import pulse_service

router = APIRouter(prefix="/pulse", tags=["pulse"])


@router.get("/active", response_model=Optional[PulseSurvey])
def get_active(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the currently active pulse survey."""
    return pulse_service.get_active_survey(db)


@router.post("/respond", response_model=PulseResponse, status_code=status.HTTP_201_CREATED)
def respond(
    response_data: PulseResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a response to the current pulse survey."""
    return pulse_service.create_pulse_response(db, current_user, response_data)


# Admin routes
@router.post("/admin/create", response_model=PulseSurvey, dependencies=[Depends(require_role(Role.ADMIN))])
def create_survey(
    survey_data: PulseSurveyCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """Admin: Create a new pulse survey."""
    return pulse_service.create_pulse_survey(db, survey_data)


@router.get("/admin/all", response_model=List[PulseSurvey], dependencies=[Depends(require_role(Role.ADMIN))])
def get_all(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """Admin: Get all surveys."""
    return pulse_service.get_all_surveys(db)


@router.get("/admin/results/{survey_id}", response_model=PulseSurveyWithStats, dependencies=[Depends(require_role(Role.ADMIN))])
def get_results(
    survey_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """Admin: Get detailed stats for a survey."""
    return pulse_service.get_survey_results(db, survey_id)


@router.patch("/admin/update/{survey_id}", response_model=PulseSurvey, dependencies=[Depends(require_role(Role.ADMIN))])
def update_survey(
    survey_id: int,
    survey_data: PulseSurveyUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """Admin: Update/Deactivate a survey."""
    return pulse_service.update_pulse_survey(db, survey_id, survey_data)


@router.delete("/admin/delete/{survey_id}", dependencies=[Depends(require_role(Role.ADMIN))])
def delete_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """Admin: Delete a survey."""
    pulse_service.delete_pulse_survey(db, survey_id)
    return {"message": "Survey deleted successfully"}
