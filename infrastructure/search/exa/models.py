"""Typed request/response models for the Exa search interfaces.

Every endpoint returns the same normalised :class:`ExaResult` record (mirroring
how the literature backends all emit a :class:`~infrastructure.search.literature.models.Paper`)
so downstream consumers treat ``/search``, ``/contents``, ``/findSimilar`` and
``/answer`` citations uniformly.

Wire payloads are camelCase (e.g. ``numResults``); the Python surface is
snake_case. ``build_contents_payload`` performs the one place where the two
conventions meet, and guards the documented "common mistakes" (content keys must
nest under ``contents``; ``category`` ``company``/``people`` reject domain and
date filters).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from infrastructure.search.exa.errors import ExaError

#: ``category`` values that reject ``excludeDomains`` and date filters (→ HTTP 400).
_FILTER_RESTRICTED_CATEGORIES = frozenset({"company", "people"})


@dataclass
class ExaResult:
    """A single Exa result, normalised across every endpoint.

    ``id`` is the stable Exa document id used to re-fetch via ``/contents``;
    ``url`` is the canonical landing page. Content fields (``text``,
    ``highlights``, ``summary``) are populated only when the request asked for
    them via the ``contents`` block.
    """

    id: str
    url: str | None = None
    title: str | None = None
    score: float | None = None
    published_date: str | None = None
    author: str | None = None
    text: str | None = None
    highlights: list[str] = field(default_factory=list)
    highlight_scores: list[float] = field(default_factory=list)
    summary: str | None = None
    image: str | None = None
    favicon: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ExaResult:
        return cls(
            id=str(data.get("id") or data.get("url") or ""),
            url=data.get("url"),
            title=data.get("title"),
            score=_as_float(data.get("score")),
            published_date=data.get("publishedDate"),
            author=data.get("author"),
            text=data.get("text"),
            highlights=list(data.get("highlights") or []),
            highlight_scores=[f for f in (_as_float(s) for s in data.get("highlightScores") or []) if f is not None],
            summary=data.get("summary"),
            image=data.get("image"),
            favicon=data.get("favicon"),
            extras=dict(data.get("extras") or {}),
            raw=dict(data),
        )


@dataclass
class Grounding:
    """Field-level citation record returned when ``outputSchema`` is used."""

    field: str
    citations: list[dict[str, Any]] = field(default_factory=list)
    confidence: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Grounding:
        return cls(
            field=str(data.get("field", "")),
            citations=list(data.get("citations") or []),
            confidence=data.get("confidence"),
        )


@dataclass
class SearchOutput:
    """Synthesised output from ``outputSchema`` searches (``output`` block)."""

    content: Any = None
    grounding: list[Grounding] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SearchOutput:
        return cls(
            content=data.get("content"),
            grounding=[Grounding.from_dict(g) for g in data.get("grounding") or []],
        )


@dataclass
class SearchResponse:
    """Response from ``POST /search`` (and ``/findSimilar``, same shape)."""

    results: list[ExaResult] = field(default_factory=list)
    request_id: str | None = None
    search_type: str | None = None
    output: SearchOutput | None = None
    cost_dollars: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SearchResponse:
        output = data.get("output")
        cost = data.get("costDollars")
        return cls(
            results=[ExaResult.from_dict(r) for r in data.get("results") or []],
            request_id=data.get("requestId"),
            search_type=data.get("searchType"),
            output=SearchOutput.from_dict(output) if isinstance(output, Mapping) else None,
            cost_dollars=_as_float(cost.get("total")) if isinstance(cost, Mapping) else _as_float(cost),
            raw=dict(data),
        )


@dataclass
class ContentsResponse:
    """Response from ``POST /contents``."""

    results: list[ExaResult] = field(default_factory=list)
    request_id: str | None = None
    cost_dollars: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ContentsResponse:
        cost = data.get("costDollars")
        return cls(
            results=[ExaResult.from_dict(r) for r in data.get("results") or []],
            request_id=data.get("requestId"),
            cost_dollars=_as_float(cost.get("total")) if isinstance(cost, Mapping) else _as_float(cost),
            raw=dict(data),
        )


@dataclass
class AnswerResponse:
    """Response from ``POST /answer`` — a grounded answer plus its citations."""

    answer: Any = None
    citations: list[ExaResult] = field(default_factory=list)
    request_id: str | None = None
    cost_dollars: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AnswerResponse:
        cost = data.get("costDollars")
        return cls(
            answer=data.get("answer"),
            citations=[ExaResult.from_dict(c) for c in data.get("citations") or []],
            request_id=data.get("requestId"),
            cost_dollars=_as_float(cost.get("total")) if isinstance(cost, Mapping) else _as_float(cost),
            raw=dict(data),
        )


def build_contents_payload(
    *,
    highlights: bool | Mapping[str, Any] | None = None,
    text: bool | Mapping[str, Any] | None = None,
    summary: bool | Mapping[str, Any] | None = None,
    max_age_hours: int | None = None,
    livecrawl_timeout: int | None = None,
    subpages: int | None = None,
) -> dict[str, Any]:
    """Build the nested ``contents`` object from snake_case kwargs.

    Returns ``{}`` when nothing was requested so callers can drop the key. Note
    the guide's guardrail: content keys must NEVER appear at the top level of a
    ``/search`` body — only inside this object.
    """
    contents: dict[str, Any] = {}
    if highlights is not None:
        contents["highlights"] = highlights
    if text is not None:
        contents["text"] = text
    if summary is not None:
        contents["summary"] = summary
    if max_age_hours is not None:
        contents["maxAgeHours"] = max_age_hours
    if livecrawl_timeout is not None:
        contents["livecrawlTimeout"] = livecrawl_timeout
    if subpages is not None:
        contents["subpages"] = subpages
    return contents


def validate_search_request(
    *,
    category: str | None,
    exclude_domains: Sequence[str] | None,
    start_published_date: str | None,
    end_published_date: str | None,
) -> None:
    """Fail fast on the documented ``category`` filter conflict (HTTP 400).

    ``company`` and ``people`` categories reject ``excludeDomains`` and date
    filters; catching it here gives a clear error instead of a server 400.
    """
    if category in _FILTER_RESTRICTED_CATEGORIES and (exclude_domains or start_published_date or end_published_date):
        raise ExaError(
            f"category={category!r} does not support excludeDomains or date filters "
            "(Exa returns HTTP 400); drop those filters or change the category"
        )


def prune(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Drop ``None`` values and empty ``contents``/collections from a payload."""
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if value is None:
            continue
        if key == "contents" and not value:
            continue
        out[key] = value
    return out


def _as_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


__all__ = [
    "AnswerResponse",
    "ContentsResponse",
    "ExaResult",
    "Grounding",
    "SearchOutput",
    "SearchResponse",
    "build_contents_payload",
    "prune",
    "validate_search_request",
]
