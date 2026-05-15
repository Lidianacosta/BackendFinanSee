from httpx import AsyncClient, codes

expenses_url = "/api/expenses/"


async def test_create_expense_with_auto_period(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    # Não enviamos period_id, o sistema deve criar sozinho baseado na data
    payload = {
        "name": "Compra Mercado",
        "value": 150.0,
        "due_date": "2026-07-20",
        "status": "AP",
    }
    response = await client.post(expenses_url, json=payload, headers=headers)

    assert response.status_code == codes.CREATED
    data = response.json()
    assert data["name"] == "Compra Mercado"
    assert (
        data["period_id"] is not None
    )  # Verificando que o ID do período foi gerado

    # Verifica se o período realmente existe no banco
    period_id = data["period_id"]
    p_resp = await client.get(f"/api/periods/{period_id}", headers=headers)
    assert p_resp.status_code == codes.OK
    assert p_resp.json()["month"] == "2026-07-01"


async def test_create_expense_with_categories(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}

    # 1. Cria categoria
    cat_resp = await client.post(
        "/api/categories/", json={"name": "Saúde"}, headers=headers
    )
    cat_id = cat_resp.json()["id"]

    # 2. Cria despesa ligada a essa categoria
    payload = {
        "name": "Farmácia",
        "value": 50.0,
        "due_date": "2026-07-25",
        "category_ids": [cat_id],
    }
    response = await client.post(expenses_url, json=payload, headers=headers)
    assert response.status_code == codes.CREATED

    # 3. Verifica se a categoria veio na resposta (Eager Loading)
    data = response.json()
    assert len(data["categories"]) == 1
    assert data["categories"][0]["name"] == "Saúde"


async def test_read_expenses_filtered_by_period(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}

    # Cria despesa em Julho
    await client.post(
        expenses_url,
        json={"name": "Julho", "value": 10, "due_date": "2026-07-01"},
        headers=headers,
    )
    # Cria despesa em Agosto
    aug_resp = await client.post(
        expenses_url,
        json={"name": "Agosto", "value": 20, "due_date": "2026-08-01"},
        headers=headers,
    )
    aug_period_id = aug_resp.json()["period_id"]

    # Filtra apenas por Agosto
    response = await client.get(
        f"{expenses_url}?period_id={aug_period_id}", headers=headers
    )
    assert response.status_code == codes.OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Agosto"


async def test_update_expense_not_found(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    import uuid

    random_id = uuid.uuid4()
    response = await client.patch(
        f"{expenses_url}{random_id}", json={"name": "Novo"}, headers=headers
    )
    assert response.status_code == codes.NOT_FOUND


async def test_create_expense_negative_value_fails(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"name": "Invalido", "value": -10.0, "due_date": "2026-01-01"}
    response = await client.post(expenses_url, json=payload, headers=headers)
    assert response.status_code == codes.UNPROCESSABLE_ENTITY


async def test_cross_user_security(
    client: AsyncClient, access_token: str, test_user_data: dict
):
    # 1. Cria usuário B e pega token B
    headers_a = {"Authorization": f"Bearer {access_token}"}

    import secrets

    password_b = "password_long_enough"
    suffix = secrets.token_hex(4)
    user_b_data = {
        "name": "User B",
        "email": f"user_b_{suffix}@test.com",
        "password": password_b,
        "confirm_password": password_b,
        "income": 1000,
        "cpf": "21415136009",  # CPF Válido garantido
        "date_of_birth": "1990-01-01",
    }
    create_resp = await client.post("/api/users/", json=user_b_data)
    assert create_resp.status_code == 201, (
        f"Create User B failed: {create_resp.text}"
    )

    login_resp = await client.post(
        "/api/auth/token",
        data={"username": user_b_data["email"], "password": password_b},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == 200, f"Login B failed: {login_resp.text}"

    token_b = login_resp.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 2. Usuário B cria uma categoria privada
    cat_resp = await client.post(
        "/api/categories/", json={"name": "Privado B"}, headers=headers_b
    )
    cat_id_b = cat_resp.json()["id"]

    # 3. Usuário A tenta acessar a categoria do Usuário B
    response = await client.get(
        f"/api/categories/{cat_id_b}", headers=headers_a
    )

    # Deve dar 404 (para não confirmar que o ID existe).
    assert response.status_code == codes.NOT_FOUND
