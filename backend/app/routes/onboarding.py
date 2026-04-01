"""Onboarding routes — employee onboarding workflows and tasks."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.onboarding import EmployeeOnboarding as EmployeeOnboardingModel
from app.services.onboarding_service import OnboardingService
from app.container import get_onboarding_service
from app.authorization.dependencies import require
from app.authorization.permissions import Permission
from app.schemas.onboarding import (
    OnboardingWorkflow, OnboardingWorkflowCreate,
    EmployeeOnboarding, EmployeeOnboardingCreate,
    EmployeeTaskProgress, EmployeeTaskProgressUpdate,
    EmployeeOnboardingSummary
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


# ── Employee Endpoints ──────────────────────────────────────────────

@router.get("/my", response_model=List[EmployeeOnboardingSummary])
def get_my_onboarding_summaries(
    current_user: User = Depends(require(Permission.VIEW_OWN_ONBOARDING)),
    service: OnboardingService = Depends(get_onboarding_service)
):
    """Get summaries of all assigned onboarding workflows."""
    return service.get_onboarding_summary(current_user.id)


@router.get("/my/{onboarding_id}", response_model=EmployeeOnboarding)
def get_my_onboarding_detail(
    onboarding_id: int,
    current_user: User = Depends(require(Permission.VIEW_OWN_ONBOARDING)),
    db: Session = Depends(get_db)
):
    """Get detailed view of a specific assigned onboarding workflow."""
    ob = db.query(EmployeeOnboardingModel).filter(
        EmployeeOnboardingModel.id == onboarding_id,
        EmployeeOnboardingModel.user_id == current_user.id
    ).first()
    if not ob:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Onboarding not found")
    return ob


@router.patch("/tasks/{progress_id}", response_model=EmployeeTaskProgress)
def update_task_status(
    progress_id: int,
    update_data: EmployeeTaskProgressUpdate,
    current_user: User = Depends(require(Permission.VIEW_OWN_ONBOARDING)),
    service: OnboardingService = Depends(get_onboarding_service)
):
    """Mark a task as completed or update notes."""
    return service.update_task_progress(current_user.id, progress_id, update_data)


# ── Admin Endpoints ─────────────────────────────────────────────────

@router.post("/admin/templates", response_model=OnboardingWorkflow)
def create_template(
    workflow_data: OnboardingWorkflowCreate,
    current_user: User = Depends(require(Permission.MANAGE_ONBOARDING)),
    service: OnboardingService = Depends(get_onboarding_service)
):
    """Create a new onboarding workflow template."""
    return service.create_workflow_template(workflow_data)


@router.put("/admin/templates/{template_id}", response_model=OnboardingWorkflow)
def update_template(
    template_id: int,
    workflow_data: OnboardingWorkflowCreate,
    current_user: User = Depends(require(Permission.MANAGE_ONBOARDING)),
    service: OnboardingService = Depends(get_onboarding_service)
):
    """Update an onboarding workflow template."""
    return service.update_template(template_id, workflow_data)


@router.get("/admin/templates", response_model=List[OnboardingWorkflow])
def list_templates(
    current_user: User = Depends(require(Permission.MANAGE_ONBOARDING)),
    service: OnboardingService = Depends(get_onboarding_service)
):
    """List all onboarding templates."""
    return service.get_all_templates()


@router.delete("/admin/templates/{template_id}")
def delete_template(
    template_id: int,
    current_user: User = Depends(require(Permission.MANAGE_ONBOARDING)),
    service: OnboardingService = Depends(get_onboarding_service)
):
    """Delete an onboarding template."""
    service.delete_template(template_id)
    return {"message": "Template deleted successfully"}


@router.post("/admin/assign", response_model=EmployeeOnboarding)
def assign_workflow(
    assignment_data: EmployeeOnboardingCreate,
    current_user: User = Depends(require(Permission.MANAGE_ONBOARDING)),
    service: OnboardingService = Depends(get_onboarding_service)
):
    """Assign a workflow template to an employee."""
    return service.assign_onboarding(assignment_data)


@router.get("/admin/assignments")
def get_assignments(
    current_user: User = Depends(require(Permission.MANAGE_ONBOARDING)),
    service: OnboardingService = Depends(get_onboarding_service)
):
    """Get all onboarding assignments with progress."""
    return service.get_all_assignments()


@router.post("/admin/assignments/{assignment_id}/remind")
def send_reminder(
    assignment_id: int,
    current_user: User = Depends(require(Permission.MANAGE_ONBOARDING)),
    service: OnboardingService = Depends(get_onboarding_service)
):
    """Send reminder to employee for onboarding tasks."""
    service.send_reminder(assignment_id, current_user.id)
    return {"message": "Reminder sent successfully"}


@router.post("/admin/assignments/{assignment_id}/notes")
def add_note(
    assignment_id: int,
    note_data: dict,
    current_user: User = Depends(require(Permission.MANAGE_ONBOARDING)),
    service: OnboardingService = Depends(get_onboarding_service)
):
    """Add note to employee onboarding."""
    note = service.add_note(assignment_id, current_user.id, note_data.get("note", ""))
    return {"message": "Note added successfully", "note": note}


@router.get("/admin/assignments/{assignment_id}/notes")
def get_notes(
    assignment_id: int,
    current_user: User = Depends(require(Permission.MANAGE_ONBOARDING)),
    service: OnboardingService = Depends(get_onboarding_service)
):
    """Get all notes for an assignment."""
    return service.get_assignment_notes(assignment_id)
