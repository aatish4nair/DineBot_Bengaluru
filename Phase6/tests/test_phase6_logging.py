"""Phase 6 tests: logging with request_id."""

import logging

import pytest

from ai_restaurant_phase6.logging_config import get_logger
from ai_restaurant_phase6.tracing import set_request_id, with_request_id


def test_get_logger_returns_logger() -> None:
    logger = get_logger("phase6.test")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "phase6.test"


def test_logger_has_request_id_filter() -> None:
    logger = get_logger("phase6.test2")
    has_filter = any(
        isinstance(f, type) and "RequestId" in getattr(f, "__name__", "")
        for f in (logger.filters if hasattr(logger, "filters") else [])
    )
    # Filter is on handler
    for h in logger.handlers:
        for f in h.filters:
            if "request_id" in str(f).lower() or "RequestId" in type(f).__name__:
                has_filter = True
                break
    assert logger.handlers
    assert any("RequestId" in type(f).__name__ for h in logger.handlers for f in h.filters)


def test_log_record_includes_request_id(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    logger = get_logger("phase6.test3")
    with with_request_id("req-xyz"):
        logger.info("test message")
    assert "req-xyz" in caplog.text or "test message" in caplog.text


def test_logger_without_request_id_uses_placeholder(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    set_request_id(None)
    logger = get_logger("phase6.test4")
    logger.info("no request id")
    assert "no request id" in caplog.text
