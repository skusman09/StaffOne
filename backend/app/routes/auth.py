from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
import os
import uuid
import shutil
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import UserCreate, UserLogin, Token, UserResponse, ProfileUpdate, PasswordChange, ForgotPasswordRequest, ResetPasswordConfirm, OTPVerify
from app.services.auth_service import create_user, authenticate_user, create_tokens_for_user, update_user_profile, change_user_password
from app.utils.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    user = create_user(db, user_create)
    return user


@router.get("/check-username/{username}")
def check_username(username: str, db: Session = Depends(get_db)):
    """Check if a username is available."""
    from app.services.auth_service import is_username_available
    available = is_username_available(db, username)
    return {"available": available}


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


@router.put("/profile", response_model=UserResponse)
def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile information."""
    return update_user_profile(
        db=db,
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
    db: Session = Depends(get_db)
):
    """Change current user's password."""
    return change_user_password(
        db=db,
        user=current_user,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )


@router.post("/upload-avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a profile picture for the current user."""
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads/avatars"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not allowed. Please upload a JPEG, PNG or WebP image."
        )
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    if not file_extension:
        file_extension = ".jpg" # Fallback
    
    filename = f"{current_user.id}_{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(upload_dir, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update user in database
    # Construct URL (assuming server runs locally or base URL is known)
    # We'll store a relative URL /api/static/avatars/filename
    avatar_url = f"/static/avatars/{filename}"
    
    from app.services.auth_service import update_user_profile
    return update_user_profile(
        db=db,
        user=current_user,
        avatar_url=avatar_url
    )


@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request a password reset via OTP."""
    from app.services.auth_service import create_reset_token
    from app.services.notification_service import send_email
    
    otp = create_reset_token(db, request.email)
    if otp:
        subject = "Your Password Reset OTP"
        message = f"Your 6-digit verification code is: {otp}\n\nThis code is valid for 10 minutes. Do not share it with anyone."
        
        send_email(request.email, subject, message)
    
    # Always return success to avoid email enumeration
    return {"message": "If an account exists with this email, a 6-digit code has been sent."}


@router.post("/verify-otp")
def verify_otp_endpoint(request: OTPVerify, db: Session = Depends(get_db)):
    """Verify the 6-digit OTP."""
    from app.services.auth_service import verify_otp
    
    is_valid = verify_otp(db, request.email, request.otp)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    
    return {"message": "Verification successful."}


@router.post("/reset-password")
def reset_password_confirm(request: ResetPasswordConfirm, db: Session = Depends(get_db)):
    """Complete password reset using the 6-digit code (token)."""
    from app.services.auth_service import reset_password_with_token
    
    success = reset_password_with_token(db, request.token, request.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    
    return {"message": "Password has been reset successfully."}
