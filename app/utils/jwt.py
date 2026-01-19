from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import os
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "B8HHhdZ7xDeqM3fGFSD7Oude0cjuF4NrxV2F6fmfKxM")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "43200"))  # 30 days default


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing user data to encode in token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string to verify
        
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_user_from_token(token: str) -> Optional[int]:
    """
    Extract user ID from JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        User ID if token is valid, None otherwise
    """
    payload = verify_token(token)
    if payload is None:
        return None
    
    user_id: Optional[int] = payload.get("sub")
    return user_id
