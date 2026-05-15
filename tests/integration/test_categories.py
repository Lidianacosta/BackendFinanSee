import uuid

import pytest
from httpx import AsyncClient, codes

categories_url = "/api/categories/"


async def test_create_category_success(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"name": "Alimentação", "description": "Gastos com comida"}
    response = await client.post(categories_url, json=payload, headers=headers)

    assert response.status_code == codes.CREATED
    data = response.json()
    assert data["name"] == "Alimentação"
    assert "id" in data


async def test_create_category_duplicate_name_fails(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"name": "Lazer"}
    await client.post(categories_url, json=payload, headers=headers)

    # Tenta criar de novo com o mesmo nome
    response = await client.post(categories_url, json=payload, headers=headers)
    assert response.status_code == codes.BAD_REQUEST
    assert "already exists" in response.json()["detail"]


async def test_read_categories(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    await client.post(
        categories_url, json={"name": "Categoria Um"}, headers=headers
    )
    await client.post(
        categories_url, json={"name": "Categoria Dois"}, headers=headers
    )

    response = await client.get(categories_url, headers=headers)
    assert response.status_code == codes.OK
    assert len(response.json()) >= 2


async def test_update_category(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    create_resp = await client.post(
        categories_url, json={"name": "Old Name"}, headers=headers
    )
    cat_id = create_resp.json()["id"]

    response = await client.patch(
        f"{categories_url}{cat_id}", json={"name": "New Name"}, headers=headers
    )
    assert response.status_code == codes.OK
    assert response.json()["name"] == "New Name"


async def test_delete_category(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    create_resp = await client.post(
        categories_url, json={"name": "To Delete"}, headers=headers
    )
    cat_id = create_resp.json()["id"]

    response = await client.delete(
        f"{categories_url}{cat_id}", headers=headers
    )
    assert response.status_code == codes.NO_CONTENT

    # Verifica se sumiu
    get_resp = await client.get(f"{categories_url}{cat_id}", headers=headers)
    assert get_resp.status_code == codes.NOT_FOUND


async def test_update_category_not_found(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    random_id = uuid.uuid4()
    response = await client.patch(
        f"{categories_url}{random_id}",
        json={"name": "New Name"},
        headers=headers,
    )
    assert response.status_code == codes.NOT_FOUND


async def test_delete_category_not_found(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    random_id = uuid.uuid4()
    response = await client.delete(
        f"{categories_url}{random_id}", headers=headers
    )
    assert response.status_code == codes.NOT_FOUND


@pytest.mark.parametrize(
    "payload",
    (
        {"name": "a"},  # Curto demais
        {"name": "Invalid123"},  # Caracteres inválidos (números)
        {"name": " " * 256},  # Longo demais
    ),
)
async def test_create_category_validation_fails(
    client: AsyncClient, access_token: str, payload: dict
):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.post(categories_url, json=payload, headers=headers)
    assert response.status_code == codes.UNPROCESSABLE_ENTITY
