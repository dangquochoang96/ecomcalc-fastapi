from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel


class PlatformFeeBase(BaseModel):
    fee_name: str
    fee_code: str
    fee_type: int
    default_value: Decimal
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    is_mandatory: Optional[bool] = False
    sort_order: Optional[int] = 0
    # is_active: Optional[bool] = True


class PlatformFeeResponse(PlatformFeeBase):
    id: int
    platform_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PlatformBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool


class PlatformResponse(PlatformBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ApiResponse(BaseModel):
    success: bool
    data: List[PlatformFeeResponse]
    message: Optional[str] = None
