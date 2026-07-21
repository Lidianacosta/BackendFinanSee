import secrets
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.main import app
from src.services.emails import EmailService

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def generate_valid_cpf():
    """Generate a random valid Brazilian CPF."""

    def get_cpf():
        def calculate_digits(digits):
            for _ in range(2):
                val = sum(
                    d * (len(digits) + 1 - i) for i, d in enumerate(digits)
                )
                digit = 11 - (val % 11)
                digits.append(0 if digit >= 10 else digit)
            return digits

        nums = [secrets.randbelow(10) for _ in range(9)]
        return "".join(map(str, calculate_digits(nums)))

    return get_cpf


@pytest_asyncio.fixture(scope="function")
async def db():
    from src import models  # noqa

    test_engine = create_async_engine(TEST_DATABASE_URL)
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        yield session
    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db):
    from src.utils.database import get_async_session

    # Mock EmailService to avoid real SMTP connection errors
    mock_email_service = AsyncMock(spec=EmailService)
    app.dependency_overrides[EmailService] = lambda: mock_email_service
    app.dependency_overrides[get_async_session] = lambda: db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user_data():
    suffix = secrets.token_hex(4)
    return {
        "name": "Test User",
        "email": f"test_{suffix}@test.com",
        "password": "password123",
        "confirm_password": "password123",
        "income": 1000,
    }


@pytest_asyncio.fixture(scope="function")
async def access_token(test_user_data, create_user, get_access_token):
    await create_user(test_user_data)
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"],
    }
    return await get_access_token(login_data)


@pytest.fixture
def get_access_token(client):
    async def _get_access_token(login_data):
        response = await client.post(
            "/api/auth/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return response.json()["access_token"]

    return _get_access_token


@pytest.fixture
def create_user(client):
    async def _create_user(user_data):
        return (await client.post("/api/users/", json=user_data)).json()

    return _create_user


@pytest_asyncio.fixture(scope="function")
async def other_user_access_token(create_user, get_access_token):
    suffix = secrets.token_hex(4)
    other_user_data = {
        "name": "Other User",
        "email": f"other_{suffix}@test.com",
        "password": "password123",
        "confirm_password": "password123",
        "income": 1000,
    }
    await create_user(other_user_data)
    login_data = {
        "username": other_user_data["email"],
        "password": other_user_data["password"],
    }
    return await get_access_token(login_data)
