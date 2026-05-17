"""Authentication controller.

Provides the OAuth2 endpoint for generating JWT access tokens.
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.core.config import settings
from src.schemas.auth import ForgotPasswordIn, ResetPasswordIn, Token
from src.services.emails import EmailServiceDep
from src.services.users import UserServiceDep
from src.utils.security import (
    authenticate_user,
    create_access_token,
    create_password_reset_token,
    verify_password_reset_token,
)

router = APIRouter(prefix="/auth")


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserServiceDep,
) -> Token:
    """Authenticate a user and return a JWT access token."""
    user = await authenticate_user(
        form_data.username, form_data.password, user_service
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(
        minutes=settings.access_token_expire_minutes
    )
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    data: ForgotPasswordIn,
    user_service: UserServiceDep,
    email_service: EmailServiceDep,
    background_tasks: BackgroundTasks,
):
    """Send a password reset email if the user exists."""
    user = await user_service.get_user_by_email(data.email)
    if user:
        token = create_password_reset_token(user.email)
        await email_service.send_password_reset_email(
            user.email, token, background_tasks
        )

    return {"message": "Se o e-mail existir, as instruções foram enviadas"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(data: ResetPasswordIn, user_service: UserServiceDep):
    """Reset the user's password using a valid reset token."""
    email = verify_password_reset_token(data.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado",
        )

    await user_service.reset_password(email, data.new_password)
    return {"message": "Senha redefinida com sucesso"}
