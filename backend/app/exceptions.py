"""Domain-specific exceptions for the Oliver backend.

Services raise these; the FastAPI exception handlers in main.py translate them
to HTTP responses. This keeps service code independent of the HTTP layer.
"""

from __future__ import annotations


class TaskNotFoundError(Exception):
    """Raised when a Task with the requested primary key does not exist."""

    def __init__(self, task_id: int) -> None:
        super().__init__(f"Task {task_id} not found")
        self.task_id = task_id


class InvalidOperationError(Exception):
    """Raised when a business-rule constraint is violated.

    Args:
        detail: Human-readable error message.
        http_status_code: HTTP status to return (default 422; use 400 for input validation).
    """

    def __init__(self, detail: str, http_status_code: int = 422) -> None:
        super().__init__(detail)
        self.detail = detail
        self.http_status_code = http_status_code
