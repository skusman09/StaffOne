from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum
from app.schemas.auth import UserResponse


class CompOffStatusEnum(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    USED = "used"


class CompOffCreate(BaseModel):
    ot_start_date: datetime
    ot_end_date: datetime
    reason: Optional[str] = None


class CompOffResponse(BaseModel):
    id: int
    user_id: int
    ot_hours: float
    comp_off_days: float
    ot_start_date: datetime
    ot_end_date: datetime
    status: CompOffStatusEnum
    request_date: datetime
    reason: Optional[str] = None
    admin_remarks: Optional[str] = None
    review_date: Optional[datetime] = None
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class CompOffReview(BaseModel):
    status: CompOffStatusEnum
    admin_remarks: Optional[str] = None


class CompOffListResponse(BaseModel):
    comp_offs: List[CompOffResponse]
    total: int
