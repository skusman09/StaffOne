"""
User repository — all User-related database queries.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.user import User, Role
from app.repositories import BaseRepository


class UserRepository(BaseRepository):
    """Data access layer for User model."""

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()

    def email_or_username_exists(self, email: str, username: str) -> Optional[User]:
        """Check if a user with the given email or username already exists."""
        return self.db.query(User).filter(
            or_(User.email == email, User.username == username)
        ).first()

    def get_by_reset_token(self, token: str) -> Optional[User]:
        """Get user by valid (non-expired) reset token."""
        return self.db.query(User).filter(
            User.reset_token == token,
            User.reset_token_expires > datetime.utcnow()
        ).first()

    def get_by_email_and_otp(self, email: str, otp: str) -> Optional[User]:
        """Get user matching email and valid OTP."""
        return self.db.query(User).filter(
            User.email == email,
            User.reset_token == otp,
            User.reset_token_expires > datetime.utcnow()
        ).first()

    def get_active_users(self) -> List[User]:
        """Get all active users."""
        return self.db.query(User).filter(User.is_active == True).all()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get paginated list of users."""
        return self.db.query(User).offset(skip).limit(limit).all()
