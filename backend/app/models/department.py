from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Department(Base):
    """Department model for organizational grouping.
    
    Allows filtering users, attendance, and payroll by department.
    """
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Manager of the department (optional)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    manager = relationship("User", foreign_keys=[manager_id], backref="managed_departments")
    users = relationship("User", foreign_keys="[User.department_id]", back_populates="department")

    def __repr__(self):
        return f"<Department {self.name}>"
