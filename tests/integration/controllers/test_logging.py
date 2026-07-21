import pytest
from httpx import AsyncClient, codes


@pytest.mark.asyncio
async def test_request_id_header_returned(client: AsyncClient):
    """Ensure the request logging middleware returns X-Request-ID."""
    resp = await client.get("/")
    assert resp.status_code == codes.OK
    assert "X-Request-ID" in resp.headers


@pytest.mark.asyncio
async def test_request_id_header_echoed_when_provided(
    client: AsyncClient,
):
    """Custom X-Request-ID sent by the client should be echoed back."""
    custom_id = "my-trace-123"
    resp = await client.get("/", headers={"X-Request-ID": custom_id})
    assert resp.headers["X-Request-ID"] == custom_id
