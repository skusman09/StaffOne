"""Pulse survey routes — employee engagement surveys."""
from fastapi import APIRouter, Depends, status
from typing import List, Optional

from app.models.user import User
from app.services.pulse_service import PulseService
from app.container import get_pulse_service
from app.authorization.dependencies import require
from app.authorization.permissions import Permission
from app.schemas.pulse import PulseSurvey, PulseSurveyCreate, PulseSurveyUpdate, PulseResponse, PulseResponseCreate, PulseSurveyWithStats

router = APIRouter(prefix="/pulse", tags=["pulse"])


@router.get("/active", response_model=Optional[PulseSurvey])
def get_active(
    current_user: User = Depends(require(Permission.RESPOND_PULSE)),
    service: PulseService = Depends(get_pulse_service)
):
    """Get the currently active pulse survey."""
    return service.get_active_survey()


@router.post("/respond", response_model=PulseResponse, status_code=status.HTTP_201_CREATED)
def respond(
    response_data: PulseResponseCreate,
    current_user: User = Depends(require(Permission.RESPOND_PULSE)),
    service: PulseService = Depends(get_pulse_service)
):
    """Submit a response to the current pulse survey."""
    return service.create_pulse_response(current_user, response_data)


# ── Admin ───────────────────────────────────────────────────────────

@router.post("/admin/create", response_model=PulseSurvey)
def create_survey(
    survey_data: PulseSurveyCreate,
    current_user: User = Depends(require(Permission.MANAGE_PULSE)),
    service: PulseService = Depends(get_pulse_service)
):
    """Create a new pulse survey."""
    return service.create_pulse_survey(survey_data)


@router.get("/admin/all", response_model=List[PulseSurvey])
def get_all(
    current_user: User = Depends(require(Permission.MANAGE_PULSE)),
    service: PulseService = Depends(get_pulse_service)
):
    """Get all surveys."""
    return service.get_all_surveys()


@router.get("/admin/results/{survey_id}", response_model=PulseSurveyWithStats)
def get_results(
    survey_id: int,
    current_user: User = Depends(require(Permission.MANAGE_PULSE)),
    service: PulseService = Depends(get_pulse_service)
):
    """Get detailed stats for a survey."""
    return service.get_survey_results(survey_id)


@router.patch("/admin/update/{survey_id}", response_model=PulseSurvey)
def update_survey(
    survey_id: int,
    survey_data: PulseSurveyUpdate,
    current_user: User = Depends(require(Permission.MANAGE_PULSE)),
    service: PulseService = Depends(get_pulse_service)
):
    """Update/Deactivate a survey."""
    return service.update_pulse_survey(survey_id, survey_data)


@router.delete("/admin/delete/{survey_id}")
def delete_survey(
    survey_id: int,
    current_user: User = Depends(require(Permission.MANAGE_PULSE)),
    service: PulseService = Depends(get_pulse_service)
):
    """Delete a survey."""
    service.delete_pulse_survey(survey_id)
    return {"message": "Survey deleted successfully"}
