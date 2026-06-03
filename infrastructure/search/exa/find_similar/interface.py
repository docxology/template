"""``/findSimilar`` interface — semantically similar pages for a seed URL.

Returns the same :class:`~infrastructure.search.exa.models.SearchResponse` shape
as ``/search``; the difference is the query is a URL rather than free text.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Sequence

from infrastructure.search.exa.errors import ExaError
from infrastructure.search.exa.models import (
    SearchResponse,
    build_contents_payload,
    prune,
)

if TYPE_CHECKING:  # pragma: no cover
    from infrastructure.search.exa.client import ExaClient


class ExaFindSimilarInterface:
    """Wraps ``POST /findSimilar``."""

    # Exa's live REST path is camelCase ``/findSimilar``; the kebab-case
    # ``/find-similar`` form returns HTTP 404 (verified against the live API).
    path = "/findSimilar"

    def __init__(self, client: ExaClient) -> None:
        self._client = client

    def find_similar(
        self,
        url: str,
        *,
        num_results: int | None = None,
        include_domains: Sequence[str] | None = None,
        exclude_domains: Sequence[str] | None = None,
        start_published_date: str | None = None,
        end_published_date: str | None = None,
        exclude_source_domain: bool | None = None,
        highlights: bool | Mapping[str, Any] | None = None,
        text: bool | Mapping[str, Any] | None = None,
        summary: bool | Mapping[str, Any] | None = None,
        max_age_hours: int | None = None,
    ) -> SearchResponse:
        """Find pages similar to ``url``.

        Defaults to highlights when no content mode is requested. Raises
        :class:`ExaError` on an empty URL.
        """
        if not url or not url.strip():
            raise ExaError("find_similar requires a non-empty seed URL")
        if highlights is None and text is None and summary is None:
            highlights = True
        payload = prune(
            {
                "url": url,
                "numResults": num_results,
                "includeDomains": list(include_domains) if include_domains else None,
                "excludeDomains": list(exclude_domains) if exclude_domains else None,
                "startPublishedDate": start_published_date,
                "endPublishedDate": end_published_date,
                "excludeSourceDomain": exclude_source_domain,
                "contents": build_contents_payload(
                    highlights=highlights,
                    text=text,
                    summary=summary,
                    max_age_hours=max_age_hours,
                ),
            }
        )
        return SearchResponse.from_dict(self._client.request(self.path, payload))


__all__ = ["ExaFindSimilarInterface"]
