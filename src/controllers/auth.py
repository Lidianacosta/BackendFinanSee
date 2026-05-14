"""Authentication controller.

Provides the OAuth2 endpoint for generating JWT access tokens.
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.core.config import settings
from src.schemas.auth import Token
from src.services.users import UserServiceDep
from src.utils.security import (
    authenticate_user,
    create_access_token,
)

router = APIRouter(prefix="/auth")


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserServiceDep,
) -> Token:
    """Authenticate a user and return a JWT access token.

    Validates the provided email and password against the database.
    If successful, generates a JWT token valid for the duration
    specified in the application settings.

    Args:
        form_data: OAuth2 password request form containing email and password.
        user_service: Dependency injected user service.

    Returns:
        A Token object containing the JWT string and token type.

    Raises:
        HTTPException: 401 Unauthorized if credentials are invalid.

    """
    user = await authenticate_user(
        form_data.username, form_data.password, user_service
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(
        minutes=settings.access_token_expire_minutes
    )
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
