"""Phase 6: Structured logging with request context support."""

import logging
import sys

from .tracing import get_request_id

LOG_FORMAT = "%(asctime)s | %(levelname)s | request_id=%(request_id)s | %(message)s"


class RequestIdFilter(logging.Filter):
    """Inject request_id into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "—"
        return True


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured with request_id in each record."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handler.addFilter(RequestIdFilter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
