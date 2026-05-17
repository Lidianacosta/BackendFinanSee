from httpx import AsyncClient, codes

periods_url = "/api/periods/"


async def test_create_period_success(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"month": "2026-06-15", "total_income": 3000.0}
    response = await client.post(periods_url, json=payload, headers=headers)

    assert response.status_code == codes.CREATED
    data = response.json()
    assert data["month"] == "2026-06-01"


async def test_period_summary_calculation(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}

    p_resp = await client.post(
        periods_url,
        json={"month": "2026-01-01", "total_income": 5000.0},
        headers=headers,
    )
    period_id = p_resp.json()["id"]

    await client.post(
        "/api/expenses/",
        json={
            "name": "Aluguel",
            "value": 2000.0,
            "due_date": "2026-01-10",
            "status": "PAID",
            "period_id": period_id,
        },
        headers=headers,
    )

    await client.post(
        "/api/expenses/",
        json={
            "name": "Internet",
            "value": 500.0,
            "due_date": "2026-01-15",
            "status": "PENDING",
            "period_id": period_id,
        },
        headers=headers,
    )

    response = await client.get(
        f"{periods_url}{period_id}/summary", headers=headers
    )
    assert response.status_code == codes.OK
    summary = response.json()

    assert float(summary["total_income"]) == 5000.0
    assert float(summary["total_expenses_paid"]) == 2000.0
    assert float(summary["total_expenses_pending"]) == 500.0
    assert float(summary["remaining_balance"]) == 3000.0


async def test_create_duplicate_period_fails(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"month": "2026-10-01", "total_income": 1000}
    await client.post(periods_url, json=payload, headers=headers)

    response = await client.post(periods_url, json=payload, headers=headers)
    assert response.status_code == codes.BAD_REQUEST


async def test_read_period_not_found(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    import uuid

    random_id = uuid.uuid4()
    response = await client.get(f"{periods_url}{random_id}", headers=headers)
    assert response.status_code == codes.NOT_FOUND


async def test_period_financial_evolution(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    p_resp = await client.post(
        periods_url,
        json={"month": "2026-05-01", "total_income": 5000.0},
        headers=headers,
    )
    period_id = p_resp.json()["id"]

    response = await client.get(
        f"{periods_url}{period_id}/evolution", headers=headers
    )
    assert response.status_code == codes.OK
    data = response.json()
    assert "evolution" in data
    assert len(data["evolution"]) == 7


async def test_period_expense_analysis(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}

    p_resp = await client.post(
        periods_url, json={"month": "2026-03-01"}, headers=headers
    )
    period_id = p_resp.json()["id"]

    cat_resp = await client.post(
        "/api/categories/", json={"name": "Comida"}, headers=headers
    )
    cat_id = cat_resp.json()["id"]

    await client.post(
        "/api/expenses/",
        json={
            "name": "Almoço",
            "value": 100.0,
            "due_date": "2026-03-05",
            "category_ids": [cat_id],
            "period_id": period_id,
        },
        headers=headers,
    )

    response = await client.get(
        f"{periods_url}{period_id}/analysis", headers=headers
    )
    assert response.status_code == codes.OK
    data = response.json()

    assert float(data["monthly_expense"]) == 100.0
    assert data["category_that_appears_most"]["name"] == "Comida"
    assert len(data["daily_evolution"]) > 0
