"""Abstract literature-search backend contract."""

from __future__ import annotations

import abc

from infrastructure.search.literature.models import Paper, SearchQuery


class BackendError(RuntimeError):
    """Raised by a backend when the request itself fails (network, parse)."""


class SearchBackend(abc.ABC):
    """Abstract base class for literature-search backends."""

    name: str = "abstract"

    @abc.abstractmethod
    def search(self, query: SearchQuery) -> list[Paper]:
        """Run *query* against the backend and return a list of papers.

        Implementations must honour ``query.max_results``, apply year filters,
        stamp ``Paper.source = self.name``, return [] when nothing matches, and
        raise :class:`BackendError` on transport or parse failures.
        """


__all__ = ["BackendError", "SearchBackend"]
