from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# --- Task Schemas ---
class OnboardingTaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    order: int = 0
    is_required: bool = True


class OnboardingTaskCreate(OnboardingTaskBase):
    pass


class OnboardingTask(OnboardingTaskBase):
    id: int
    workflow_id: int

    class Config:
        from_attributes = True


# --- Workflow Schemas ---
class OnboardingWorkflowBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_active: bool = True


class OnboardingWorkflowCreate(OnboardingWorkflowBase):
    tasks: List[OnboardingTaskCreate] = []


class OnboardingWorkflow(OnboardingWorkflowBase):
    id: int
    created_at: datetime
    updated_at: datetime
    tasks: List[OnboardingTask] = []

    class Config:
        from_attributes = True


# --- Progress Schemas ---
class EmployeeTaskProgressBase(BaseModel):
    is_completed: bool = False
    notes: Optional[str] = None


class EmployeeTaskProgressUpdate(EmployeeTaskProgressBase):
    pass


class EmployeeTaskProgress(EmployeeTaskProgressBase):
    id: int
    employee_onboarding_id: int
    task_id: int
    completed_at: Optional[datetime] = None
    task: OnboardingTask

    class Config:
        from_attributes = True


class EmployeeOnboardingBase(BaseModel):
    status: str = "in_progress"


class EmployeeOnboardingCreate(EmployeeOnboardingBase):
    user_id: int
    workflow_id: int


class EmployeeOnboarding(EmployeeOnboardingBase):
    id: int
    user_id: int
    workflow_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    workflow: OnboardingWorkflow
    task_progress: List[EmployeeTaskProgress] = []

    class Config:
        from_attributes = True


class EmployeeOnboardingSummary(BaseModel):
    id: int
    workflow_title: str
    status: str
    progress_percentage: float
    tasks_total: int
    tasks_completed: int
    started_at: datetime
