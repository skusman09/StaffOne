from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class OnboardingWorkflow(Base):
    """Template for an onboarding workflow (e.g., 'Engineering Onboarding')."""
    __tablename__ = "onboarding_workflows"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tasks = relationship("OnboardingTask", back_populates="workflow", cascade="all, delete-orphan")
    employee_onboardings = relationship("EmployeeOnboarding", back_populates="workflow")


class OnboardingTask(Base):
    """Template for a task within a workflow."""
    __tablename__ = "onboarding_tasks"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("onboarding_workflows.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, default=0)  # Sequence of tasks
    is_required = Column(Boolean, default=True)

    # Relationships
    workflow = relationship("OnboardingWorkflow", back_populates="tasks")


class EmployeeOnboarding(Base):
    """An instance of a workflow assigned to a specific employee."""
    __tablename__ = "employee_onboardings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workflow_id = Column(Integer, ForeignKey("onboarding_workflows.id"), nullable=False)
    status = Column(String, default="in_progress")  # in_progress, completed, overdue
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User")
    workflow = relationship("OnboardingWorkflow", back_populates="employee_onboardings")
    task_progress = relationship("EmployeeTaskProgress", back_populates="onboarding", cascade="all, delete-orphan")
    notes = relationship("OnboardingNote", back_populates="assignment", cascade="all, delete-orphan")


class EmployeeTaskProgress(Base):
    """The status of a specific task for a specific employee."""
    __tablename__ = "employee_task_progress"

    id = Column(Integer, primary_key=True, index=True)
    employee_onboarding_id = Column(Integer, ForeignKey("employee_onboardings.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("onboarding_tasks.id"), nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    onboarding = relationship("EmployeeOnboarding", back_populates="task_progress")
    task = relationship("OnboardingTask")


class OnboardingNote(Base):
    """Admin notes for employee onboarding progress."""
    __tablename__ = "onboarding_notes"

    id = Column(Integer, primary_key=True, index=True)
    employee_onboarding_id = Column(Integer, ForeignKey("employee_onboardings.id"), nullable=False)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignment = relationship("EmployeeOnboarding", back_populates="notes")
    admin = relationship("User", foreign_keys=[admin_id])
