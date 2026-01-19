from pydantic import BaseModel, Field
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
    
    class Config:
        from_attributes = True


class LoginResponseData(BaseModel):
    """Schema for login response data"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 12960000  # 150 days in seconds
    user: UserInfoResponse


class LoginResponse(BaseModel):
    """Schema for complete login response"""
    status: str = "success"
    code: int = 1
    message: str = "Token Generated"
    data: LoginResponseData


class UserProfileResponse(BaseModel):
    """Schema for user profile response"""
    status: str = "success"
    code: int = 1
    message: str = "Token Generated"
    data: UserInfoResponse
