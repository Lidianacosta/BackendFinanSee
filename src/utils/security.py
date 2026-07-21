"""Security operations and JWT management.

Provides dependencies for authenticating users, generating access and
refresh tokens, and extracting the current user from active requests.
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from src.core.config import settings
from src.schemas.auth import TokenData
from src.schemas.users import UserRead
from src.services.users import UserServiceDep
from src.utils.password import verify_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


async def authenticate_user(
    email: str, password: str, user_service: UserServiceDep
):
    """Authenticate a user by email and password."""
    user = await user_service.get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def _create_token(
    data: dict, expires_delta: timedelta, token_type: str
) -> str:
    """Build a signed JWT with the given payload, expiry and type claim."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + expires_delta
    to_encode.update({"exp": expire, "type": token_type})
    return jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )


def create_access_token(
    data: dict, expires_delta: timedelta | None = None
) -> str:
    """Generate a JWT access token (short-lived)."""
    delta = expires_delta or timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return _create_token(data, delta, token_type="access")


def create_refresh_token(
    data: dict, expires_delta: timedelta | None = None
) -> str:
    """Generate a JWT refresh token (long-lived)."""
    delta = expires_delta or timedelta(
        minutes=settings.refresh_token_expire_minutes
    )
    return _create_token(data, delta, token_type="refresh")


def create_password_reset_token(email: str) -> str:
    """Generate a short-lived token for password reset (15 minutes)."""
    expires = datetime.now(UTC) + timedelta(minutes=15)
    to_encode = {"exp": expires, "sub": email, "type": "password_reset"}
    return jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )


def _decode_token_type(token: str, expected_type: str) -> dict | None:
    """Decode a JWT and return payload only if type matches."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        if payload.get("type") != expected_type:
            return None
        return payload
    except InvalidTokenError:
        return None


def verify_password_reset_token(token: str) -> str | None:
    """Verify a password reset token and return the email if valid."""
    payload = _decode_token_type(token, "password_reset")
    if payload is None:
        return None
    return payload.get("sub")


def verify_refresh_token(token: str) -> str | None:
    """Verify a refresh token and return the email (sub) if valid."""
    payload = _decode_token_type(token, "refresh")
    if payload is None:
        return None
    return payload.get("sub")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: UserServiceDep,
):
    """Retrieve the current user from an incoming access JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = _decode_token_type(token, "access")
    if payload is None:
        raise credentials_exception
    email = payload.get("sub")
    if email is None:
        raise credentials_exception
    token_data = TokenData(email=email)
    user = await user_service.get_user_by_email(str(token_data.email))
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(
    current_user: Annotated[UserRead, Depends(get_current_user)],
):
    """Retrieve the current user ensuring their account is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    return current_user
