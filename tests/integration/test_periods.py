from httpx import AsyncClient, codes

periods_url = "/api/periods/"


async def test_create_period_success(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"month": "2026-06-15", "total_income": 3000.0}
    response = await client.post(periods_url, json=payload, headers=headers)

    assert response.status_code == codes.CREATED
    data = response.json()
    # O validador deve ter mudado para o dia 01
    assert data["month"] == "2026-06-01"


async def test_period_summary_calculation(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}

    # 1. Cria período
    p_resp = await client.post(
        periods_url,
        json={"month": "2026-01-01", "total_income": 5000.0},
        headers=headers,
    )
    period_id = p_resp.json()["id"]

    # 2. Cria uma despesa Paga (2000.0)
    await client.post(
        "/api/expenses/",
        json={
            "name": "Aluguel",
            "value": 2000.0,
            "due_date": "2026-01-10",
            "status": "P",
            "period_id": period_id,
        },
        headers=headers,
    )

    # 3. Cria uma despesa Pendente (500.0)
    await client.post(
        "/api/expenses/",
        json={
            "name": "Internet",
            "value": 500.0,
            "due_date": "2026-01-15",
            "status": "AP",
            "period_id": period_id,
        },
        headers=headers,
    )

    # 4. Busca o resumo
    response = await client.get(
        f"{periods_url}{period_id}/summary", headers=headers
    )
    assert response.status_code == codes.OK
    summary = response.json()

    assert float(summary["total_income"]) == 5000.0
    assert float(summary["total_expenses_paid"]) == 2000.0
    assert float(summary["total_expenses_pending"]) == 500.0
    assert float(summary["remaining_balance"]) == 3000.0  # 5000 - 2000


async def test_create_duplicate_period_fails(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"month": "2026-10-01", "total_income": 1000}
    await client.post(periods_url, json=payload, headers=headers)

    # Tenta criar o mesmo mês de novo
    response = await client.post(periods_url, json=payload, headers=headers)
    assert response.status_code == codes.BAD_REQUEST


async def test_read_period_not_found(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    import uuid

    random_id = uuid.uuid4()
    response = await client.get(f"{periods_url}{random_id}", headers=headers)
    assert response.status_code == codes.NOT_FOUND
