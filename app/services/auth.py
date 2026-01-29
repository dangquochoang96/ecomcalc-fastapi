from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Response
from app.models.user import User
from app.models.user_platform import UserPlatform
from app.schemas.auth import (
    TokenResponse,
    UserInfoResponse,
    LoginResponseData,
    LoginResponse,
)
from app.schemas.user import UserCreate
from app.services.user import UserService
from app.utils.jwt import create_access_token, create_refresh_token


class AuthService:
    """Service layer for authentication operations"""

    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> TokenResponse:
        """
        Register a new user and return access token.

        Args:
            db: Database session
            user_data: User registration data

        Returns:
            TokenResponse with access token

        Raises:
            HTTPException: If email or phone already exists
        """
        # Create new user using UserService (handles validation and hashing)
        user_response = UserService.create_user(db, user_data)

        # Get the underlying database object for token creation
        # In a real scenario you might want to adjust UserService to return the model or work with the schema
        # For now we query it back or assume ID is consistent
        db_user = db.query(User).filter(User.id == user_response.id).first()

        # Create access token
        access_token = create_access_token(data={"sub": str(db_user.id)})

        # Create user info response
        user_info = UserInfoResponse(
            id=db_user.id,
            email=db_user.email,
            full_name=db_user.full_name,
            phone=db_user.phone,
            preferences=None,
            created_at=getattr(db_user, "created_at", None),
            updated_at=getattr(db_user, "updated_at", None),
            is_active=db_user.is_active,
        )

        # Create response data
        response_data = LoginResponseData(
            access_token=access_token,
            token_type="bearer",
            expires_in=12960000,  # 150 days in seconds
            user=user_info,
        )

        return LoginResponse(data=response_data)

    @staticmethod
    def login_user(
        response: Response, db: Session, username: str, password: str
    ) -> LoginResponse:
        """
        Authenticate user and return access token.

        Args:
            response: HTTP response object
            db: Database session
            username: Email or phone number
            password: Plain text password

        Returns:
            LoginResponse with complete response format

        Raises:
            HTTPException: If credentials are invalid
        """
        user = UserService.authenticate_user(db, username, password)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email/phone or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
            )

        # Create access token

        access_token = create_access_token(data={"sub": str(user.id)})

        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,  # 30 days
        )

        # Create user info response
        user_info = UserInfoResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            preferences=None,
            created_at=getattr(user, "created_at", None),
            updated_at=getattr(user, "updated_at", None),
            is_active=user.is_active,
            platforms=user.user_platforms if hasattr(user, "user_platforms") else [],
        )

        # Create response data
        response_data = LoginResponseData(
            access_token=access_token, token_type="bearer", user=user_info
        )

        return LoginResponse(data=response_data)

    @staticmethod
    def get_current_user_info(db: Session, user_id: int) -> UserInfoResponse:
        """
        Get current user information.

        Args:
            db: Database session
            user_id: User ID from token

        Returns:
            UserInfoResponse with user data

        Raises:
            HTTPException: If user not found
        """
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        platforms = db.query(UserPlatform).filter(UserPlatform.user_id == user_id).all()

        return UserInfoResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            preferences=None,
            created_at=getattr(user, "created_at", None),
            updated_at=getattr(user, "updated_at", None),
            is_active=user.is_active,
            platforms=platforms,
        )
