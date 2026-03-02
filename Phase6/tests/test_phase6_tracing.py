"""Phase 6 tests: request ID tracing."""

import pytest

from ai_restaurant_phase6.tracing import (
    generate_request_id,
    get_request_id,
    set_request_id,
    with_request_id,
)


def test_generate_request_id_returns_uuid_string() -> None:
    rid = generate_request_id()
    assert isinstance(rid, str)
    assert len(rid) == 36
    assert rid.count("-") == 4


def test_get_request_id_default_none() -> None:
    assert get_request_id() is None


def test_set_and_get_request_id() -> None:
    set_request_id("req-123")
    assert get_request_id() == "req-123"
    set_request_id(None)
    assert get_request_id() is None


def test_with_request_id_sets_and_clears_context() -> None:
    assert get_request_id() is None
    with with_request_id("ctx-1") as rid:
        assert rid == "ctx-1"
        assert get_request_id() == "ctx-1"
    assert get_request_id() is None


def test_with_request_id_generates_when_not_provided() -> None:
    with with_request_id() as rid:
        assert rid is not None
        assert len(rid) == 36
        assert get_request_id() == rid


def test_with_request_id_isolates_context() -> None:
    set_request_id("outer")
    with with_request_id("inner") as rid:
        assert get_request_id() == "inner"
    assert get_request_id() == "outer"
    set_request_id(None)
