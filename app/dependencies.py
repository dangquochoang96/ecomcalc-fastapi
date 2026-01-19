from typing import Optional
from fastapi import Header, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.utils.jwt import get_user_from_token
from app.models.user import User

# Define security scheme for JWT
security = HTTPBearer()


async def get_token_header(x_token: Optional[str] = Header(None)):
    """
    Dependency to validate token from header.
    Modify this according to your authentication requirements.
    """
    if x_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Token header missing"
        )
    # Add your token validation logic here
    return x_token


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current user from JWT token.
    
    Args:
        credentials: HTTP Authorization credentials containing the JWT token
        db: Database session
        
    Returns:
        User object if authenticated
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    # Get user ID from token
    user_id = get_user_from_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user
