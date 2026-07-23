import logging

import pytest
from httpx import AsyncClient, codes

from src.main import app  # noqa: F401  - ensure app is imported for client


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


@pytest.mark.asyncio
async def test_request_logging_middleware_logs_unhandled_exception(caplog):
    """The middleware except branch logs and re-raises when call_next fails.

    We instantiate the middleware directly with a fake app whose call_next
    raises, so the except branch in dispatch() is exercised in isolation.
    """
    from starlette.requests import Request

    from src.core.logging import RequestLoggingMiddleware

    async def boom_app(scope, receive, send):
        """Fake downstream app that raises during dispatch."""
        raise RuntimeError("boom")

    mw = RequestLoggingMiddleware(boom_app)
    req = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/_raise",
            "headers": [],
            "query_string": b"",
        }
    )

    with caplog.at_level(logging.ERROR, logger="finansee.request"):
        with pytest.raises(RuntimeError, match="boom"):
            await mw.dispatch(req, lambda r: boom_app(r.scope, None, None))
