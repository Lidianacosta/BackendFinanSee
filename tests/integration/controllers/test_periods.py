import uuid
from datetime import date

from httpx import AsyncClient, codes

periods_url = "/api/periods/"


async def test_create_period_success(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"month": "2026-06-15", "total_income": 3000.0}
    response = await client.post(periods_url, json=payload, headers=headers)
    assert response.status_code == codes.CREATED
    assert response.json()["month"] == "2026-06-01"


async def test_read_all_periods(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    await client.post(
        periods_url, json={"month": "2026-05-01"}, headers=headers
    )
    response = await client.get(periods_url, headers=headers)
    assert response.status_code == codes.OK


async def test_read_current_period(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get(f"{periods_url}current/", headers=headers)
    assert response.status_code == codes.OK
    assert response.json()["month"] == date.today().replace(day=1).isoformat()


async def test_period_full_analysis(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}

    p_resp = await client.post(
        periods_url, json={"month": "2026-03-01"}, headers=headers
    )
    period_id = p_resp.json()["id"]

    summary_resp = await client.get(
        f"{periods_url}{period_id}/summary", headers=headers
    )
    assert summary_resp.status_code == codes.OK

    evo_resp = await client.get(
        f"{periods_url}{period_id}/evolution", headers=headers
    )
    assert evo_resp.status_code == codes.OK

    ana_resp = await client.get(
        f"{periods_url}{period_id}/analysis", headers=headers
    )
    assert ana_resp.status_code == codes.OK


async def test_read_period_not_found(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get(
        f"{periods_url}{uuid.uuid4()}", headers=headers
    )
    assert response.status_code == codes.NOT_FOUND


async def test_create_duplicate_period_fails(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"month": "2026-10-01", "total_income": 1000}
    await client.post(periods_url, json=payload, headers=headers)
    response = await client.post(periods_url, json=payload, headers=headers)
    assert response.status_code == codes.BAD_REQUEST
