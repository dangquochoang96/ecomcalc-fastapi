import re
from typing import Optional


def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if email is valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone_number(phone: str, country_code: str = "VN") -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number to validate
        country_code: Country code for validation rules
        
    Returns:
        bool: True if phone number is valid
    """
    # Example for Vietnamese phone numbers
    if country_code == "VN":
        pattern = r'^(0|\+84)[0-9]{9}$'
        return bool(re.match(pattern, phone))
    
    # Add more country-specific validations as needed
    return True


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength
    
    Args:
        password: Password to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, None


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS attacks
    
    Args:
        text: Input text to sanitize
        
    Returns:
        str: Sanitized text
    """
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&']
    sanitized = text
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    return sanitized.strip()
