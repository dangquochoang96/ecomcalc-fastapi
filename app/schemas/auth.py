from pydantic import BaseModel, Field
from fastapi import status
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Schema for login request - supports both email and phone"""

    username: str = Field(..., description="Email or phone number")
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    """Schema for token response"""

    access_token: str
    token_type: str = "bearer"


class UserPlatformInfo(BaseModel):
    """Schema for user platform information"""

    id: int
    platform_id: int
    shop_name: Optional[str] = None
    shop_id: Optional[str] = None
    is_default: bool = False
    category_id: Optional[int] = None
    tax_profile: Optional[int] = None

    class Config:
        from_attributes = True


class UserInfoResponse(BaseModel):
    """Schema for user information response"""

    id: int
    email: str
    full_name: Optional[str] = None
    phone: str
    preferences: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    platforms: list[UserPlatformInfo] = []

    class Config:
        from_attributes = True


class LoginResponseData(BaseModel):
    """Schema for login response data"""

    access_token: str
    token_type: str = "bearer"
    user: UserInfoResponse


class LoginResponse(BaseModel):
    """Schema for complete login response"""

    code: int = status.HTTP_200_OK
    message: str = "Login successful"
    data: LoginResponseData


class UserProfileResponse(BaseModel):
    """Schema for user profile response"""

    code: int = status.HTTP_200_OK
    message: str = "User profile retrieved successfully"
    data: UserInfoResponse
