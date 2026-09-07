"""Configuration for the Monid HTTP API client.

Canonical reference: https://monid.ai/docs/api/overview.md
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from infrastructure.search.monid.errors import MonidError

DEFAULT_BASE_URL = "https://api.monid.ai"
API_KEY_ENV = "MONID_API_KEY"


@dataclass(frozen=True)
class MonidConfig:
    """Immutable Monid client configuration."""

    api_key: str
    base_url: str = DEFAULT_BASE_URL
    timeout: float = 120.0
    poll_interval_seconds: float = 5.0
    max_poll_attempts: int = 30

    def __post_init__(self) -> None:
        if not self.api_key or not str(self.api_key).strip():
            raise MonidError(f"Monid API key is empty; set {API_KEY_ENV} or pass api_key explicitly")
        object.__setattr__(self, "base_url", self.base_url.rstrip("/"))

    @classmethod
    def from_env(cls, *, base_url: str | None = None, **kwargs: object) -> MonidConfig:
        """Build config from ``MONID_API_KEY``."""
        api_key = os.environ.get(API_KEY_ENV, "").strip()
        if not api_key:
            raise MonidError(f"{API_KEY_ENV} is not set in the environment")
        return cls(api_key=api_key, base_url=base_url or DEFAULT_BASE_URL, **kwargs)  # type: ignore[arg-type]

    def auth_headers(self) -> dict[str, str]:
        """Headers every Monid request must carry."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }


__all__ = ["API_KEY_ENV", "DEFAULT_BASE_URL", "MonidConfig"]
