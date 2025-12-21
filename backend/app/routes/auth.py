from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import UserCreate, UserLogin, Token, UserResponse
from app.services.auth_service import create_user, authenticate_user, create_tokens_for_user
from app.utils.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    user = create_user(db, user_create)
    return user


@router.post("/login", response_model=Token)
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    """Login and get access token."""
    import logging
    logger = logging.getLogger(__name__)
    
    user = authenticate_user(db, user_login.username, user_login.password)
    tokens = create_tokens_for_user(user)
    
    # Verify token decode immediately after creation (for debugging)
    from app.core.security import decode_token
    test_payload = decode_token(tokens["access_token"])
    if test_payload:
        logger.info(f"Token created successfully for user {user.username}")
    else:
        logger.warning("Token decode failed immediately after creation - this may indicate a configuration issue")
    
    return tokens


@router.get(
    "/me", 
    response_model=UserResponse,
    dependencies=[Depends(get_current_user)]
)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information.
    
    Supports both Bearer token and HTTP Basic Auth (username/password).
    For Swagger UI, click "Authorize" and use Bearer token (get it from /auth/login).
    """
    return current_user

