"""Unit and integration tests for security utilities."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import jwt
import pytest
from fastapi import HTTPException

from src.core.config import settings
from src.utils.security import (
    _decode_token_type,
    authenticate_user,
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    get_current_user,
    verify_password_reset_token,
    verify_refresh_token,
)


def test_create_access_token_has_type_access():
    """create_access_token must include claim type=access."""
    token = create_access_token(data={"sub": "x@test.com"})
    payload = _decode_token_type(token, "access")
    assert payload is not None
    assert payload["sub"] == "x@test.com"


def test_create_refresh_token_has_type_refresh():
    """create_refresh_token must include claim type=refresh."""
    token = create_refresh_token(data={"sub": "x@test.com"})
    payload = _decode_token_type(token, "refresh")
    assert payload is not None
    assert payload["sub"] == "x@test.com"


def test_decode_rejects_wrong_type_access_as_refresh():
    """An access token should not decode as refresh."""
    token = create_access_token(data={"sub": "x@test.com"})
    assert _decode_token_type(token, "refresh") is None


def test_decode_rejects_wrong_type_refresh_as_access():
    """A refresh token should not decode as access."""
    token = create_refresh_token(data={"sub": "x@test.com"})
    assert _decode_token_type(token, "access") is None


def test_decode_rejects_password_reset_as_access():
    """A password reset token should not decode as access."""
    token = create_password_reset_token("x@test.com")
    assert _decode_token_type(token, "access") is None


def test_verify_password_reset_token_valid():
    """verify_password_reset_token returns the email for a valid token."""
    token = create_password_reset_token("x@test.com")
    assert verify_password_reset_token(token) == "x@test.com"


def test_verify_password_reset_token_invalid():
    """verify_password_reset_token returns None for a random string."""
    assert verify_password_reset_token("not-a-jwt") is None


def test_verify_password_reset_token_wrong_type():
    """verify_password_reset_token rejects access tokens."""
    token = create_access_token(data={"sub": "x@test.com"})
    assert verify_password_reset_token(token) is None


def test_verify_refresh_token_valid():
    """verify_refresh_token returns the email for a valid refresh token."""
    token = create_refresh_token(data={"sub": "x@test.com"})
    assert verify_refresh_token(token) == "x@test.com"


def test_verify_refresh_token_invalid():
    """verify_refresh_token returns None for a random string."""
    assert verify_refresh_token("not-a-jwt") is None


def test_verify_refresh_token_wrong_type():
    """verify_refresh_token rejects access tokens."""
    token = create_access_token(data={"sub": "x@test.com"})
    assert verify_refresh_token(token) is None


def test_decode_expired_token_returns_none():
    """An expired token must not decode via _decode_token_type."""
    past_expire = datetime.now(UTC) - timedelta(minutes=5)
    payload = {
        "sub": "expired@test.com",
        "exp": past_expire,
        "type": "access",
    }
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    assert _decode_token_type(token, "access") is None


def test_decode_token_with_invalid_signature_returns_none():
    """A token signed with a random key must be rejected."""
    token = jwt.encode(
        {"sub": "x@test.com", "type": "access", "exp": 99999999999},
        "wrong-secret",
        algorithm="HS256",
    )
    assert _decode_token_type(token, "access") is None


def test_decode_token_without_type_claim_returns_none():
    """A token without 'type' claim is rejected (mismatch expected)."""
    expired_far = datetime.now(UTC) + timedelta(hours=1)
    token = jwt.encode(
        {"sub": "x@test.com", "exp": expired_far},
        settings.secret_key,
        algorithm="HS256",
    )
    assert _decode_token_type(token, "access") is None


@pytest.mark.asyncio
async def test_authenticate_user_not_found():
    """authenticate_user returns None when the user does not exist."""
    from src.services.users import UserService

    user_service = AsyncMock(spec=UserService)
    user_service.get_user_by_email = AsyncMock(return_value=None)

    res = await authenticate_user("nobody@test.com", "anything", user_service)
    assert res is None


@pytest.mark.asyncio
async def test_authenticate_user_inactive():
    """authenticate_user returns None when the user is inactive."""
    from src.models.users import User
    from src.services.users import UserService
    from src.utils.password import get_password_hash

    user = User(
        email="off@test.com",
        hashed_password=get_password_hash("password123"),
        is_active=False,
    )
    user_service = AsyncMock(spec=UserService)
    user_service.get_user_by_email = AsyncMock(return_value=user)

    res = await authenticate_user("off@test.com", "password123", user_service)
    assert res is None


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password():
    """authenticate_user returns None when the password is wrong."""
    from src.models.users import User
    from src.services.users import UserService
    from src.utils.password import get_password_hash

    user = User(
        email="u@test.com",
        hashed_password=get_password_hash("password123"),
    )
    user_service = AsyncMock(spec=UserService)
    user_service.get_user_by_email = AsyncMock(return_value=user)

    res = await authenticate_user("u@test.com", "wrong-pwd", user_service)
    assert res is None


@pytest.mark.asyncio
async def test_authenticate_user_success():
    """authenticate_user returns the user when correct."""
    from src.models.users import User
    from src.services.users import UserService
    from src.utils.password import get_password_hash

    user = User(
        email="ok@test.com",
        hashed_password=get_password_hash("password123"),
    )
    user_service = AsyncMock(spec=UserService)
    user_service.get_user_by_email = AsyncMock(return_value=user)

    res = await authenticate_user("ok@test.com", "password123", user_service)
    assert res is user


@pytest.mark.asyncio
async def test_get_current_user_user_not_found():
    """get_current_user raises 401 when the DB has no such user."""
    from src.services.users import UserService

    token = create_access_token(data={"sub": "ghost@test.com"})
    user_service = AsyncMock(spec=UserService)
    user_service.get_user_by_email = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token, user_service=user_service)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_token_without_sub():
    """get_current_user raises 401 when the token has no 'sub'."""
    from src.services.users import UserService

    expired_far = datetime.now(UTC) + timedelta(hours=1)
    token = jwt.encode(
        {"exp": expired_far, "type": "access"},
        settings.secret_key,
        algorithm="HS256",
    )
    user_service = AsyncMock(spec=UserService)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token, user_service=user_service)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_token_wrong_type():
    """get_current_user rejects tokens with type != access."""
    from src.services.users import UserService

    token = create_refresh_token(data={"sub": "x@test.com"})
    user_service = AsyncMock(spec=UserService)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token, user_service=user_service)
    assert exc.value.status_code == 401
