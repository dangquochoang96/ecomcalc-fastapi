from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserProfileResponse,
)
from app.schemas.user import UserCreate
from app.services.auth import AuthService
from app.dependencies import get_db, get_current_user
from app.models.user import User

router = APIRouter()


@router.post(
    "/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED
)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    - **email**: Valid email address (must be unique)
    - **phone**: Phone number (must be unique)
    - **full_name**: Optional full name
    - **password**: Password (minimum 8 characters)

    Returns complete response with access token and user info upon successful registration.
    """
    return AuthService.register_user(db, user_data)


@router.post("/login", response_model=LoginResponse)
def login(response: Response, login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with email or phone and password.

    - **username**: Email or phone number
    - **password**: User password

    Returns complete response with access token and user info upon successful authentication.
    """
    return AuthService.login_user(
        response, db, login_data.username, login_data.password
    )


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """
    Logout endpoint.

    Note: Since JWT is stateless, the actual logout is handled on the client side
    by removing the token. This endpoint is provided for consistency and can be
    extended with token blacklisting if needed.
    """
    return {
        "message": "Successfully logged out. Please remove the token from client storage."
    }


@router.get("/user-profile", response_model=UserProfileResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get current authenticated user information.

    Requires valid authentication token in Authorization header.
    Returns complete user profile information in standard response format.
    """
    user_info = AuthService.get_current_user_info(db, current_user.id)
    return UserProfileResponse(data=user_info)
