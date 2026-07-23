"""Authentication controller.

Provides the OAuth2 endpoint for generating JWT access/refresh tokens
and the refresh endpoint to renew access tokens.
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.core.config import settings
from src.schemas.auth import (
    ForgotPasswordIn,
    RefreshIn,
    ResetPasswordIn,
    Token,
    TokenPair,
)
from src.services.emails import EmailServiceDep
from src.services.users import UserServiceDep
from src.utils.security import (
    authenticate_user,
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    verify_password_reset_token,
    verify_refresh_token,
)

router = APIRouter(prefix="/auth")


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserServiceDep,
) -> Token:
    """Authenticate a user and return access + refresh JWT tokens."""
    user = await authenticate_user(
        form_data.username, form_data.password, user_service
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_expires = timedelta(minutes=settings.access_token_expire_minutes)
    refresh_expires = timedelta(minutes=settings.refresh_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_expires
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh_access_token(
    data: RefreshIn,
    user_service: UserServiceDep,
) -> TokenPair:
    """Issue a new access token from a valid refresh token."""
    refresh_token = data.refresh_token
    email = verify_refresh_token(refresh_token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await user_service.get_user_by_email(email)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inválido ou inativo",
        )
    access_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_expires
    )
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


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
        token = create_password_reset_token(user.email or "")
        await email_service.send_password_reset_email(
            user.email or "", token, background_tasks
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
