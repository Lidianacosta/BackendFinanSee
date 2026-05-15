import pytest
from httpx import AsyncClient, codes

# O prefixo agora é apenas /users/ conforme configurado no main.py
users_url = "/api/users/"

async def test_create_user_is_success(
    client: AsyncClient, test_user_data: dict
):
    response = await client.post(users_url, json=test_user_data)
    assert response.status_code == codes.CREATED
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert "id" in data

@pytest.mark.parametrize(
    "field,new_value,expected_error",
    (
        ("name", "1", "String should have at least 2 characters"),
        ("email", "not-an-email", "value is not a valid email address"),
        ("password", "short", "String should have at least 8 characters"),
        ("cpf", "11111111111", "Value error, CPF inválido"),
        ("date_of_birth", "2015-01-01", "Value error, O usuário deve ter pelo menos 18 anos"),
    ),
)
async def test_create_user_fail_for_invalid_field(
    client: AsyncClient,
    test_user_data: dict,
    field,
    new_value,
    expected_error,
):
    test_user_data.update({field: new_value})
    response = await client.post(users_url, json=test_user_data)

    assert response.status_code == codes.UNPROCESSABLE_ENTITY
    data = response.json()
    
    # Verifica se a mensagem de erro esperada está em algum lugar dos erros do Pydantic
    error_messages = [err["msg"] for err in data["detail"]]
    assert any(expected_error in msg for msg in error_messages)

async def test_read_user_me_is_success(
    client: AsyncClient, 
    access_token: str, 
    test_user_data: dict
):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get(f"{users_url}me/", headers=headers)
    
    assert response.status_code == codes.OK
    data = response.json()
    assert data["email"] == test_user_data["email"]

async def test_login_success(client: AsyncClient, test_user_data: dict):
    # Primeiro criamos o usuário
    await client.post(users_url, json=test_user_data)
    
    # Tentamos logar
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"],
    }
    response = await client.post(
        "/api/auth/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == codes.OK
    assert "access_token" in response.json()
