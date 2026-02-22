from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

# Configure CryptContext for bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        plain: Plain text password

    Returns:
        Hashed password string
    """
    # Bcrypt has a 72-byte limit, always truncate to 71 bytes to be safe
    # Convert to bytes, truncate, then back to string
    password_bytes = plain.encode('utf-8')
    if len(password_bytes) > 71:
        password_bytes = password_bytes[:71]
    password_str = password_bytes.decode('utf-8', errors='ignore')
    
    return pwd_context.hash(password_str)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain text password against a hashed password.

    Args:
        plain: Plain text password
        hashed: Hashed password string

    Returns:
        True if password matches, False otherwise
    """
    # Bcrypt has a 72-byte limit, truncate if necessary (same as hash_password)
    password_bytes = plain.encode('utf-8')
    if len(password_bytes) > 71:
        password_bytes = password_bytes[:71]
    password_str = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.verify(password_str, hashed)


def create_access_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of data to encode in the token
        expires_delta: Token expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload dictionary or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None
