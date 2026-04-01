"""
Authentication dependencies for FastAPI routes.

Provides get_current_user — the foundational auth dependency used by
both direct route injection and the PBAC require() layer.
"""
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.core.security import decode_token

security = HTTPBearer(auto_error=False)
http_basic = HTTPBasic(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    basic_credentials: Optional[HTTPBasicCredentials] = Security(http_basic),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user.
    Supports both Bearer token and HTTP Basic Auth (username/password).
    """
    import logging
    logger = logging.getLogger(__name__)

    # Try Bearer token first
    if credentials:
        token = credentials.credentials
        payload = decode_token(token)

        if payload is None:
            # Fall through to Basic Auth if available
            if basic_credentials:
                return _authenticate_basic(db, basic_credentials)
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

        user_id = payload.get("user_id") or payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials - missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )

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
        return _authenticate_basic(db, basic_credentials)

    # No authentication provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer, Basic"},
    )


def _authenticate_basic(db: Session, creds: HTTPBasicCredentials) -> User:
    """Authenticate via username/password using AuthService directly."""
    from app.services.auth_service import AuthService
    try:
        return AuthService(db=db).authenticate_user(creds.username, creds.password)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
