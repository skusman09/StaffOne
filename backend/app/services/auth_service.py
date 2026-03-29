from sqlalchemy.orm import Session
from typing import Optional
from fastapi import HTTPException, status
from app.models.user import User, Role
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.schemas.auth import UserCreate, UserLogin
from datetime import timedelta
from app.core.config import settings


def create_user(db: Session, user_create: UserCreate) -> User:
    """Create a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_create.email) | (User.username == user_create.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_create.password)
    db_user = User(
        email=user_create.email,
        username=user_create.username,
        hashed_password=hashed_password,
        full_name=user_create.full_name,
        role=Role.EMPLOYEE
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def is_username_available(db: Session, username: str) -> bool:
    """Check if a username is available."""
    user = db.query(User).filter(User.username == username).first()
    return user is None


def authenticate_user(db: Session, username: str, password: str) -> User:
    """Authenticate a user and return user object."""
    user = db.query(User).filter(User.username == username).first()
    
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


def create_tokens_for_user(user: User) -> dict:
    """Create access and refresh tokens for a user."""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Convert user.id to string for JWT 'sub' claim (some JWT libraries require string)
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


def update_user_profile(db: Session, user: User, email: str = None, username: str = None, 
                        full_name: str = None, timezone: str = None, avatar_url: str = None) -> User:
    """Update user profile information."""
    # Check if new email is already taken
    if email and email != user.email:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        user.email = email
    
    # Check if new username is already taken
    if username and username != user.username:
        existing = db.query(User).filter(User.username == username).first()
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
    
    db.commit()
    db.refresh(user)
    return user


def change_user_password(db: Session, user: User, current_password: str, new_password: str) -> User:
    """Change user password after verifying current password."""
    # Verify current password
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters"
        )
    
    # Update password
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user


def create_reset_token(db: Session, email: str) -> Optional[str]:
    """Generate and store a password reset token for a user."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    
    import secrets
    from datetime import datetime, timedelta
    
    # Generate a 6-digit numeric OTP
    otp = ''.join([secrets.choice('0123456789') for _ in range(6)])
    user.reset_token = otp
    user.reset_token_expires = datetime.utcnow() + timedelta(minutes=10) # OTP valid for 10 mins
    
    db.commit()
    return otp


def reset_password_with_token(db: Session, token: str, new_password: str) -> bool:
    """Reset user password using a valid reset token."""
    from datetime import datetime
    
    user = db.query(User).filter(
        User.reset_token == token,
        User.reset_token_expires > datetime.utcnow()
    ).first()
    
    if not user:
        return False
    
    # Update password and clear token
    # Check if new password is same as old password
    if verify_password(new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as your old password"
        )
        
    user.hashed_password = get_password_hash(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    
    db.commit()
    return True


def verify_otp(db: Session, email: str, otp: str) -> bool:
    """Verify if the OTP is valid for the given email."""
    from datetime import datetime
    
    user = db.query(User).filter(
        User.email == email,
        User.reset_token == otp,
        User.reset_token_expires > datetime.utcnow()
    ).first()
    
    return user is not None
