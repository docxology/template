"""Exa search error type.

Kept deliberately separate from :mod:`infrastructure.search.literature.base`
so the Exa interface is a fully independent search interface under
``infrastructure/search`` with no cross-import into the literature backends.
"""

from __future__ import annotations


class ExaError(RuntimeError):
    """Raised when an Exa request fails (transport, non-2xx status, or parse).

    Carries the HTTP ``status`` and raw ``body`` when the failure is a non-2xx
    API response, so callers can branch on, e.g., 401 (bad key) vs 400 (bad
    request) without re-parsing.
    """

    def __init__(self, message: str, *, status: int | None = None, body: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.body = body


__all__ = ["ExaError"]
