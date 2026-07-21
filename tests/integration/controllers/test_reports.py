import uuid

from httpx import AsyncClient, codes

periods_url = "/api/periods/"


async def test_export_period_pdf_success(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}

    p_resp = await client.post(
        periods_url, json={"month": "2026-05-01"}, headers=headers
    )
    period_id = p_resp.json()["id"]

    response = await client.get(
        f"{periods_url}{period_id}/export", headers=headers
    )

    assert response.status_code == codes.OK
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert len(response.content) > 0


async def test_export_period_pdf_not_found(
    client: AsyncClient, access_token: str
):
    headers = {"Authorization": f"Bearer {access_token}"}
    random_id = uuid.uuid4()
    response = await client.get(
        f"{periods_url}{random_id}/export", headers=headers
    )
    assert response.status_code == codes.NOT_FOUND
