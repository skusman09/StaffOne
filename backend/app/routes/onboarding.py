from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User, Role
from app.models.onboarding import EmployeeOnboarding as EmployeeOnboardingModel, EmployeeTaskProgress as EmployeeTaskProgressModel
from app.utils.dependencies import get_current_user, require_role
from app.schemas.onboarding import (
    OnboardingWorkflow, OnboardingWorkflowCreate, 
    EmployeeOnboarding, EmployeeOnboardingCreate, 
    EmployeeTaskProgress, EmployeeTaskProgressUpdate,
    EmployeeOnboardingSummary
)
from app.services import onboarding_service

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


# --- Employee Endpoints ---

@router.get("/my", response_model=List[EmployeeOnboardingSummary])
def get_my_onboarding_summaries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get summaries of all assigned onboarding workflows for the current user."""
    return onboarding_service.get_onboarding_summary(db, current_user.id)


@router.get("/my/{onboarding_id}", response_model=EmployeeOnboarding)
def get_my_onboarding_detail(
    onboarding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a task as completed or update notes."""
    return onboarding_service.update_task_progress(db, current_user.id, progress_id, update_data)


# --- Admin Endpoints ---

@router.post("/admin/templates", response_model=OnboardingWorkflow, dependencies=[Depends(require_role(Role.ADMIN))])
def create_template(
    workflow_data: OnboardingWorkflowCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """Admin: Create a new onboarding workflow template."""
    return onboarding_service.create_workflow_template(db, workflow_data)


@router.put("/admin/templates/{template_id}", response_model=OnboardingWorkflow, dependencies=[Depends(require_role(Role.ADMIN))])
def update_template(
    template_id: int,
    workflow_data: OnboardingWorkflowCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """Admin: Update an onboarding workflow template."""
    return onboarding_service.update_template(db, template_id, workflow_data)


@router.get("/admin/templates", response_model=List[OnboardingWorkflow], dependencies=[Depends(require_role(Role.ADMIN))])
def list_templates(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """Admin: List all onboarding templates."""
    return onboarding_service.get_all_templates(db)


@router.delete("/admin/templates/{template_id}", dependencies=[Depends(require_role(Role.ADMIN))])
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """Admin: Delete an onboarding template."""
    onboarding_service.delete_template(db, template_id)
    return {"message": "Template deleted successfully"}


@router.post("/admin/assign", response_model=EmployeeOnboarding, dependencies=[Depends(require_role(Role.ADMIN))])
def assign_workflow(
    assignment_data: EmployeeOnboardingCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """Admin: Assign a workflow template to an employee."""
    return onboarding_service.assign_onboarding(db, assignment_data)


@router.get("/admin/assignments", dependencies=[Depends(require_role(Role.ADMIN))])
def get_assignments(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """Admin: Get all onboarding assignments with progress."""
    return onboarding_service.get_all_assignments(db)


@router.post("/admin/assignments/{assignment_id}/remind", dependencies=[Depends(require_role(Role.ADMIN))])
def send_reminder(
    assignment_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """Admin: Send reminder to employee for onboarding tasks."""
    onboarding_service.send_reminder(db, assignment_id, admin_user.id)
    return {"message": "Reminder sent successfully"}


@router.post("/admin/assignments/{assignment_id}/notes", dependencies=[Depends(require_role(Role.ADMIN))])
def add_note(
    assignment_id: int,
    note_data: dict,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """Admin: Add note to employee onboarding."""
    note = onboarding_service.add_note(db, assignment_id, admin_user.id, note_data.get("note", ""))
    return {"message": "Note added successfully", "note": note}


@router.get("/admin/assignments/{assignment_id}/notes", dependencies=[Depends(require_role(Role.ADMIN))])
def get_notes(
    assignment_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """Admin: Get all notes for an assignment."""
    return onboarding_service.get_assignment_notes(db, assignment_id)
