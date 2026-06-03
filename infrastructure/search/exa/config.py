"""Configuration for the Exa search client.

The only required secret is ``EXA_API_KEY``. Everything else has a documented
default so a coding agent can construct :class:`ExaConfig` with nothing but the
environment variable set.

Canonical reference (source of truth for hosts/params/shape):
https://docs.exa.ai/reference/search-api-guide-for-coding-agents
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from infrastructure.search.exa.errors import ExaError

#: Public Exa REST host. Override per-request only for tests (httpserver).
DEFAULT_BASE_URL = "https://api.exa.ai"

#: Environment variable holding the API key.
API_KEY_ENV = "EXA_API_KEY"

#: Balanced default search type — see the Search Type Reference in the guide.
DEFAULT_SEARCH_TYPE = "auto"

#: Valid ``type`` values accepted by ``POST /search``.
VALID_SEARCH_TYPES = frozenset({"auto", "fast", "instant", "deep-lite", "deep", "deep-reasoning"})


@dataclass(frozen=True)
class ExaConfig:
    """Immutable Exa client configuration.

    Attributes:
        api_key: Exa API key (sent as the ``x-api-key`` header).
        base_url: REST host, without a trailing slash.
        default_type: ``type`` used when a search call does not specify one.
        timeout: Per-request timeout in seconds. Deep search types stack
            latency, so allow generous headroom (default 60s).
    """

    api_key: str
    base_url: str = DEFAULT_BASE_URL
    default_type: str = DEFAULT_SEARCH_TYPE
    timeout: float = 60.0

    def __post_init__(self) -> None:
        if not self.api_key or not str(self.api_key).strip():
            raise ExaError(f"Exa API key is empty; set {API_KEY_ENV} or pass api_key explicitly")
        if self.default_type not in VALID_SEARCH_TYPES:
            raise ExaError(f"invalid default_type {self.default_type!r}; expected one of {sorted(VALID_SEARCH_TYPES)}")
        # Normalise away a trailing slash so path joins stay clean.
        object.__setattr__(self, "base_url", self.base_url.rstrip("/"))

    @classmethod
    def from_env(cls, *, base_url: str | None = None, **kwargs: object) -> ExaConfig:
        """Build config from ``EXA_API_KEY``.

        Raises:
            ExaError: when the environment variable is unset or blank.
        """
        api_key = os.environ.get(API_KEY_ENV, "").strip()
        if not api_key:
            raise ExaError(f"{API_KEY_ENV} is not set in the environment")
        return cls(api_key=api_key, base_url=base_url or DEFAULT_BASE_URL, **kwargs)  # type: ignore[arg-type]

    def auth_headers(self) -> dict[str, str]:
        """Headers every Exa request must carry."""
        return {"x-api-key": self.api_key, "Content-Type": "application/json"}


__all__ = [
    "API_KEY_ENV",
    "DEFAULT_BASE_URL",
    "DEFAULT_SEARCH_TYPE",
    "ExaConfig",
    "VALID_SEARCH_TYPES",
]
