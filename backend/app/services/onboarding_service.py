from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from app.models.onboarding import OnboardingWorkflow, OnboardingTask, EmployeeOnboarding as EmployeeOnboardingModel, EmployeeTaskProgress
from app.schemas.onboarding import OnboardingWorkflowCreate, EmployeeOnboardingCreate, EmployeeTaskProgressUpdate
from app.models.user import User
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime


# --- Admin: Template Management ---

def create_workflow_template(db: Session, workflow_data: OnboardingWorkflowCreate) -> OnboardingWorkflow:
    """Create an onboarding workflow template with tasks."""
    db_workflow = OnboardingWorkflow(
        title=workflow_data.title,
        description=workflow_data.description,
        is_active=workflow_data.is_active
    )
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)

    for task_data in workflow_data.tasks:
        db_task = OnboardingTask(
            workflow_id=db_workflow.id,
            **task_data.model_dump()
        )
        db.add(db_task)
    
    db.commit()
    db.refresh(db_workflow)
    return db_workflow


def update_template(db: Session, template_id: int, workflow_data: OnboardingWorkflowCreate) -> OnboardingWorkflow:
    """Update an onboarding workflow template and its tasks."""
    template = db.query(OnboardingWorkflow).filter(OnboardingWorkflow.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Update template details
    template.title = workflow_data.title
    template.description = workflow_data.description
    template.is_active = workflow_data.is_active
    
    # Delete existing tasks
    db.query(OnboardingTask).filter(OnboardingTask.workflow_id == template_id).delete()
    
    # Add new tasks
    for task_data in workflow_data.tasks:
        db_task = OnboardingTask(
            workflow_id=template_id,
            **task_data.model_dump()
        )
        db.add(db_task)
    
    db.commit()
    db.refresh(template)
    return template


def get_all_templates(db: Session) -> List[OnboardingWorkflow]:
    """Admin: Get all onboarding templates."""
    return db.query(OnboardingWorkflow).order_by(OnboardingWorkflow.created_at.desc()).all()


def delete_template(db: Session, template_id: int) -> None:
    """Admin: Delete an onboarding template and all related data."""
    template = db.query(OnboardingWorkflow).filter(OnboardingWorkflow.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Delete all employee assignments for this template
    db.query(EmployeeOnboardingModel).filter(EmployeeOnboardingModel.workflow_id == template_id).delete()
    
    # Delete all tasks for this template
    db.query(OnboardingTask).filter(OnboardingTask.workflow_id == template_id).delete()
    
    # Delete the template
    db.delete(template)
    db.commit()


def get_all_assignments(db: Session) -> List[dict]:
    """Admin: Get all onboarding assignments with progress."""
    assignments = db.query(EmployeeOnboardingModel).options(
        joinedload(EmployeeOnboardingModel.user),
        joinedload(EmployeeOnboardingModel.workflow),
        joinedload(EmployeeOnboardingModel.task_progress)
    ).all()
    
    result = []
    for assignment in assignments:
        total = len(assignment.task_progress)
        completed = sum(1 for p in assignment.task_progress if p.is_completed)
        
        result.append({
            "id": assignment.id,
            "user_id": assignment.user_id,
            "workflow_id": assignment.workflow_id,
            "status": assignment.status,
            "started_at": assignment.started_at,
            "completed_at": assignment.completed_at,
            "user": {
                "username": assignment.user.username,
                "email": assignment.user.email
            },
            "workflow": {
                "title": assignment.workflow.title
            },
            "progress_percentage": (completed / total * 100) if total > 0 else 0,
            "tasks_total": total,
            "tasks_completed": completed
        })
    
    return result


# --- Onboarding Management ---

def assign_onboarding(db: Session, assignment_data: EmployeeOnboardingCreate) -> EmployeeOnboardingModel:
    """Assign a workflow template to an employee."""
    # Check if user already has this onboarding
    existing = db.query(EmployeeOnboardingModel).filter(
        EmployeeOnboardingModel.user_id == assignment_data.user_id,
        EmployeeOnboardingModel.workflow_id == assignment_data.workflow_id
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow already assigned to this user")

    # Get workflow template
    workflow = db.query(OnboardingWorkflow).filter(OnboardingWorkflow.id == assignment_data.workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow template not found")

    # Create employee onboarding instance
    db_onboarding = EmployeeOnboardingModel(
        user_id=assignment_data.user_id,
        workflow_id=assignment_data.workflow_id
    )
    db.add(db_onboarding)
    db.commit()
    db.refresh(db_onboarding)

    # Initialize task progress for all tasks in the workflow
    for task in workflow.tasks:
        db_progress = EmployeeTaskProgress(
            employee_onboarding_id=db_onboarding.id,
            task_id=task.id,
            is_completed=False
        )
        db.add(db_progress)
    
    db.commit()
    db.refresh(db_onboarding)
    return db_onboarding


def get_employee_onboarding(db: Session, user_id: int) -> List[EmployeeOnboardingModel]:
    """Get all assigned onboarding workflows for an employee."""
    return db.query(EmployeeOnboardingModel).filter(EmployeeOnboardingModel.user_id == user_id).all()


def update_task_progress(
    db: Session, 
    user_id: int, 
    progress_id: int, 
    update_data: EmployeeTaskProgressUpdate
) -> EmployeeTaskProgress:
    """Update task completion status."""
    db_progress = db.query(EmployeeTaskProgress).join(EmployeeOnboardingModel).filter(
        EmployeeTaskProgress.id == progress_id,
        EmployeeOnboardingModel.user_id == user_id
    ).first()

    if not db_progress:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task progress record not found")

    # Update fields
    if update_data.is_completed and not db_progress.is_completed:
        db_progress.is_completed = True
        db_progress.completed_at = datetime.utcnow()
    elif not update_data.is_completed:
        db_progress.is_completed = False
        db_progress.completed_at = None
    
    if update_data.notes is not None:
        db_progress.notes = update_data.notes

    db.commit()
    db.refresh(db_progress)

    # Check if onboarding is now complete
    check_onboarding_completion(db, db_progress.employee_onboarding_id)
    
    return db_progress


def send_reminder(db: Session, assignment_id: int, admin_id: int) -> bool:
    """Send reminder notification to employee."""
    assignment = db.query(EmployeeOnboardingModel).filter(
        EmployeeOnboardingModel.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Create notification for employee
    from app.models.notification import Notification, NotificationType
    notification = Notification(
        user_id=assignment.user_id,
        notification_type=NotificationType.ONBOARDING_REMINDER,
        title="Onboarding Reminder",
        message=f"Reminder: Please complete your pending onboarding tasks for '{assignment.workflow.title}'",
        link=f"/onboarding/{assignment.id}"
    )
    db.add(notification)
    db.commit()
    
    # TODO: Send email notification here
    # send_email_notification(assignment.user.email, "Onboarding Reminder", message)
    
    return True


def add_note(db: Session, assignment_id: int, admin_id: int, note_text: str):
    """Add admin note to assignment."""
    assignment = db.query(EmployeeOnboardingModel).filter(
        EmployeeOnboardingModel.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Create note
    from app.models.onboarding import OnboardingNote
    note = OnboardingNote(
        employee_onboarding_id=assignment_id,
        admin_id=admin_id,
        note=note_text
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    
    # Create notification for employee
    from app.models.notification import Notification, NotificationType
    notification = Notification(
        user_id=assignment.user_id,
        notification_type=NotificationType.ONBOARDING_NOTE_ADDED,
        title="New Onboarding Note",
        message=f"Admin added a note to your onboarding: '{assignment.workflow.title}'",
        link=f"/onboarding/{assignment.id}"
    )
    db.add(notification)
    db.commit()
    
    return note


def get_assignment_notes(db: Session, assignment_id: int):
    """Get all notes for an assignment."""
    from app.models.onboarding import OnboardingNote
    from app.models.user import User
    
    notes = db.query(OnboardingNote, User).join(
        User, OnboardingNote.admin_id == User.id
    ).filter(
        OnboardingNote.employee_onboarding_id == assignment_id
    ).order_by(
        OnboardingNote.created_at.desc()
    ).all()
    
    return [
        {
            "id": note.id,
            "note": note.note,
            "created_at": note.created_at.isoformat(),
            "admin": {
                "username": user.username,
                "email": user.email
            }
        }
        for note, user in notes
    ]


def check_onboarding_completion(db: Session, onboarding_id: int):
    """Update onboarding status if all tasks are completed."""
    onboarding = db.query(EmployeeOnboardingModel).filter(EmployeeOnboardingModel.id == onboarding_id).first()
    if not onboarding:
        return

    all_completed = all(p.is_completed for p in onboarding.task_progress)
    if all_completed and onboarding.status != "completed":
        onboarding.status = "completed"
        onboarding.completed_at = datetime.utcnow()
        db.commit()
    elif not all_completed and onboarding.status == "completed":
        onboarding.status = "in_progress"
        onboarding.completed_at = None
        db.commit()


def get_onboarding_summary(db: Session, user_id: int) -> List[dict]:
    """Get a summary of onboarding progress for a user."""
    onboardings = db.query(EmployeeOnboardingModel).options(
        joinedload(EmployeeOnboardingModel.workflow),
        joinedload(EmployeeOnboardingModel.task_progress).joinedload(EmployeeTaskProgress.task)
    ).filter(EmployeeOnboardingModel.user_id == user_id).all()
    summaries = []
    
    for ob in onboardings:
        total = len(ob.task_progress)
        completed = sum(1 for p in ob.task_progress if p.is_completed)
        summaries.append({
            "id": ob.id,
            "workflow_title": ob.workflow.title,
            "status": ob.status,
            "progress_percentage": (completed / total * 100) if total > 0 else 0,
            "tasks_total": total,
            "tasks_completed": completed,
            "started_at": ob.started_at
        })
    
    return summaries
