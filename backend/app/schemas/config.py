from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


class SystemConfigBase(BaseModel):
    """Base schema for system config."""
    key: str
    value: str
    description: Optional[str] = None
    value_type: Literal["string", "int", "float", "bool"] = "string"


class SystemConfigCreate(SystemConfigBase):
    """Schema for creating a system config."""
    pass


class SystemConfigUpdate(BaseModel):
    """Schema for updating a system config."""
    value: str
    description: Optional[str] = None


class SystemConfigResponse(SystemConfigBase):
    """Response schema for system config."""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SystemConfigListResponse(BaseModel):
    """Response schema for listing system configs."""
    configs: list[SystemConfigResponse]
    total: int
