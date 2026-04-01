"""
Base repository providing common data access operations.

Design rules:
- Repositories use flush() only — never commit()
- Services own transaction boundaries (commit/rollback)
- Routes never touch db.commit()
"""
from typing import TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from app.database import Base

T = TypeVar("T", bound=Base)


class BaseRepository:
    """Simple base repository with common CRUD helpers.
    
    Subclasses inherit these and add domain-specific query methods.
    Repositories only flush — services control commits.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, model_class: Type[T], id: int) -> Optional[T]:
        """Get a record by its primary key."""
        return self.db.query(model_class).filter(model_class.id == id).first()

    def add(self, obj) -> None:
        """Add an object to the session (flush, not commit)."""
        self.db.add(obj)
        self.db.flush()

    def delete(self, obj) -> None:
        """Delete an object (flush, not commit)."""
        self.db.delete(obj)
        self.db.flush()

    def commit(self) -> None:
        """Commit the current transaction."""
        self.db.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.db.rollback()

    def refresh(self, obj) -> None:
        """Refresh an object from the database."""
        self.db.refresh(obj)
