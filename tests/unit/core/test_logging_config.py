"""Unit tests for logging configuration and request id handling."""

import logging

from src.core.logging import (
    RequestIdFilter,
    configure_logging,
)


def test_request_id_filter_assigns_when_missing():
    """filter should set request_id when record does not have it."""
    f = RequestIdFilter()
    f.request_id = "abc-123"
    record = logging.LogRecord(
        name="x", level=logging.INFO, pathname="", lineno=1,
        msg="hello", args=(), exc_info=None,
    )
    assert not hasattr(record, "request_id")
    assert f.filter(record) is True
    assert record.request_id == "abc-123"


def test_request_id_filter_preserves_existing_value():
    """filter should not overwrite when record already has request_id."""
    f = RequestIdFilter()
    f.request_id = "new"
    record = logging.LogRecord(
        name="x", level=logging.INFO, pathname="", lineno=1,
        msg="hello", args=(), exc_info=None,
    )
    record.request_id = "existing"
    f.filter(record)
    assert record.request_id == "existing"


def test_configure_logging_installs_handler_and_level():
    """configure_logging should clear handlers and set the level."""
    root = logging.getLogger()
    root.handlers = []  # reset
    configure_logging("DEBUG")
    assert root.level == logging.DEBUG
    assert any(isinstance(h, logging.StreamHandler) for h in root.handlers)


def test_configure_logging_with_string_level():
    """configure_logging should uppercase the level string."""
    root = logging.getLogger()
    configure_logging("warning")
    assert root.level == logging.WARNING
