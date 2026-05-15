import secrets

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.main import app
from src.utils.database import get_async_session

# Banco de dados de teste separado para não sujar o original
TEST_DATABASE_URL = "sqlite+aiosqlite:///test.db"


@pytest_asyncio.fixture(scope="function")
async def db():
    # Criamos um engine específico para os testes
    test_engine = create_async_engine(TEST_DATABASE_URL)

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield test_engine

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture(name="client")
async def get_client(db):
    # Override da sessão para usar o banco de teste
    async def override_get_session():
        async with AsyncSession(db) as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user_data():
    password = secrets.token_urlsafe(16)
    return {
        "name": "Test User",
        "email": f"test_{secrets.token_hex(4)}@test.com",
        "password": password,
        "confirm_password": password,
        "income": 5000.0,
        "cpf": "72475225009",
        "date_of_birth": "2000-01-01",
    }


@pytest_asyncio.fixture
async def access_token(client: AsyncClient, test_user_data):
    # Primeiro criamos o usuário via API
    create_response = await client.post("/api/users/", json=test_user_data)
    if create_response.status_code != 201:
        raise RuntimeError(f"User creation failed: {create_response.text}")

    # Fazemos login para pegar o token
    login_response = await client.post(
        "/api/auth/token",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
            "grant_type": "password",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if login_response.status_code != 200:
        raise RuntimeError(f"Auth failed: {login_response.text}")

    return login_response.json()["access_token"]
