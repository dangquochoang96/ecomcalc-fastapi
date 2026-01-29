from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
from app.models.user import User
from app.models.user_platform import UserPlatform as UserPlatformModel
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserPlatform,
    UserPlatformResponse,
)
from app.utils.password import hash_password, verify_password


class UserService:
    """Service layer for user CRUD operations"""

    @staticmethod
    def create_user(db: Session, user: UserCreate) -> UserResponse:
        """Create a new user"""
        # Check if email already exists
        if UserService.get_user_by_email(db, user.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Check if phone already exists
        if UserService.get_user_by_phone(db, user.phone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered",
            )

        # Hash the password properly
        hashed_password = hash_password(user.password)
        db_user = User(
            email=user.email,
            phone=user.phone,
            full_name=user.full_name,
            password_hash=hashed_password,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return UserResponse.model_validate(db_user)

    @staticmethod
    def create_user_platform(
        db: Session, user_platform: UserPlatform
    ) -> UserPlatformResponse:
        """Create a new user platform"""
        db_user_platform = UserPlatformModel(
            platform_id=user_platform.platform_id,
            category_id=user_platform.category_id,
            shop_name=user_platform.shop_name,
            shop_id=user_platform.shop_id,
            is_default=user_platform.is_default,
            tax_profile=user_platform.tax_profile,
        )
        db.add(db_user_platform)
        db.commit()
        db.refresh(db_user_platform)
        return UserPlatformResponse.model_validate(db_user_platform)

    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """Get all users with pagination"""
        users = db.query(User).offset(skip).limit(limit).all()
        return [UserResponse.model_validate(user) for user in users]

    @staticmethod
    def get_user(db: Session, user_id: int) -> Optional[UserResponse]:
        """Get a user by ID"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            return UserResponse.model_validate(db_user)
        return None

    @staticmethod
    def update_user(
        db: Session, user_id: int, user_update: UserUpdate
    ) -> Optional[UserResponse]:
        """Update a user"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return None

        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
        return UserResponse.model_validate(db_user)

    @staticmethod
    def update_user_platform(
        db: Session, user_id: int, user_platform_update: UserPlatform
    ) -> Optional[UserPlatformResponse]:
        """Update a user platform"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return None

        # Check for existing platform entry
        db_platform = (
            db.query(UserPlatformModel)
            .filter(
                UserPlatformModel.user_id == user_id,
                UserPlatformModel.platform_id == user_platform_update.platform_id,
                UserPlatformModel.id == user_platform_update.id,
            )
            .first()
        )

        if not db_platform:
            return None

        # Update fields
        update_data = user_platform_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_platform, field, value)

        db.commit()
        db.refresh(db_platform)
        return UserPlatformResponse.model_validate(db_platform)

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Delete a user"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return False

        db.delete(db_user)
        db.commit()
        return True

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get a user by email"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_phone(db: Session, phone: str) -> Optional[User]:
        """Get a user by phone"""
        return db.query(User).filter(User.phone == phone).first()

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email or phone and password.

        Args:
            db: Database session
            username: Email or phone number
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        # Try to find user by email or phone
        user = (
            db.query(User)
            .filter(or_(User.email == username, User.phone == username))
            .first()
        )

        if not user:
            return None

        # Verify password
        if not verify_password(password, user.password_hash):
            return None

        return user
