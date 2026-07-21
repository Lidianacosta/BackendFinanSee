import uuid

import pytest
from httpx import AsyncClient, codes
from sqlmodel import col, select

from src.models.users import User


@pytest.mark.asyncio
async def test_login_invalid_password(
    client: AsyncClient, test_user_data: dict
):
    await client.post("/api/users/", json=test_user_data)
    login_data = {
        "username": test_user_data["email"],
        "password": "wrongpassword",
    }
    response = await client.post(
        "/api/auth/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == codes.UNAUTHORIZED
    assert "E-mail ou senha incorretos" in response.json()["detail"]


@pytest.mark.asyncio
async def test_read_user_not_found_explicit(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get(f"/api/users/{uuid.uuid4()}", headers=headers)
    assert response.status_code == codes.NOT_FOUND


@pytest.mark.asyncio
async def test_inactive_user_login_fail(
    client: AsyncClient, test_user_data: dict, db
):
    await client.post("/api/users/", json=test_user_data)

    statement = select(User).where(col(User.email) == test_user_data["email"])
    result = await db.exec(statement)
    user = result.first()
    user.is_active = False
    db.add(user)
    await db.commit()

    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"],
    }
    response = await client.post(
        "/api/auth/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == codes.UNAUTHORIZED


import pytest
from httpx import AsyncClient

from src.utils.security import create_password_reset_token


@pytest.mark.asyncio
async def test_auth_full_flow(client: AsyncClient, test_user_data):
    await client.post("/api/users/", json=test_user_data)

    response = await client.post(
        "/api/auth/token",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

    response = await client.post(
        "/api/auth/token",
        data={
            "username": test_user_data["email"],
            "password": "wrongpassword",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "E-mail ou senha incorretos"

    response = await client.post(
        "/api/auth/forgot-password", json={"email": test_user_data["email"]}
    )
    assert response.status_code == 200
    assert "instruções foram enviadas" in response.json()["message"]

    response = await client.post(
        "/api/auth/forgot-password", json={"email": "nonexistent@test.com"}
    )
    assert response.status_code == 200

    token = create_password_reset_token(test_user_data["email"])
    response = await client.post(
        "/api/auth/reset-password",
        json={
            "token": token,
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        },
    )
    assert response.status_code == 200
    assert "Senha redefinida com sucesso" in response.json()["message"]

    response = await client.post(
        "/api/auth/reset-password",
        json={
            "token": "invalidtoken",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        },
    )
    assert response.status_code == 400
    assert "Token inválido ou expirado" in response.json()["detail"]


import pytest
from httpx import AsyncClient

from src.main import app
from src.services.emails import EmailService

auth_url = "/api/auth/"


@pytest.mark.asyncio
async def test_forgot_password_is_success(
    client: AsyncClient, test_user_data: dict
):
    await client.post("/api/users/", json=test_user_data)

    payload = {"email": test_user_data["email"]}
    response = await client.post(f"{auth_url}forgot-password", json=payload)

    assert response.status_code == codes.OK
    assert "instruções foram enviadas" in response.json()["message"]

    mock_email_service = app.dependency_overrides[EmailService]()
    assert mock_email_service.send_password_reset_email.called


@pytest.mark.asyncio
async def test_reset_password_flow_complete(
    client: AsyncClient, test_user_data: dict
):
    from src.utils.security import create_password_reset_token

    await client.post("/api/users/", json=test_user_data)

    token = create_password_reset_token(test_user_data["email"])

    new_password = "new_secure_password"
    payload = {
        "token": token,
        "new_password": new_password,
        "confirm_password": new_password,
    }
    response = await client.post(f"{auth_url}reset-password", json=payload)

    assert response.status_code == codes.OK
    assert "Senha redefinida com sucesso" in response.json()["message"]

    login_data = {
        "username": test_user_data["email"],
        "password": new_password,
    }
    login_response = await client.post(
        f"{auth_url}token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == codes.OK
    assert "access_token" in login_response.json()


@pytest.mark.asyncio
async def test_reset_password_fails_with_mismatched_passwords(
    client: AsyncClient,
):
    payload = {
        "token": "valid_token_but_not_relevant_here",
        "new_password": "password123",
        "confirm_password": "different_password",
    }
    response = await client.post(f"{auth_url}reset-password", json=payload)

    assert response.status_code == codes.UNPROCESSABLE_ENTITY
    assert "As senhas não coincidem" in response.text


@pytest.mark.asyncio
async def test_reset_password_fails_with_invalid_token(client: AsyncClient):
    payload = {
        "token": "invalid_or_expired_token",
        "new_password": "new_secure_password",
        "confirm_password": "new_secure_password",
    }
    response = await client.post(f"{auth_url}reset-password", json=payload)

    assert response.status_code == codes.BAD_REQUEST
    assert "Token inválido ou expirado" in response.json()["detail"]


@pytest.mark.asyncio
async def test_reset_password_fails_with_wrong_token_type(
    client: AsyncClient, test_user_data: dict
):
    await client.post("/api/users/", json=test_user_data)
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"],
    }
    login_resp = await client.post(
        f"{auth_url}token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    access_token = login_resp.json()["access_token"]

    payload = {
        "token": access_token,
        "new_password": "new_secure_password",
        "confirm_password": "new_secure_password",
    }
    response = await client.post(f"{auth_url}reset-password", json=payload)

    assert response.status_code == codes.BAD_REQUEST
    assert "Token inválido ou expirado" in response.json()["detail"]


@pytest.mark.asyncio
async def test_reset_password_fails_for_non_existent_user(client: AsyncClient):
    from src.utils.security import create_password_reset_token

    token = create_password_reset_token("nonexistent@example.com")

    payload = {
        "token": token,
        "new_password": "new_secure_password",
        "confirm_password": "new_secure_password",
    }
    response = await client.post(f"{auth_url}reset-password", json=payload)

    assert response.status_code == codes.NOT_FOUND
    assert "Usuário não encontrado" in response.json()["detail"]
