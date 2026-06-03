"""``/contents`` interface — clean parsed content for URLs you already have.

Use this when URLs come from another source (a database, RSS, prior search
``id``s) or when you need to refresh stale content via ``max_age_hours``. On
``/contents`` the content keys (``highlights``/``text``/``summary``) are
top-level — unlike ``/search`` where they nest under ``contents``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Sequence

from infrastructure.search.exa.errors import ExaError
from infrastructure.search.exa.models import ContentsResponse, prune

if TYPE_CHECKING:  # pragma: no cover
    from infrastructure.search.exa.client import ExaClient


class ExaContentsInterface:
    """Wraps ``POST /contents``."""

    path = "/contents"

    def __init__(self, client: ExaClient) -> None:
        self._client = client

    def get(
        self,
        urls: str | Sequence[str],
        *,
        highlights: bool | Mapping[str, Any] | None = None,
        text: bool | Mapping[str, Any] | None = None,
        summary: bool | Mapping[str, Any] | None = None,
        max_age_hours: int | None = None,
        livecrawl_timeout: int | None = None,
        subpages: int | None = None,
    ) -> ContentsResponse:
        """Fetch content for one or more URLs (or Exa result ``id``s).

        Defaults to highlights when no content mode is given. Raises
        :class:`ExaError` when no URLs are supplied.
        """
        url_list = [urls] if isinstance(urls, str) else list(urls)
        url_list = [u for u in url_list if u and u.strip()]
        if not url_list:
            raise ExaError("contents requires at least one non-empty URL")
        if highlights is None and text is None and summary is None:
            highlights = True
        payload = prune(
            {
                "urls": url_list,
                "highlights": highlights,
                "text": text,
                "summary": summary,
                "maxAgeHours": max_age_hours,
                "livecrawlTimeout": livecrawl_timeout,
                "subpages": subpages,
            }
        )
        return ContentsResponse.from_dict(self._client.request(self.path, payload))


__all__ = ["ExaContentsInterface"]
