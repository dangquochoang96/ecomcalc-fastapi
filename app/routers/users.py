from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
    UserPlatform,
    UserPlatformResponse,
)
from app.services.user import UserService
from app.dependencies import get_current_user, get_db

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    return UserService.create_user(db, user)


@router.post("/platform", response_model=UserPlatformResponse)
def create_user_platform(
    user_platform: UserPlatform,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new user platform"""
    return UserService.create_user_platform(db, user_platform, user_id=current_user.id)


@router.get("/", response_model=List[UserResponse])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all users with pagination"""
    return UserService.get_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID"""
    user = UserService.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update a user"""
    user = UserService.update_user(db, user_id, user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.put("/{user_id}/platform", response_model=UserPlatformResponse)
def update_user_platform(
    user_id: int,
    user_platform_update: UserPlatform,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update a user platform"""
    platform_data = UserService.update_user_platform(db, user_id, user_platform_update)
    if not platform_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return platform_data


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a user"""
    success = UserService.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
