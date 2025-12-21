from sqlalchemy.orm import Session
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

