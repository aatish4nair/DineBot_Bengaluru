"""Phase 6 tests: error handling and graceful fallbacks."""

import pytest

from ai_restaurant_phase6.error_handling import with_graceful_fallback
from ai_restaurant_phase6.metrics import get_metrics, reset_metrics


def test_graceful_fallback_returns_result_on_success() -> None:
    reset_metrics()

    @with_graceful_fallback(fallback_value=None)
    def succeed() -> str:
        return "ok"

    assert succeed() == "ok"
    s = get_metrics().snapshot()
    assert s["request_count"] == 1
    assert s["error_count"] == 0
    assert s["recommendation_count"] == 1


def test_graceful_fallback_returns_fallback_on_exception() -> None:
    reset_metrics()

    @with_graceful_fallback(fallback_value="fallback")
    def fail() -> str:
        raise ValueError("oops")

    assert fail() == "fallback"
    s = get_metrics().snapshot()
    assert s["request_count"] == 1
    assert s["error_count"] == 1
    assert s["recommendation_count"] == 0


def test_graceful_fallback_reraise_propagates_exception() -> None:
    reset_metrics()

    @with_graceful_fallback(fallback_value="x", reraise=True)
    def fail() -> str:
        raise RuntimeError("propagate")

    with pytest.raises(RuntimeError, match="propagate"):
        fail()
    s = get_metrics().snapshot()
    assert s["error_count"] == 1


def test_graceful_fallback_with_args_and_kwargs() -> None:
    reset_metrics()

    @with_graceful_fallback(fallback_value=0)
    def add(a: int, b: int) -> int:
        return a + b

    assert add(2, 3) == 5
    assert add(1, 2) == 3
