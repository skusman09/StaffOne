from pydantic import BaseModel
from typing import Optional, List


class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    manager_id: Optional[int] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    manager_id: Optional[int] = None


class DepartmentResponse(DepartmentBase):
    id: int

    class Config:
        from_attributes = True


class DepartmentListResponse(BaseModel):
    departments: List[DepartmentResponse]
    total: int
