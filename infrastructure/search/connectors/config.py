"""Configuration loading for the connector search module."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ConnectorSearchConfig:
    """Runtime configuration for the connector registry.

    Attributes:
        enabled_connectors: Names of connectors to activate.  Empty list means
            all built-in connectors.
        default_max_results: Default result cap when :class:`SearchOptions` is
            not supplied.
        cache_ttl: HTTP-cache TTL in seconds.  Pass ``0`` to disable.
        mailto: Polite-pool email forwarded to backends that support it
            (OpenAlex, Crossref).
    """

    enabled_connectors: list[str] = field(default_factory=list)
    default_max_results: int = 10
    cache_ttl: float = 300.0
    mailto: str = "team@example.org"
    source_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize this object to a plain dict for JSON output."""
        return {
            "enabled_connectors": self.enabled_connectors,
            "default_max_results": self.default_max_results,
            "cache_ttl": self.cache_ttl,
            "mailto": self.mailto,
        }


_CONFIG_KEYS = frozenset(
    {
        "enabled_connectors",
        "default_max_results",
        "cache_ttl",
        "mailto",
    }
)


def load_connector_search_config(project_dir: Path | str) -> ConnectorSearchConfig:
    """Load optional ``connector_search.yaml`` from *project_dir*.

    Falls back to defaults when the file is absent.

    Args:
        project_dir: Project root directory.

    Returns:
        A populated :class:`ConnectorSearchConfig`.

    Raises:
        ValueError: On unknown keys or invalid values.
    """
    project_dir = Path(project_dir)
    config_path = project_dir / "connector_search.yaml"
    if not config_path.exists():
        return ConnectorSearchConfig()

    try:
        import yaml

        payload: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except ImportError:
        import json as _json

        payload = _json.loads(config_path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError(f"connector_search.yaml must be a mapping: {config_path}")

    unknown = set(payload) - _CONFIG_KEYS
    if unknown:
        raise ValueError(f"unknown connector_search key(s): {', '.join(sorted(str(k) for k in unknown))}")

    enabled = payload.get("enabled_connectors") or []
    if not isinstance(enabled, list):
        raise ValueError("connector_search.enabled_connectors must be a list")

    max_results = payload.get("default_max_results", 10)
    if not isinstance(max_results, int) or max_results <= 0:
        raise ValueError("connector_search.default_max_results must be a positive integer")

    cache_ttl = payload.get("cache_ttl", 300.0)
    if not isinstance(cache_ttl, (int, float)) or cache_ttl < 0:
        raise ValueError("connector_search.cache_ttl must be a non-negative number")

    mailto = str(payload.get("mailto", "team@example.org"))

    return ConnectorSearchConfig(
        enabled_connectors=[str(e) for e in enabled],
        default_max_results=int(max_results),
        cache_ttl=float(cache_ttl),
        mailto=mailto,
        source_path=str(config_path),
    )


__all__ = ["ConnectorSearchConfig", "load_connector_search_config"]
