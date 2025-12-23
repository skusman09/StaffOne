from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from app.models.user import Role


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: Role
    is_active: bool
    timezone: str
    avatar_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token data."""
    user_id: Optional[int] = None
    username: Optional[str] = None


class RoleUpdate(BaseModel):
    """Schema for updating user role."""
    role: Role


class ProfileUpdate(BaseModel):
    """Schema for updating user profile."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    timezone: Optional[str] = None
    avatar_url: Optional[str] = None


class PasswordChange(BaseModel):
    """Schema for changing password."""
    current_password: str
    new_password: str