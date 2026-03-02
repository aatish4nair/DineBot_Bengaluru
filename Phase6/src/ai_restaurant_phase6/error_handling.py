"""Phase 6: Error handling and graceful fallbacks."""

from collections.abc import Callable
from typing import TypeVar

from .logging_config import get_logger
from .metrics import get_metrics

T = TypeVar("T")
LOG = get_logger(__name__)


def with_graceful_fallback(
    fallback_value: T,
    log_message: str = "Operation failed, using fallback",
    reraise: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that catches exceptions, logs them, records an error metric,
    and returns a fallback value (or re-raises if reraise=True).
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: object, **kwargs: object) -> T:
            metrics = get_metrics()
            metrics.increment_requests()
            try:
                result = fn(*args, **kwargs)
                metrics.increment_recommendations()
                return result
            except Exception as e:
                metrics.increment_errors()
                LOG.exception("%s: %s", log_message, e)
                if reraise:
                    raise
                return fallback_value

        return wrapper  # type: ignore[return-value]

    return decorator
