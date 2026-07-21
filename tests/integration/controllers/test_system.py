import uuid
from datetime import timedelta

import pytest
from httpx import AsyncClient, codes

from src.utils.security import create_access_token


@pytest.mark.asyncio
async def test_auth_token_missing_sub(client: AsyncClient):
    from datetime import UTC, datetime

    import jwt

    from src.core.config import settings

    token = jwt.encode(
        {"exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    response = await client.get(
        "/api/users/me/", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == codes.UNAUTHORIZED
    assert (
        "Não foi possível validar as credenciais" in response.json()["detail"]
    )


@pytest.mark.asyncio
async def test_auth_user_not_found_in_token(client: AsyncClient):
    token = create_access_token(
        {"sub": "ghost@test.com"}, timedelta(minutes=5)
    )
    response = await client.get(
        "/api/users/me/", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == codes.UNAUTHORIZED


@pytest.mark.asyncio
async def test_category_service_duplicate_update_fails(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    await client.post(
        "/api/categories/", json={"name": "Alimentação"}, headers=headers
    )
    c2 = await client.post(
        "/api/categories/", json={"name": "Lazer"}, headers=headers
    )
    c2_id = c2.json()["id"]

    resp = await client.patch(
        f"/api/categories/{c2_id}",
        json={"name": "Alimentação"},
        headers=headers,
    )
    assert resp.status_code in [codes.BAD_REQUEST, codes.INTERNAL_SERVER_ERROR]


@pytest.mark.asyncio
async def test_expense_read_all_with_all_filters(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = "/api/expenses/?search=test&status=PAID&offset=0&limit=10"
    resp = await client.get(url, headers=headers)
    assert resp.status_code == codes.OK


@pytest.mark.asyncio
async def test_report_service_error_handling(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = await client.get(
        f"/api/periods/{uuid.uuid4()}/export", headers=headers
    )
    assert resp.status_code == codes.NOT_FOUND
