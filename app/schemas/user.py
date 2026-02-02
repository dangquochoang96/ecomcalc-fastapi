from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr
    phone: str = Field(..., min_length=3, max_length=15)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user"""

    phone: str = Field(..., min_length=3, max_length=10)
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema for updating a user"""

    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=3, max_length=15)
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class UserPlatform(BaseModel):
    """Schema for user platform"""

    id: Optional[int] = None
    platform_id: int
    category_id: Optional[int] = None
    shop_name: Optional[str] = None
    shop_id: Optional[str] = None
    tax_profile: Optional[int] = None
    is_default: Optional[bool] = True


class UserPlatformResponse(UserPlatform):
    """Schema for user platform response"""

    id: int
    user_id: int
    platform_id: int
    category_id: Optional[int] = None
    shop_name: Optional[str] = None
    tax_profile: Optional[int] = None

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """Schema for user response"""

    id: int
    is_active: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
