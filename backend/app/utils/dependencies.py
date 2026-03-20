from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User, Role
from app.core.security import decode_token
from app.services.auth_service import authenticate_user, create_tokens_for_user

security = HTTPBearer(auto_error=False)  # Make Bearer optional
http_basic = HTTPBasic(auto_error=False)  # Make Basic Auth optional


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    basic_credentials: Optional[HTTPBasicCredentials] = Security(http_basic),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user.
    Supports both Bearer token and HTTP Basic Auth (username/password).
    """
    # Try Bearer token first
    if credentials:
        import logging
        logger = logging.getLogger(__name__)
        
        token = credentials.credentials
        logger.debug(f"Received Bearer token, length: {len(token)}")
        
        payload = decode_token(token)
        
        if payload is None:
            logger.warning("Token decode returned None - check backend logs for JWT decode error")
            # Fall through to Basic Auth if available
            if basic_credentials:
                logger.debug("Falling back to Basic Auth")
                try:
                    user = authenticate_user(db, basic_credentials.username, basic_credentials.password)
                    return user
                except HTTPException:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication credentials",
                        headers={"WWW-Authenticate": "Bearer, Basic"},
                    )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials - token decode failed",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials - wrong token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user_id from payload (sub is string, user_id is int)
        user_id = payload.get("user_id") or payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials - missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Convert to int if it's a string
        if isinstance(user_id, str):
            try:
                user_id = int(user_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials - invalid user ID format",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        return user
    
    # Fall back to Basic Auth
    if basic_credentials:
        try:
            user = authenticate_user(db, basic_credentials.username, basic_credentials.password)
            return user
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Basic"},
            )
    
    # No authentication provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer, Basic"},
    )


def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to get current admin user."""
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def require_role(required_role: Role):
    """Dependency factory to require a specific role."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role.value} role"
            )
        return current_user
    return role_checker



