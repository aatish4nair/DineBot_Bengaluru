"""Phase 6: In-memory metrics (counters and timers)."""

import time
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class MetricsStore:
    """Thread-safe in-memory metrics."""

    request_count: int = 0
    error_count: int = 0
    recommendation_count: int = 0
    _lock: Lock = field(default_factory=Lock, repr=False)

    def increment_requests(self) -> None:
        with self._lock:
            self.request_count += 1

    def increment_errors(self) -> None:
        with self._lock:
            self.error_count += 1

    def increment_recommendations(self) -> None:
        with self._lock:
            self.recommendation_count += 1

    def snapshot(self) -> dict[str, int]:
        """Return a copy of current counter values."""
        with self._lock:
            return {
                "request_count": self.request_count,
                "error_count": self.error_count,
                "recommendation_count": self.recommendation_count,
            }


_default_store: MetricsStore | None = None


def get_metrics() -> MetricsStore:
    """Return the global metrics store (singleton)."""
    global _default_store
    if _default_store is None:
        _default_store = MetricsStore()
    return _default_store


def reset_metrics() -> None:
    """Reset the global metrics store (for tests)."""
    global _default_store
    _default_store = MetricsStore()
