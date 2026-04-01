"""Auth routes — API handlers delegating to AuthService."""
import os
import uuid
import shutil
import logging
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Request

from app.core.config import settings
from app.core.rate_limiter import limiter
from app.schemas.auth import (
    UserCreate, UserLogin, Token, UserResponse, ProfileUpdate,
    PasswordChange, ForgotPasswordRequest, ResetPasswordConfirm, OTPVerify
)
from app.services.auth_service import AuthService
from app.core.job_queue import enqueue
from app.core.jobs import job_send_email
from app.utils.dependencies import get_current_user
from app.authorization.dependencies import require
from app.authorization.permissions import Permission
from app.container import get_auth_service
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_create: UserCreate, 
    service: AuthService = Depends(get_auth_service)
):
    """Register a new user."""
    return service.create_user(user_create)


@router.get("/check-username/{username}")
def check_username(
    username: str, 
    service: AuthService = Depends(get_auth_service)
):
    """Check if a username is available."""
    available = service.is_username_available(username)
    return {"available": available}


@router.post("/login", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login(
    request: Request, 
    user_login: UserLogin, 
    service: AuthService = Depends(get_auth_service)
):
    """Login and get access token."""
    user = service.authenticate_user(user_login.username, user_login.password)
    tokens = service.create_tokens_for_user(user)
    logger.info(f"User {user.username} logged in successfully")
    return tokens


@router.get(
    "/me",
    response_model=UserResponse,
    dependencies=[Depends(get_current_user)]
)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service)
):
    """Update current user's profile information."""
    return service.update_user_profile(
        user=current_user,
        email=profile_data.email,
        username=profile_data.username,
        full_name=profile_data.full_name,
        timezone=profile_data.timezone
    )


@router.put("/password", response_model=UserResponse)
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service)
):
    """Change current user's password."""
    return service.change_user_password(
        user=current_user,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )


@router.post("/upload-avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service)
):
    """Upload a profile picture for the current user."""
    upload_dir = "uploads/avatars"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not allowed. Please upload a JPEG, PNG or WebP image."
        )

    file_extension = os.path.splitext(file.filename)[1]
    if not file_extension:
        file_extension = ".jpg"

    filename = f"{current_user.id}_{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    avatar_url = f"/static/avatars/{filename}"
    return service.update_user_profile(user=current_user, avatar_url=avatar_url)


@router.post("/forgot-password")
@limiter.limit(settings.RATE_LIMIT_OTP)
def forgot_password(
    forgot_request: ForgotPasswordRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service)
):
    """Request a password reset via OTP."""
    otp = service.create_reset_token(forgot_request.email)
    if otp:
        subject = "Your Password Reset OTP"
        message = f"Your 6-digit verification code is: {otp}\n\nThis code is valid for 10 minutes."
        enqueue(job_send_email, forgot_request.email, subject, message)
    return {"message": "If an account exists with this email, a 6-digit code has been sent."}


@router.post("/verify-otp")
@limiter.limit(settings.RATE_LIMIT_OTP)
def verify_otp_endpoint(
    request: Request, 
    otp_data: OTPVerify, 
    service: AuthService = Depends(get_auth_service)
):
    """Verify the 6-digit OTP."""
    is_valid = service.verify_otp(otp_data.email, otp_data.otp)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    return {"message": "Verification successful."}


@router.post("/reset-password")
def reset_password_confirm(
    request: ResetPasswordConfirm, 
    service: AuthService = Depends(get_auth_service)
):
    """Complete password reset using the 6-digit code (token)."""
    success = service.reset_password_with_token(request.token, request.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    return {"message": "Password has been reset successfully."}
