"""Base class for connector implementations."""

from __future__ import annotations

from infrastructure.search.connectors.http import ConnectorHttpClient
from infrastructure.search.connectors.types import (
    ConnectorDomain,
    ConnectorHit,
    FetchOptions,
    SearchOptions,
)

__all__ = ["BaseConnector"]


class BaseConnector:
    """Mixin providing a shared HTTP client and catalog metadata.

    Subclasses must set class-level ``id``, ``name``, ``domain``,
    ``description``, and optionally ``homepage`` as class attributes,
    then implement ``search`` and ``fetch``.
    """

    id: str
    name: str
    domain: ConnectorDomain
    description: str = ""
    homepage: str | None = None

    def __init__(
        self,
        http: ConnectorHttpClient | None = None,
    ) -> None:
        self._http = http if http is not None else ConnectorHttpClient()

    def search(
        self,
        query: str,
        opts: SearchOptions | None = None,
    ) -> list[ConnectorHit]:  # pragma: no cover
        """Search for results matching a query."""
        raise NotImplementedError

    def fetch(
        self,
        record_id: str,
        opts: FetchOptions | None = None,
    ) -> object:  # pragma: no cover
        """Fetch a resource by identifier."""
        raise NotImplementedError
