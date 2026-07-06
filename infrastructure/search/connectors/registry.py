"""Connector registry — maps names and domains to connector instances."""

from __future__ import annotations

from typing import Iterator

from infrastructure.search.connectors.types import (
    CatalogEntry,
    Connector,
    ConnectorDomain,
)


class ConnectorRegistry:
    """Central registry of science-DB connectors.

    Usage::

        registry = ConnectorRegistry()
        registry.register(OpenAlexConnector())
        connector = registry.get("openalex")
        bio_connectors = registry.by_domain(ConnectorDomain.biology)

    The registry is *not* a singleton; callers that want a shared global
    instance should use :func:`infrastructure.search.connectors.get_registry`.
    """

    def __init__(self) -> None:
        self._store: dict[str, Connector] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def register(self, connector: Connector) -> None:
        """Register *connector* under its :attr:`~Connector.name`.

        Args:
            connector: Any object that satisfies the
                :class:`~infrastructure.search.connectors.types.Connector`
                protocol.

        Raises:
            ValueError: When a connector with the same name is already
                registered.
        """
        if not hasattr(connector, "name") or not connector.name:
            raise ValueError("Connector must have a non-empty `name` attribute")
        if connector.name in self._store:
            raise ValueError(
                f"Connector '{connector.name}' is already registered. "
                "Use replace=True to overwrite or deregister first."
            )
        self._store[connector.name] = connector

    def deregister(self, name: str) -> None:
        """Remove the connector registered under *name*.

        Args:
            name: Connector key.

        Raises:
            KeyError: When *name* is not registered.
        """
        if name not in self._store:
            raise KeyError(f"No connector registered as '{name}'")
        del self._store[name]

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get(self, name: str) -> Connector:
        """Return the connector registered under *name*.

        Args:
            name: Connector key.

        Raises:
            KeyError: When *name* is not registered.
        """
        try:
            return self._store[name]
        except KeyError:
            raise KeyError(f"No connector registered as '{name}'. Available: {sorted(self._store)}") from None

    def has(self, name: str) -> bool:
        """Return ``True`` when *name* is registered."""
        return name in self._store

    def all(self) -> list[Connector]:  # noqa: A003
        """Return all registered connectors in insertion order."""
        return list(self._store.values())

    def by_domain(self, domain: ConnectorDomain) -> list[Connector]:
        """Return connectors whose primary domain matches *domain*."""
        return [c for c in self._store.values() if c.domain == domain]

    def catalog(self) -> list[CatalogEntry]:
        """Return a :class:`CatalogEntry` for every registered connector."""
        entries: list[CatalogEntry] = []
        for connector in self._store.values():
            supports_fetch = callable(getattr(connector, "fetch", None))
            entries.append(
                CatalogEntry(
                    name=connector.name,
                    domain=connector.domain,
                    description=connector.description,
                    base_url=getattr(connector, "base_url", ""),
                    supports_fetch=supports_fetch,
                )
            )
        return entries

    def __iter__(self) -> Iterator[Connector]:
        return iter(self._store.values())

    def __len__(self) -> int:
        return len(self._store)

    def __repr__(self) -> str:
        names = sorted(self._store)
        return f"{self.__class__.__name__}({names!r})"


__all__ = ["ConnectorRegistry"]
