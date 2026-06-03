"""``/search`` interface — Exa's primary neural/keyword search endpoint.

Covers raw retrieval (``results`` + ``highlights``) and synthesised structured
output (``outputSchema`` + ``systemPrompt``). All wire fields are camelCase; the
Python surface is snake_case and ``None`` arguments are pruned from the body.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Sequence

from infrastructure.search.exa.config import VALID_SEARCH_TYPES
from infrastructure.search.exa.errors import ExaError
from infrastructure.search.exa.models import (
    SearchResponse,
    build_contents_payload,
    prune,
    validate_search_request,
)

if TYPE_CHECKING:  # pragma: no cover
    from infrastructure.search.exa.client import ExaClient


class ExaSearchInterface:
    """Wraps ``POST /search``."""

    path = "/search"

    def __init__(self, client: ExaClient) -> None:
        self._client = client

    def search(
        self,
        query: str,
        *,
        type: str | None = None,
        num_results: int | None = None,
        category: str | None = None,
        user_location: str | None = None,
        include_domains: Sequence[str] | None = None,
        exclude_domains: Sequence[str] | None = None,
        start_published_date: str | None = None,
        end_published_date: str | None = None,
        moderation: bool | None = None,
        # content retrieval (nested under `contents`)
        highlights: bool | Mapping[str, Any] | None = None,
        text: bool | Mapping[str, Any] | None = None,
        summary: bool | Mapping[str, Any] | None = None,
        max_age_hours: int | None = None,
        livecrawl_timeout: int | None = None,
        subpages: int | None = None,
        # synthesised structured output
        output_schema: Mapping[str, Any] | None = None,
        system_prompt: str | None = None,
        additional_queries: Sequence[str] | None = None,
    ) -> SearchResponse:
        """Run a search.

        Defaults to raw retrieval with highlights (the token-efficient mode the
        coding-agent guide recommends). Pass ``output_schema`` to get Exa to
        synthesise grounded JSON in ``response.output``.

        Raises:
            ExaError: empty query, invalid ``type``, or a ``category`` that
                conflicts with the requested filters.
        """
        if not query or not query.strip():
            raise ExaError("search query must be a non-empty string")
        resolved_type = type or self._client.config.default_type
        if resolved_type not in VALID_SEARCH_TYPES:
            raise ExaError(f"invalid type {resolved_type!r}; expected one of {sorted(VALID_SEARCH_TYPES)}")
        validate_search_request(
            category=category,
            exclude_domains=exclude_domains,
            start_published_date=start_published_date,
            end_published_date=end_published_date,
        )
        # Default to highlights when no content mode was requested at all.
        if highlights is None and text is None and summary is None:
            highlights = True
        payload = prune(
            {
                "query": query,
                "type": resolved_type,
                "numResults": num_results,
                "category": category,
                "userLocation": user_location,
                "includeDomains": list(include_domains) if include_domains else None,
                "excludeDomains": list(exclude_domains) if exclude_domains else None,
                "startPublishedDate": start_published_date,
                "endPublishedDate": end_published_date,
                "moderation": moderation,
                "outputSchema": dict(output_schema) if output_schema else None,
                "systemPrompt": system_prompt,
                "additionalQueries": list(additional_queries) if additional_queries else None,
                "contents": build_contents_payload(
                    highlights=highlights,
                    text=text,
                    summary=summary,
                    max_age_hours=max_age_hours,
                    livecrawl_timeout=livecrawl_timeout,
                    subpages=subpages,
                ),
            }
        )
        return SearchResponse.from_dict(self._client.request(self.path, payload))


__all__ = ["ExaSearchInterface"]
