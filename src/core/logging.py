"""Logging configuration for the FinanSee API.

Provides a structured logger setup and a middleware to log every HTTP
request with its duration and status code.
"""

import logging
import sys
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "request_id=%(request_id)s | %(message)s"
)


class RequestIdFilter(logging.Filter):
    """Inject a per-request id into every log record."""

    def __init__(self) -> None:
        """Initialize filter with a default empty request id."""
        super().__init__()
        self.request_id: str = "-"

    def filter(self, record: logging.LogRecord) -> bool:
        """Attach request_id to the record."""
        if not hasattr(record, "request_id"):
            record.request_id = self.request_id
        return True


_request_filter = RequestIdFilter()


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging once at app startup."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handler.addFilter(_request_filter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log each request with method, path, status and duration in ms."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request and emit log lines."""
        _request_filter.request_id = request.headers.get(
            "X-Request-ID", str(uuid.uuid4())
        )
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logging.getLogger("finansee.request").exception(
                "UNHANDLED method=%s path=%s duration_ms=%.2f",
                request.method,
                request.url.path,
                duration_ms,
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = _request_filter.request_id
        logging.getLogger("finansee.request").info(
            "method=%s path=%s status=%d duration_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
