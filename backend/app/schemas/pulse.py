from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class PulseResponseBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class PulseResponseCreate(PulseResponseBase):
    survey_id: int


class UserPulseResponse(BaseModel):
    username: str
    email: str

    class Config:
        from_attributes = True


class PulseResponse(PulseResponseBase):
    id: int
    survey_id: int
    user_id: int
    created_at: datetime
    user: Optional[UserPulseResponse] = None

    class Config:
        from_attributes = True


class PulseSurveyBase(BaseModel):
    question: str


class PulseSurveyCreate(PulseSurveyBase):
    pass


class PulseSurveyUpdate(BaseModel):
    question: Optional[str] = None
    is_active: Optional[bool] = None


class PulseSurvey(PulseSurveyBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PulseSurveyWithStats(PulseSurvey):
    response_count: int
    average_rating: float
    responses: List[PulseResponse] = []
