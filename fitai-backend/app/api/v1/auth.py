import logging

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import get_db
from app.schemas.user import Token, UserCreate, UserResponse
from app.services.auth_service import login, register

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Register a new user.

    Args:
        user_in: User creation data (email, username, password)
        db: Database session

    Returns:
        Created user response (without password)

    Raises:
        HTTPException: 400 if email or username already exists, 500 for other errors
    """
    try:
        user = await register(user_in, db)
        return UserResponse.model_validate(user)
    except HTTPException:
        # Re-raise HTTP exceptions (400, 401, etc.)
        raise
    except SQLAlchemyError as e:
        # Database-related errors
        logger.exception("Database error during user registration")
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {error_msg}. Please ensure migrations are run.",
        ) from e
    except Exception as e:
        # Log unexpected errors for debugging
        logger.exception("Unexpected error during user registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        ) from e


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login_user(
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Authenticate user and return JWT token.

    Args:
        email: User email
        password: User password
        db: Database session

    Returns:
        Token with access_token and token_type

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    return await login(email, password, db)
