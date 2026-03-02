"""Phase 6 tests: metrics store."""

import pytest

from ai_restaurant_phase6.metrics import (
    MetricsStore,
    get_metrics,
    reset_metrics,
)


def test_metrics_store_snapshot_defaults() -> None:
    reset_metrics()
    m = get_metrics()
    s = m.snapshot()
    assert s["request_count"] == 0
    assert s["error_count"] == 0
    assert s["recommendation_count"] == 0


def test_metrics_store_increments() -> None:
    reset_metrics()
    m = get_metrics()
    m.increment_requests()
    m.increment_requests()
    m.increment_errors()
    m.increment_recommendations()
    s = m.snapshot()
    assert s["request_count"] == 2
    assert s["error_count"] == 1
    assert s["recommendation_count"] == 1


def test_get_metrics_singleton() -> None:
    reset_metrics()
    a = get_metrics()
    b = get_metrics()
    assert a is b


def test_reset_metrics_creates_new_store() -> None:
    m1 = get_metrics()
    m1.increment_requests()
    reset_metrics()
    m2 = get_metrics()
    assert m2.snapshot()["request_count"] == 0
