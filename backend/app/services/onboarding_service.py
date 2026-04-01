"""
Onboarding service — business logic for employee onboarding management.

Architecture:
- Class-based service
- Uses @transactional to prevent double-commits and ensure atomicity
- Eager loads related models to avoid N+1 queries
"""
import logging
from typing import List
from datetime import datetime

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.onboarding import OnboardingWorkflow, OnboardingTask, EmployeeOnboarding as EmployeeOnboardingModel, EmployeeTaskProgress, OnboardingNote
from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.schemas.onboarding import OnboardingWorkflowCreate, EmployeeOnboardingCreate, EmployeeTaskProgressUpdate
from app.core.transaction import transactional

logger = logging.getLogger(__name__)


class OnboardingService:
    """Handles all onboarding templates, assignments, and tasks."""

    def __init__(self, db: Session):
        self.db = db

    # ── Admin: Template Management ────────────────────────────────────────

    @transactional
    def create_workflow_template(self, workflow_data: OnboardingWorkflowCreate) -> OnboardingWorkflow:
        """Create an onboarding workflow template with tasks."""
        db_workflow = OnboardingWorkflow(
            title=workflow_data.title,
            description=workflow_data.description,
            is_active=workflow_data.is_active
        )
        self.db.add(db_workflow)
        self.db.flush()  # Gets ID without committing

        for task_data in workflow_data.tasks:
            db_task = OnboardingTask(
                workflow_id=db_workflow.id,
                **task_data.model_dump()
            )
            self.db.add(db_task)

        self.db.flush()
        self.db.refresh(db_workflow)
        return db_workflow

    @transactional
    def update_template(self, template_id: int, workflow_data: OnboardingWorkflowCreate) -> OnboardingWorkflow:
        """Update an onboarding workflow template and its tasks."""
        template = self.db.query(OnboardingWorkflow).filter(OnboardingWorkflow.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        template.title = workflow_data.title
        template.description = workflow_data.description
        template.is_active = workflow_data.is_active

        # Replace existing tasks
        self.db.query(OnboardingTask).filter(OnboardingTask.workflow_id == template_id).delete()
        for task_data in workflow_data.tasks:
            db_task = OnboardingTask(
                workflow_id=template_id,
                **task_data.model_dump()
            )
            self.db.add(db_task)

        self.db.flush()
        self.db.refresh(template)
        return template

    def get_all_templates(self) -> List[OnboardingWorkflow]:
        """Admin: Get all onboarding templates."""
        return self.db.query(OnboardingWorkflow).order_by(OnboardingWorkflow.created_at.desc()).all()

    @transactional
    def delete_template(self, template_id: int) -> None:
        """Admin: Delete an onboarding template and all related data."""
        template = self.db.query(OnboardingWorkflow).filter(OnboardingWorkflow.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        self.db.query(EmployeeOnboardingModel).filter(EmployeeOnboardingModel.workflow_id == template_id).delete()
        self.db.query(OnboardingTask).filter(OnboardingTask.workflow_id == template_id).delete()
        self.db.delete(template)

    def get_all_assignments(self) -> List[dict]:
        """Admin: Get all onboarding assignments with progress."""
        assignments = self.db.query(EmployeeOnboardingModel).options(
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

    # ── Onboarding Management ─────────────────────────────────────────────

    @transactional
    def assign_onboarding(self, assignment_data: EmployeeOnboardingCreate) -> EmployeeOnboardingModel:
        """Assign a workflow template to an employee."""
        existing = self.db.query(EmployeeOnboardingModel).filter(
            EmployeeOnboardingModel.user_id == assignment_data.user_id,
            EmployeeOnboardingModel.workflow_id == assignment_data.workflow_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow already assigned to this user")

        workflow = self.db.query(OnboardingWorkflow).filter(OnboardingWorkflow.id == assignment_data.workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow template not found")

        db_onboarding = EmployeeOnboardingModel(
            user_id=assignment_data.user_id,
            workflow_id=assignment_data.workflow_id
        )
        self.db.add(db_onboarding)
        self.db.flush()

        for task in workflow.tasks:
            db_progress = EmployeeTaskProgress(
                employee_onboarding_id=db_onboarding.id,
                task_id=task.id,
                is_completed=False
            )
            self.db.add(db_progress)

        self.db.flush()
        self.db.refresh(db_onboarding)
        return db_onboarding

    def get_employee_onboarding(self, user_id: int) -> List[EmployeeOnboardingModel]:
        """Get all assigned onboarding workflows for an employee."""
        return self.db.query(EmployeeOnboardingModel).filter(EmployeeOnboardingModel.user_id == user_id).all()

    @transactional
    def update_task_progress(
        self, user_id: int, progress_id: int, update_data: EmployeeTaskProgressUpdate
    ) -> EmployeeTaskProgress:
        """Update task completion status."""
        db_progress = self.db.query(EmployeeTaskProgress).join(EmployeeOnboardingModel).filter(
            EmployeeTaskProgress.id == progress_id,
            EmployeeOnboardingModel.user_id == user_id
        ).first()

        if not db_progress:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task progress record not found")

        if update_data.is_completed and not db_progress.is_completed:
            db_progress.is_completed = True
            db_progress.completed_at = datetime.utcnow()
        elif not update_data.is_completed:
            db_progress.is_completed = False
            db_progress.completed_at = None

        if update_data.notes is not None:
            db_progress.notes = update_data.notes

        self.db.flush()
        self._check_onboarding_completion(db_progress.employee_onboarding_id)

        self.db.refresh(db_progress)
        return db_progress

    @transactional
    def send_reminder(self, assignment_id: int, admin_id: int) -> bool:
        """Send reminder notification to employee."""
        assignment = self.db.query(EmployeeOnboardingModel).filter(
            EmployeeOnboardingModel.id == assignment_id
        ).first()

        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        notification = Notification(
            user_id=assignment.user_id,
            notification_type=NotificationType.ONBOARDING_REMINDER,
            title="Onboarding Reminder",
            message=f"Reminder: Please complete your pending onboarding tasks for '{assignment.workflow.title}'",
            link=f"/onboarding/{assignment.id}"
        )
        self.db.add(notification)
        return True

    @transactional
    def add_note(self, assignment_id: int, admin_id: int, note_text: str) -> OnboardingNote:
        """Add admin note to assignment."""
        assignment = self.db.query(EmployeeOnboardingModel).filter(
            EmployeeOnboardingModel.id == assignment_id
        ).first()

        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        note = OnboardingNote(
            employee_onboarding_id=assignment_id,
            admin_id=admin_id,
            note=note_text
        )
        self.db.add(note)
        self.db.flush()
        self.db.refresh(note)

        notification = Notification(
            user_id=assignment.user_id,
            notification_type=NotificationType.ONBOARDING_NOTE_ADDED,
            title="New Onboarding Note",
            message=f"Admin added a note to your onboarding: '{assignment.workflow.title}'",
            link=f"/onboarding/{assignment.id}"
        )
        self.db.add(notification)
        return note

    def get_assignment_notes(self, assignment_id: int) -> List[dict]:
        """Get all notes for an assignment."""
        notes = self.db.query(OnboardingNote, User).join(
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

    def _check_onboarding_completion(self, onboarding_id: int):
        """Update onboarding status if all tasks are completed. Called within transaction."""
        onboarding = self.db.query(EmployeeOnboardingModel).filter(EmployeeOnboardingModel.id == onboarding_id).first()
        if not onboarding:
            return

        all_completed = all(p.is_completed for p in onboarding.task_progress)
        if all_completed and onboarding.status != "completed":
            onboarding.status = "completed"
            onboarding.completed_at = datetime.utcnow()
        elif not all_completed and onboarding.status == "completed":
            onboarding.status = "in_progress"
            onboarding.completed_at = None

    def get_onboarding_summary(self, user_id: int) -> List[dict]:
        """Get a summary of onboarding progress for a user."""
        onboardings = self.db.query(EmployeeOnboardingModel).options(
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


# ── Backward-compatible module-level functions ──────────────────────

def create_workflow_template(db: Session, workflow_data: OnboardingWorkflowCreate) -> OnboardingWorkflow:
    return OnboardingService(db).create_workflow_template(workflow_data)

def update_template(db: Session, template_id: int, workflow_data: OnboardingWorkflowCreate) -> OnboardingWorkflow:
    return OnboardingService(db).update_template(template_id, workflow_data)

def get_all_templates(db: Session) -> List[OnboardingWorkflow]:
    return OnboardingService(db).get_all_templates()

def delete_template(db: Session, template_id: int) -> None:
    return OnboardingService(db).delete_template(template_id)

def get_all_assignments(db: Session) -> List[dict]:
    return OnboardingService(db).get_all_assignments()

def assign_onboarding(db: Session, assignment_data: EmployeeOnboardingCreate) -> EmployeeOnboardingModel:
    return OnboardingService(db).assign_onboarding(assignment_data)

def get_employee_onboarding(db: Session, user_id: int) -> List[EmployeeOnboardingModel]:
    return OnboardingService(db).get_employee_onboarding(user_id)

def update_task_progress(db: Session, user_id: int, progress_id: int, update_data: EmployeeTaskProgressUpdate) -> EmployeeTaskProgress:
    return OnboardingService(db).update_task_progress(user_id, progress_id, update_data)

def send_reminder(db: Session, assignment_id: int, admin_id: int) -> bool:
    return OnboardingService(db).send_reminder(assignment_id, admin_id)

def add_note(db: Session, assignment_id: int, admin_id: int, note_text: str):
    return OnboardingService(db).add_note(assignment_id, admin_id, note_text)

def get_assignment_notes(db: Session, assignment_id: int):
    return OnboardingService(db).get_assignment_notes(assignment_id)

def check_onboarding_completion(db: Session, onboarding_id: int):
    # Backward compat sets up an isolated transaction context since
    # it used to manage its own commits.
    svc = OnboardingService(db)
    svc._check_onboarding_completion(onboarding_id)
    db.commit()

def get_onboarding_summary(db: Session, user_id: int) -> List[dict]:
    return OnboardingService(db).get_onboarding_summary(user_id)
