"""
Authentication service — business logic for user registration, login, profile, and password management.

Architecture:
- Accepts IUserRepository via constructor (Dependency Inversion)
- Uses @transactional for consistent commit/rollback
- Pure orchestration: load data → validate → persist
"""
import logging
import secrets
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, Role
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.core.config import settings
from app.core.transaction import transactional
from app.schemas.auth import UserCreate
from app.interfaces.repositories import IUserRepository
from app.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    """Handles all authentication and user management business logic."""

    def __init__(self, db: Session, user_repo: IUserRepository = None):
        self.db = db
        self.user_repo = user_repo or UserRepository(db)

    # ── Registration & Login ────────────────────────────────────────────

    @transactional
    def create_user(self, user_create: UserCreate) -> User:
        """Register a new user with validation."""
        existing = self.user_repo.email_or_username_exists(
            user_create.email, user_create.username
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already registered"
            )

        hashed_password = get_password_hash(user_create.password)
        db_user = User(
            email=user_create.email,
            username=user_create.username,
            hashed_password=hashed_password,
            full_name=user_create.full_name,
            role=Role.EMPLOYEE
        )

        self.user_repo.add(db_user)
        self.db.flush()
        self.db.refresh(db_user)
        return db_user

    def is_username_available(self, username: str) -> bool:
        """Check if a username is available."""
        return self.user_repo.get_by_username(username) is None

    def authenticate_user(self, username: str, password: str) -> User:
        """Authenticate a user by username and password."""
        user = self.user_repo.get_by_username(username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        return user

    @staticmethod
    def create_tokens_for_user(user: User) -> dict:
        """Create access and refresh tokens for a user."""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "user_id": user.id, "username": user.username},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "user_id": user.id, "username": user.username}
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    # ── Profile Management ──────────────────────────────────────────────

    @transactional
    def update_user_profile(
        self, user: User,
        email: str = None, username: str = None,
        full_name: str = None, timezone: str = None,
        avatar_url: str = None
    ) -> User:
        """Update user profile information."""
        if email and email != user.email:
            existing = self.user_repo.get_by_email(email)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            user.email = email

        if username and username != user.username:
            existing = self.user_repo.get_by_username(username)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            user.username = username

        if full_name is not None:
            user.full_name = full_name

        if timezone is not None:
            user.timezone = timezone

        if avatar_url is not None:
            user.avatar_url = avatar_url

        self.db.flush()
        self.db.refresh(user)
        return user

    # ── Password Management ─────────────────────────────────────────────

    @transactional
    def change_user_password(self, user: User, current_password: str, new_password: str) -> User:
        """Change user password after verifying current password."""
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        if len(new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 6 characters"
            )

        user.hashed_password = get_password_hash(new_password)
        self.db.flush()
        self.db.refresh(user)
        return user

    @transactional
    def create_reset_token(self, email: str) -> Optional[str]:
        """Generate and store a 6-digit OTP for password reset."""
        user = self.user_repo.get_by_email(email)
        if not user:
            return None

        otp = ''.join([secrets.choice('0123456789') for _ in range(6)])
        user.reset_token = otp
        user.reset_token_expires = datetime.utcnow() + timedelta(minutes=10)
        return otp

    def verify_otp(self, email: str, otp: str) -> bool:
        """Verify if the OTP is valid for the given email."""
        user = self.user_repo.get_by_email_and_otp(email, otp)
        return user is not None

    @transactional
    def reset_password_with_token(self, token: str, new_password: str) -> bool:
        """Reset user password using a valid reset token."""
        user = self.user_repo.get_by_reset_token(token)

        if not user:
            return False

        if verify_password(new_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password cannot be the same as your old password"
            )

        user.hashed_password = get_password_hash(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        return True




# ── DI Factory ──────────────────────────────────────────────────────

def get_auth_service(db: Session) -> AuthService:
    """Factory for FastAPI Depends() injection."""
    return AuthService(db)

