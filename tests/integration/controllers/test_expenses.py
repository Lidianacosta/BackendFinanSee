import secrets
import uuid

from httpx import AsyncClient, codes

expenses_url = "/api/expenses/"


async def test_create_expense_with_auto_period(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "name": "Compra Mercado",
        "value": 150.0,
        "due_date": "2026-07-20",
        "status": "PENDING",
    }
    response = await client.post(expenses_url, json=payload, headers=headers)
    assert response.status_code == codes.CREATED


async def test_read_expenses_full(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    await client.post(
        expenses_url,
        json={"name": "Busca X", "value": 10, "due_date": "2026-01-01"},
        headers=headers,
    )
    resp = await client.get(expenses_url, headers=headers)
    assert resp.status_code == codes.OK


async def test_update_expense_full_path(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    e = await client.post(
        expenses_url,
        json={"name": "Old Exp", "value": 10, "due_date": "2026-01-01"},
        headers=headers,
    )
    eid = e.json()["id"]

    resp = await client.patch(
        f"{expenses_url}{eid}", json={"name": "New Exp"}, headers=headers
    )
    assert resp.status_code == codes.OK
    assert resp.json()["name"] == "New Exp"


async def test_delete_expense_full_path(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    e = await client.post(
        expenses_url,
        json={"name": "To Del", "value": 10, "due_date": "2026-01-01"},
        headers=headers,
    )
    eid = e.json()["id"]

    resp = await client.delete(f"{expenses_url}{eid}", headers=headers)
    assert resp.status_code == codes.NO_CONTENT


async def test_read_expense_not_found(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get(
        f"{expenses_url}{uuid.uuid4()}", headers=headers
    )
    assert response.status_code == codes.NOT_FOUND


async def test_delete_expense_not_owned_fails(
    client: AsyncClient, access_token: str, generate_valid_cpf
):
    headers_a = {"Authorization": f"Bearer {access_token}"}
    create_resp = await client.post(
        expenses_url,
        json={"name": "Minha A", "value": 10, "due_date": "2026-05-01"},
        headers=headers_a,
    )
    exp_id = create_resp.json()["id"]

    suffix = secrets.token_hex(4)
    password_b = "password_very_long_and_secure_123"
    user_b = {
        "name": "Hacker",
        "email": f"hacker_{suffix}@test.com",
        "password": password_b,
        "confirm_password": password_b,
        "cpf": generate_valid_cpf(),
        "date_of_birth": "1990-01-01",
    }
    await client.post("/api/users/", json=user_b)
    login_resp = await client.post(
        "/api/auth/token",
        data={"username": user_b["email"], "password": password_b},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token_b = login_resp.json()["access_token"]

    response = await client.delete(
        f"{expenses_url}{exp_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == codes.NOT_FOUND


async def test_read_expenses_filtering(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}

    cat1_resp = await client.post(
        "/api/categories/", json={"name": "Lazer"}, headers=headers
    )
    cat2_resp = await client.post(
        "/api/categories/", json={"name": "Saude"}, headers=headers
    )
    cat1_id = cat1_resp.json()["id"]
    cat2_id = cat2_resp.json()["id"]

    await client.post(
        expenses_url,
        json={
            "name": "Cinema",
            "value": 50,
            "due_date": "2026-08-01",
            "status": "PAID",
            "category_ids": [cat1_id],
        },
        headers=headers,
    )
    await client.post(
        expenses_url,
        json={
            "name": "Farmacia",
            "value": 30,
            "due_date": "2026-08-02",
            "status": "PENDING",
            "category_ids": [cat2_id],
        },
        headers=headers,
    )
    await client.post(
        expenses_url,
        json={
            "name": "Jantar",
            "value": 100,
            "due_date": "2026-09-01",
            "status": "PENDING",
            "category_ids": [cat1_id],
        },
        headers=headers,
    )

    resp = await client.get(f"{expenses_url}?search=Cin", headers=headers)
    assert len(resp.json()) == 1
    assert resp.json()[0]["name"] == "Cinema"

    resp = await client.get(f"{expenses_url}?status=PAID", headers=headers)
    assert len(resp.json()) == 1
    assert resp.json()[0]["name"] == "Cinema"

    resp = await client.get(
        f"{expenses_url}?category_ids={cat1_id}", headers=headers
    )
    assert len(resp.json()) == 2

    p_resp = await client.get("/api/periods/", headers=headers)
    p8_id = [p["id"] for p in p_resp.json() if "2026-08" in p["month"]][0]
    resp = await client.get(
        f"{expenses_url}?period_id={p8_id}", headers=headers
    )
    assert len(resp.json()) == 2


async def test_update_expense_categories(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}

    cat1_resp = await client.post(
        "/api/categories/", json={"name": "Viagem"}, headers=headers
    )
    cat1_id = cat1_resp.json()["id"]

    e_resp = await client.post(
        expenses_url,
        json={"name": "Voo", "value": 1000, "due_date": "2026-10-01"},
        headers=headers,
    )
    eid = e_resp.json()["id"]

    resp = await client.patch(
        f"{expenses_url}{eid}",
        json={"category_ids": [cat1_id]},
        headers=headers,
    )
    assert resp.status_code == codes.OK
    assert len(resp.json()["categories"]) == 1
    assert resp.json()["categories"][0]["id"] == cat1_id

    resp = await client.patch(
        f"{expenses_url}{eid}", json={"category_ids": []}, headers=headers
    )
    assert resp.status_code == codes.OK
    assert len(resp.json()["categories"]) == 0
