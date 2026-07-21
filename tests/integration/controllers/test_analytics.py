import pytest
from httpx import AsyncClient, codes

periods_url = "/api/periods/"
expenses_url = "/api/expenses/"


@pytest.mark.asyncio
async def test_period_duplicate_error_path(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"month": "2026-12-01"}
    await client.post(periods_url, json=payload, headers=headers)
    resp = await client.post(periods_url, json=payload, headers=headers)
    assert resp.status_code == codes.BAD_REQUEST
    assert "Já existe um período para este mês" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_period_evolution_with_missing_months(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    p_resp = await client.post(
        periods_url, json={"month": "2026-06-01"}, headers=headers
    )
    period_id = p_resp.json()["id"]

    response = await client.get(
        f"{periods_url}{period_id}/evolution", headers=headers
    )
    assert response.status_code == codes.OK
    data = response.json()["evolution"]
    assert float(data[0]["data"]["monthly_expense"]) == 0.0


@pytest.mark.asyncio
async def test_expense_analysis_with_no_expenses(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    p_resp = await client.post(
        periods_url, json={"month": "2026-08-01"}, headers=headers
    )
    period_id = p_resp.json()["id"]

    response = await client.get(
        f"{periods_url}{period_id}/analysis", headers=headers
    )
    assert response.status_code == codes.OK
    data = response.json()
    assert float(data["monthly_expense"]) == 0.0
    assert data["category_that_appears_most"] == {}


@pytest.mark.asyncio
async def test_expense_analysis_top_category_logic(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    p_resp = await client.post(
        periods_url, json={"month": "2026-09-01"}, headers=headers
    )
    period_id = p_resp.json()["id"]

    c1 = await client.post(
        "/api/categories/", json={"name": "Categoria Um"}, headers=headers
    )
    c2 = await client.post(
        "/api/categories/", json={"name": "Categoria Dois"}, headers=headers
    )
    cid_a = c1.json()["id"]
    cid_b = c2.json()["id"]

    await client.post(
        expenses_url,
        json={
            "name": "Exp Um",
            "value": 10,
            "due_date": "2026-09-01",
            "category_ids": [cid_a],
            "period_id": period_id,
        },
        headers=headers,
    )
    await client.post(
        expenses_url,
        json={
            "name": "Exp Dois",
            "value": 10,
            "due_date": "2026-09-02",
            "category_ids": [cid_b],
            "period_id": period_id,
        },
        headers=headers,
    )
    await client.post(
        expenses_url,
        json={
            "name": "Exp Tres",
            "value": 10,
            "due_date": "2026-09-03",
            "category_ids": [cid_b],
            "period_id": period_id,
        },
        headers=headers,
    )

    response = await client.get(
        f"{periods_url}{period_id}/analysis", headers=headers
    )
    assert (
        response.json()["category_that_appears_most"]["name"]
        == "Categoria Dois"
    )


@pytest.mark.asyncio
async def test_update_user_income_sync_period(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    await client.get(f"{periods_url}current/", headers=headers)

    new_income = 9999.0
    await client.patch(
        "/api/users/me/", json={"income": new_income}, headers=headers
    )

    updated_curr = await client.get(f"{periods_url}current/", headers=headers)
    assert float(updated_curr.json()["total_income"]) == new_income


@pytest.mark.asyncio
async def test_period_evolution_year_wrap(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    p_resp = await client.post(
        periods_url, json={"month": "2026-01-01"}, headers=headers
    )
    period_id = p_resp.json()["id"]

    response = await client.get(
        f"{periods_url}{period_id}/evolution", headers=headers
    )
    assert response.status_code == codes.OK

    p_resp = await client.post(
        periods_url, json={"month": "2026-12-01"}, headers=headers
    )
    period_id = p_resp.json()["id"]

    response = await client.get(
        f"{periods_url}{period_id}/evolution", headers=headers
    )
    assert response.status_code == codes.OK


@pytest.mark.asyncio
async def test_expense_analysis_different_month_lengths(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}

    p_resp = await client.post(
        periods_url, json={"month": "2025-02-01"}, headers=headers
    )
    period_id = p_resp.json()["id"]
    response = await client.get(
        f"{periods_url}{period_id}/analysis", headers=headers
    )
    assert response.status_code == codes.OK

    p_resp = await client.post(
        periods_url, json={"month": "2024-02-01"}, headers=headers
    )
    period_id = p_resp.json()["id"]
    response = await client.get(
        f"{periods_url}{period_id}/analysis", headers=headers
    )
    assert response.status_code == codes.OK

    p_resp = await client.post(
        periods_url, json={"month": "2025-01-01"}, headers=headers
    )
    period_id = p_resp.json()["id"]
    response = await client.get(
        f"{periods_url}{period_id}/analysis", headers=headers
    )
    assert response.status_code == codes.OK
