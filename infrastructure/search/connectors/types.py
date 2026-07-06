"""Type definitions for the science-DB connector registry.

Defines the core domain taxonomy, data models, and the Connector protocol
that every concrete connector implementation must satisfy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class ConnectorDomain(str, Enum):
    """Scientific domain taxonomy for connector classification."""

    biology = "biology"
    chemistry = "chemistry"
    physics = "physics"
    genomics = "genomics"
    proteomics = "proteomics"
    structure = "structure"
    literature = "literature"
    materials = "materials"
    clinical = "clinical"
    general = "general"


@dataclass(frozen=True)
class ConnectorHit:
    """A single normalised result returned by a connector search.

    Attributes:
        id: Source-prefixed unique identifier, e.g. ``"openalex:W2741809807"``.
        title: Title of the record.
        authors: Ordered display-name list.
        year: Four-digit publication year, or ``None`` if unknown.
        doi: DOI without ``https://doi.org/`` prefix, or ``None``.
        url: Canonical landing URL, or ``None``.
        abstract: Abstract text, or ``None``.
        source: Short name of the connector that produced this hit.
        score: Backend-reported relevance score in ``[0, 1]``.  Defaults to
            ``0.0`` when the backend provides no score.
        extra: Backend-specific metadata preserved for debugging.
    """

    id: str
    title: str
    authors: tuple[str, ...] = field(default_factory=tuple)
    year: int | None = None
    doi: str | None = None
    url: str | None = None
    abstract: str | None = None
    source: str = ""
    score: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-safe mapping."""
        return {
            "id": self.id,
            "title": self.title,
            "authors": list(self.authors),
            "year": self.year,
            "doi": self.doi,
            "url": self.url,
            "abstract": self.abstract,
            "source": self.source,
            "score": self.score,
            "extra": self.extra,
        }


@dataclass(frozen=True)
class CatalogEntry:
    """Describes a registered connector in the catalog.

    Attributes:
        name: Unique registry key (lowercase, hyphens/underscores).
        domain: Primary scientific domain.
        description: One-line human description.
        base_url: Canonical API base URL.
        supports_fetch: Whether the connector implements :meth:`Connector.fetch`.
    """

    name: str
    domain: ConnectorDomain
    description: str
    base_url: str
    supports_fetch: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-safe mapping."""
        return {
            "name": self.name,
            "domain": self.domain.value,
            "description": self.description,
            "base_url": self.base_url,
            "supports_fetch": self.supports_fetch,
        }


@dataclass
class SearchOptions:
    """Options controlling a connector :meth:`~Connector.search` call.

    Attributes:
        max_results: Upper bound on results to return.  Individual connectors
            may return fewer if the API caps at a lower limit.
        year_min: Inclusive lower bound on publication year.
        year_max: Inclusive upper bound on publication year.
        extra: Pass-through mapping of connector-specific parameters.
    """

    max_results: int = 10
    year_min: int | None = None
    year_max: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class FetchOptions:
    """Options controlling a connector :meth:`~Connector.fetch` call.

    Attributes:
        include_abstract: Request abstract text even if the default response
            omits it (some APIs require an extra round-trip).
        extra: Pass-through mapping of connector-specific parameters.
    """

    include_abstract: bool = True
    extra: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Connector(Protocol):
    """Protocol that every science-DB connector must satisfy.

    Connectors are stateless, side-effect-free objects that wrap a single
    external data source.  Implementations *must* define the three class-level
    attributes and implement :meth:`search`; :meth:`fetch` is optional.
    """

    #: Unique registry key — passed to :class:`ConnectorRegistry.register`.
    name: str
    #: Primary scientific domain.
    domain: ConnectorDomain
    #: One-line human description.
    description: str

    def search(
        self,
        query: str,
        options: SearchOptions | None = None,
    ) -> list[ConnectorHit]:
        """Search this data source and return normalised hits.

        Args:
            query: Free-text search string.
            options: Optional search parameters.

        Returns:
            A list of :class:`ConnectorHit` objects, sorted by
            descending relevance when possible.

        Raises:
            ConnectorError: On transport or protocol failure.
        """
        ...

    def fetch(
        self,
        record_id: str,
        options: FetchOptions | None = None,
    ) -> ConnectorHit | None:
        """Fetch a single record by its source-specific identifier.

        Args:
            record_id: The ``id`` field from a previous :meth:`search` hit
                (source-prefixed), or a raw external identifier.
            options: Optional fetch parameters.

        Returns:
            A single :class:`ConnectorHit`, or ``None`` when the record is
            not found.

        Raises:
            ConnectorError: On transport or protocol failure.
        """
        ...


class ConnectorError(Exception):
    """Raised by connectors on transport or protocol failure."""


__all__ = [
    "ConnectorDomain",
    "ConnectorError",
    "ConnectorHit",
    "CatalogEntry",
    "SearchOptions",
    "FetchOptions",
    "Connector",
]
