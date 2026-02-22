from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repo import UserRepository
from app.schemas.user import Token, UserCreate
from app.models.user import User
from app.config import get_settings

settings = get_settings()


async def register(user_in: UserCreate, db: AsyncSession) -> User:
    """
    Register a new user.

    Args:
        user_in: User creation schema with email, username, and password
        db: Database session

    Returns:
        Created User instance

    Raises:
        HTTPException: 400 if email or username already exists
    """
    user_repo = UserRepository(db)

    # Check if email already exists
    existing_user = await user_repo.get_by_email(user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if username already exists
    existing_user = await user_repo.get_by_username(user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Hash password and create user
    try:
        hashed_pw = hash_password(user_in.password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error hashing password: {str(e)}",
        ) from e
    
    user_data = {
        "email": user_in.email,
        "username": user_in.username,
        "hashed_pw": hashed_pw,
    }
    user = await user_repo.create(user_data)
    await db.commit()
    return user


async def login(email: str, password: str, db: AsyncSession) -> Token:
    """
    Authenticate a user and return JWT token.

    Args:
        email: User email
        password: Plain text password
        db: Database session

    Returns:
        Token with access_token and token_type

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    user_repo = UserRepository(db)

    # Get user by email
    user = await user_repo.get_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not verify_password(password, user.hashed_pw):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(data=token_data, expires_delta=access_token_expires)

    return Token(access_token=access_token, token_type="bearer")
