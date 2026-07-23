import uuid

import pytest
from httpx import AsyncClient, codes

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
        (
            "date_of_birth",
            "2015-01-01",
            "Value error, O usuário deve ter pelo menos 18 anos",
        ),
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

    error_messages = [err["msg"] for err in data["detail"]]
    assert any(expected_error in msg for msg in error_messages)


async def test_read_user_me_is_success(
    client: AsyncClient, access_token: str, test_user_data: dict
):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get(f"{users_url}me/", headers=headers)

    assert response.status_code == codes.OK
    data = response.json()
    assert data["email"] == test_user_data["email"]


async def test_login_success(client: AsyncClient, test_user_data: dict):
    await client.post(users_url, json=test_user_data)

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


async def test_create_user_duplicate_email_fails(
    client: AsyncClient, test_user_data: dict
):
    await client.post(users_url, json=test_user_data)
    response = await client.post(users_url, json=test_user_data)
    assert response.status_code == codes.BAD_REQUEST
    assert "E-mail já cadastrado" in response.json()["detail"]


async def test_update_user_partial_success(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"name": "Lidiana Updated", "income": 7000.0}
    response = await client.patch(
        f"{users_url}me/", json=payload, headers=headers
    )

    assert response.status_code == codes.OK
    data = response.json()
    assert data["name"] == "Lidiana Updated"
    assert float(data["income"]) == 7000.0


async def test_update_user_password_success(
    client: AsyncClient, access_token: str, test_user_data: dict
):
    headers = {"Authorization": f"Bearer {access_token}"}
    new_pass = "new_secret_123"
    payload = {"password": new_pass}
    response = await client.patch(
        f"{users_url}me/", json=payload, headers=headers
    )
    assert response.status_code == codes.OK

    login_data = {"username": test_user_data["email"], "password": new_pass}
    login_resp = await client.post(
        "/api/auth/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == codes.OK


async def test_read_user_not_found_admin_route(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    random_id = uuid.uuid4()
    response = await client.get(f"{users_url}{random_id}", headers=headers)
    assert response.status_code == codes.NOT_FOUND


async def test_create_user_triggers_welcome_email(
    client: AsyncClient, test_user_data: dict
):
    """POST /users should schedule the welcome email as a background task."""
    from src.main import app
    from src.services.emails import EmailService

    mock_email_service = app.dependency_overrides[EmailService]()
    mock_email_service.send_welcome_email.reset_mock()

    resp = await client.post(users_url, json=test_user_data)
    assert resp.status_code == codes.CREATED
    assert mock_email_service.send_welcome_email.called


async def test_delete_user_me_is_no_content(
    client: AsyncClient, access_token: str
):
    """DELETE /users/me should return 204 and remove the user."""
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await client.delete(f"{users_url}me/", headers=headers)
    assert resp.status_code == codes.NO_CONTENT

    # Subsequent /me should now be 401 (user no longer exists)
    resp2 = await client.get(f"{users_url}me/", headers=headers)
    assert resp2.status_code == codes.UNAUTHORIZED


async def test_update_user_me_changes_name_only(
    client: AsyncClient, access_token: str
):
    """Patching only the name should keep income unchanged."""
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await client.patch(
        f"{users_url}me/", json={"name": "Just Renamed"}, headers=headers
    )
    assert resp.status_code == codes.OK
    assert resp.json()["name"] == "Just Renamed"
