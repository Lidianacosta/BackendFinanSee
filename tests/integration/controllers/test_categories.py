import secrets
import uuid

import pytest
from httpx import AsyncClient, codes


async def test_create_category_success(
    client: AsyncClient, access_token: str, categories_url: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"name": "Alimentação", "description": "Gastos com comida"}

    response = await client.post(categories_url, json=payload, headers=headers)

    assert response.status_code == codes.CREATED


async def test_create_category_duplicate_name_fails(
    client: AsyncClient, access_token: str, categories_url: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"name": "Lazer"}

    await client.post(categories_url, json=payload, headers=headers)
    response = await client.post(categories_url, json=payload, headers=headers)
    data = response.json()

    assert response.status_code == codes.BAD_REQUEST
    assert data["detail"] == "Já existe uma categoria com este nome"


@pytest.mark.parametrize(
    "field,value, error_message",
    (
        ("name", "131321332213311231", "Nome contém caracteres inválidos"),
        (
            "description",
            "invalid_description_with_semicolon;",
            "Descrição contém caracteres inválidos",
        ),
    ),
)
async def test_create_category_fails_for_invalid_field(
    client: AsyncClient,
    access_token: str,
    field,
    value,
    error_message,
    categories_url: str,
):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"name": "Lazer", "Description": "Programar"}
    payload.update({field: value})

    response = await client.post(
        categories_url,
        json=payload,
        headers=headers,
    )
    data = response.json()

    assert response.status_code == codes.UNPROCESSABLE_ENTITY
    assert error_message in data["detail"][0]["msg"]


async def test_read_categories_all(
    client: AsyncClient, access_token: str, categories_url: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    await client.post(categories_url, json={"name": "Cat A"}, headers=headers)

    response = await client.get(categories_url, headers=headers)
    data = response.json()

    assert response.status_code == codes.OK
    assert len(data) >= 1


async def test_read_categories_all_return_noting_for_other_user(
    client: AsyncClient,
    access_token: str,
    other_user_access_token,
    categories_url: str,
):

    headers = {"Authorization": f"Bearer {access_token}"}
    await client.post(categories_url, json={"name": "Cat A"}, headers=headers)
    owner_response = await client.get(categories_url, headers=headers)
    owner_data = owner_response.json()

    headers = {"Authorization": f"Bearer {other_user_access_token}"}
    other_user_response = await client.get(categories_url, headers=headers)
    other_user_data = other_user_response.json()

    assert owner_response.status_code == codes.OK
    assert len(owner_data) >= 1
    assert other_user_response.status_code == codes.OK
    assert len(other_user_data) >= 0


async def test_read_category_success(
    client: AsyncClient,
    access_token: str,
    categories_url: str,
    categories: list[dict[str, str]],
):
    category_to_read = categories[0]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get(
        f"{categories_url}{category_to_read['id']}", headers=headers
    )
    assert response.status_code == codes.OK


async def test_read_category_not_found(
    client: AsyncClient, access_token: str, categories_url: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get(
        f"{categories_url}{uuid.uuid4()}", headers=headers
    )
    assert response.status_code == codes.NOT_FOUND


async def test_read_category_return_noting_for_other_user(
    client: AsyncClient,
    other_user_access_token,
    categories_url: str,
    categories,
):

    headers = {"Authorization": f"Bearer {other_user_access_token}"}
    response = await client.get(
        f"{categories_url}{categories[0]['id']}", headers=headers
    )

    assert response.status_code == codes.NOT_FOUND


@pytest.mark.parametrize(
    "field,value", (("name", "New Name"), ("description", "New Description"))
)
async def test_update_category_invalid_values(
    client: AsyncClient,
    access_token: str,
    categories_url: str,
    field: str,
    value: str,
    categories,
):
    category = categories[0]
    headers = {"Authorization": f"Bearer {access_token}"}

    response = await client.patch(
        f"{categories_url}{category['id']}",
        json={field: value},
        headers=headers,
    )
    data = response.json()

    assert response.status_code == codes.OK
    assert data[field] != category[field]
    assert data[field] == value


async def test_update_category_success_fail_for_invalid_id(
    client: AsyncClient, access_token: str, categories_url: str
):
    headers = {"Authorization": f"Bearer {access_token}"}

    response = await client.patch(
        f"{categories_url}{'invalid'}", json={"name": "New"}, headers=headers
    )
    assert response.status_code == codes.UNPROCESSABLE_ENTITY


async def test_delete_category_full_path(
    client: AsyncClient, access_token: str, categories_url: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    c = await client.post(
        categories_url, json={"name": "To Delete"}, headers=headers
    )
    cid = c.json()["id"]

    response = await client.delete(f"{categories_url}{cid}", headers=headers)
    assert response.status_code == codes.NO_CONTENT


async def test_delete_category_not_owned_fails(
    client: AsyncClient,
    access_token: str,
    generate_valid_cpf,
    categories_url: str,
):
    headers_a = {"Authorization": f"Bearer {access_token}"}
    create_resp = await client.post(
        categories_url, json={"name": "Privada A"}, headers=headers_a
    )
    cat_id = create_resp.json()["id"]

    suffix = secrets.token_hex(4)
    password_b = "password_very_long_and_secure_123"
    user_b_payload = {
        "name": "User B",
        "email": f"user_b_{suffix}@test.com",
        "password": password_b,
        "confirm_password": password_b,
        "cpf": generate_valid_cpf(),
        "date_of_birth": "1990-01-01",
    }
    await client.post("/api/users/", json=user_b_payload)
    login_resp = await client.post(
        "/api/auth/token",
        data={"username": user_b_payload["email"], "password": password_b},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token_b = login_resp.json()["access_token"]

    response = await client.delete(
        f"{categories_url}{cat_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == codes.NOT_FOUND
