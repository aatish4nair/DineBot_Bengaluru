"""Phase 6: Request tracing with traceable request IDs."""

import contextvars
import uuid

request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


def get_request_id() -> str | None:
    """Return the current request ID for this context, or None."""
    return request_id_ctx.get()


def set_request_id(value: str | None) -> None:
    """Set the request ID for the current context."""
    request_id_ctx.set(value)


def generate_request_id() -> str:
    """Generate a new unique request ID."""
    return str(uuid.uuid4())


class _RequestIdContext:
    """Context manager that sets a request ID for the current context."""

    def __init__(self, request_id: str | None = None):
        self._request_id = request_id if request_id is not None else generate_request_id()
        self._token: object | None = None

    def __enter__(self) -> str:
        self._token = request_id_ctx.set(self._request_id)
        return self._request_id

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        if self._token is not None:
            request_id_ctx.reset(self._token)


def with_request_id(request_id: str | None = None) -> _RequestIdContext:
    """
    Context manager that sets a request ID for the current context.
    If none provided, generates a new one.
    """
    return _RequestIdContext(request_id)
