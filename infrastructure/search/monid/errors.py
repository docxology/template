"""Monid client errors."""


class MonidError(Exception):
    """Base error for Monid API failures."""

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        body: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.body = body


__all__ = ["MonidError"]
