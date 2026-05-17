import pytest
from httpx import AsyncClient, codes

from src.main import app
from src.services.emails import EmailService

auth_url = "/api/auth/"


@pytest.mark.asyncio
async def test_forgot_password_is_success(
    client: AsyncClient, test_user_data: dict
):
    # 1. Primeiro criamos o usuário
    await client.post("/api/users/", json=test_user_data)

    # 2. Solicitamos o reset de senha
    payload = {"email": test_user_data["email"]}
    response = await client.post(f"{auth_url}forgot-password", json=payload)

    assert response.status_code == codes.OK
    assert "instruções foram enviadas" in response.json()["message"]

    # 3. Verificamos se o serviço de email foi chamado (Mock)
    mock_email_service = app.dependency_overrides[EmailService]()
    assert mock_email_service.send_password_reset_email.called


@pytest.mark.asyncio
async def test_reset_password_flow_complete(
    client: AsyncClient, test_user_data: dict
):
    from src.utils.security import create_password_reset_token

    # 1. Criamos o usuário
    await client.post("/api/users/", json=test_user_data)

    # 2. Geramos um token manualmente para o teste (simulando o recebido por email)
    token = create_password_reset_token(test_user_data["email"])

    # 3. Redefinimos a senha
    new_password = "new_secure_password"
    payload = {
        "token": token,
        "new_password": new_password,
        "confirm_password": new_password,
    }
    response = await client.post(f"{auth_url}reset-password", json=payload)

    assert response.status_code == codes.OK
    assert "Senha redefinida com sucesso" in response.json()["message"]

    # 4. Verificamos se conseguimos logar com a nova senha
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
