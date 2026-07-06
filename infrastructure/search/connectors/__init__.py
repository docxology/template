"""Science-DB connector registry.

This package provides a registry of connectors for querying scientific
databases and repositories.  Each connector wraps one external data source
and returns normalised :class:`~infrastructure.search.connectors.types.ConnectorHit`
objects regardless of the underlying API.

Quick start::

    from infrastructure.search.connectors import search_connector, list_connectors

    # Search OpenAlex
    hits = search_connector("openalex", "CRISPR base editing", max_results=5)
    for h in hits:
        print(h.title, h.year)

    # List all available connectors
    for entry in list_connectors():
        print(entry.name, entry.domain.value)

The global registry is populated lazily on first import of this package.
"""

from __future__ import annotations

from infrastructure.search.connectors.config import ConnectorSearchConfig, load_connector_search_config
from infrastructure.search.connectors.http import ConnectorHttpClient, ConnectorHttpError
from infrastructure.search.connectors.registry import ConnectorRegistry
from infrastructure.search.connectors.types import (
    CatalogEntry,
    Connector,
    ConnectorDomain,
    ConnectorError,
    ConnectorHit,
    FetchOptions,
    SearchOptions,
)
from infrastructure.search.connectors.impl import (
    ArxivConnector,
    BiorxivConnector,
    CrossrefConnector,
    EuropePMCConnector,
    OpenAlexConnector,
    PDBConnector,
    SemanticScholarConnector,
    UniProtConnector,
    _ALL_CONNECTORS,
)

# ---------------------------------------------------------------------------
# Global registry
# ---------------------------------------------------------------------------

_REGISTRY: ConnectorRegistry | None = None


def get_registry() -> ConnectorRegistry:
    """Return the global connector registry, creating it on first call."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = ConnectorRegistry()
        for cls in _ALL_CONNECTORS:
            _REGISTRY.register(cls())
    return _REGISTRY


def reset_registry() -> None:
    """Reset the global registry (primarily for testing)."""
    global _REGISTRY
    _REGISTRY = None


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def list_connectors() -> list[CatalogEntry]:
    """Return a catalog of all registered connectors.

    Returns:
        A list of :class:`CatalogEntry` objects in registration order.
    """
    return get_registry().catalog()


def search_connector(
    connector_name: str,
    query: str,
    max_results: int = 10,
    year_min: int | None = None,
    year_max: int | None = None,
) -> list[ConnectorHit]:
    """Search a single named connector.

    Args:
        connector_name: Registry key, e.g. ``"openalex"``.
        query: Free-text search query.
        max_results: Maximum hits to return.
        year_min: Inclusive lower bound on publication year.
        year_max: Inclusive upper bound on publication year.

    Returns:
        List of :class:`ConnectorHit` objects.

    Raises:
        KeyError: If *connector_name* is not registered.
        ConnectorError: On transport failure.
    """
    reg = get_registry()
    connector = reg.get(connector_name)
    opts = SearchOptions(max_results=max_results, year_min=year_min, year_max=year_max)
    return connector.search(query, opts)


__all__ = [
    # Types
    "CatalogEntry",
    "Connector",
    "ConnectorDomain",
    "ConnectorError",
    "ConnectorHit",
    "FetchOptions",
    "SearchOptions",
    # HTTP
    "ConnectorHttpClient",
    "ConnectorHttpError",
    # Registry
    "ConnectorRegistry",
    # Config
    "ConnectorSearchConfig",
    "load_connector_search_config",
    # Implementations
    "ArxivConnector",
    "BiorxivConnector",
    "CrossrefConnector",
    "EuropePMCConnector",
    "OpenAlexConnector",
    "PDBConnector",
    "SemanticScholarConnector",
    "UniProtConnector",
    # Convenience
    "get_registry",
    "reset_registry",
    "list_connectors",
    "search_connector",
]
