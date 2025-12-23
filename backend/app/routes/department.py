from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.department import Department
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentListResponse
from app.utils.dependencies import get_current_admin_user

router = APIRouter(prefix="/departments", tags=["departments"])


@router.post("/", response_model=DepartmentResponse, status_code=201)
def create_department(
    dept: DepartmentCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new department. Admin only."""
    # Check if name already exists
    existing = db.query(Department).filter(Department.name == dept.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department with this name already exists")
    
    new_dept = Department(
        name=dept.name,
        description=dept.description,
        manager_id=dept.manager_id
    )
    db.add(new_dept)
    db.commit()
    db.refresh(new_dept)
    return new_dept


@router.get("/", response_model=DepartmentListResponse)
def list_departments(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all departments. Admin only."""
    departments = db.query(Department).all()
    return DepartmentListResponse(
        departments=departments,
        total=len(departments)
    )


@router.get("/{dept_id}", response_model=DepartmentResponse)
def get_department(
    dept_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get department details. Admin only."""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept


@router.put("/{dept_id}", response_model=DepartmentResponse)
def update_department(
    dept_id: int,
    dept_update: DepartmentUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update department. Admin only."""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    if dept_update.name is not None:
        # Check if name already exists for other department
        existing = db.query(Department).filter(
            Department.name == dept_update.name, 
            Department.id != dept_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Department with this name already exists")
        dept.name = dept_update.name
    
    if dept_update.description is not None:
        dept.description = dept_update.description
    
    if dept_update.manager_id is not None:
        # Verify manager exists
        if dept_update.manager_id:
            manager = db.query(User).filter(User.id == dept_update.manager_id).first()
            if not manager:
                raise HTTPException(status_code=404, detail="Manager user not found")
        dept.manager_id = dept_update.manager_id
        
    db.commit()
    db.refresh(dept)
    return dept


@router.delete("/{dept_id}")
def delete_department(
    dept_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete department. Admin only."""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Check if users are assigned to this department
    has_users = db.query(User).filter(User.department_id == dept_id).first()
    if has_users:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete department with assigned users. Move users first."
        )
        
    db.delete(dept)
    db.commit()
    return {"message": "Department deleted successfully"}
