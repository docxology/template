"""Offline adapter over ``infrastructure.search.deep_research``.

Deep research (OpenAI / Gemini deep-research agents) is a **paid,
non-deterministic** capability. To keep this public exemplar CI-safe and
reproducible, the adapter exposes two deterministic, offline-only entry points:

* :func:`list_provider_profile` / :func:`build_offline_request` — construct the
  *real* provider-neutral request objects from
  :mod:`infrastructure.search.deep_research` (no network, no key required), so
  the template ships a clonable, type-checked call-site for live dispatch.
* :func:`replay_recorded_report` — load a recorded deep-research report fixture
  (JSON) and return a normalized result built from the real
  :class:`DeepResearchResult` model. Fails **closed** (raises) when the fixture
  is missing — it never fabricates a passing run.

This mirrors the fixture-replay idiom used by ``template_sia``: a single,
deterministic replay path that exercises the genuine infrastructure surface
without implying live, billed execution in CI.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Real, exported infrastructure symbols (see
# ``infrastructure/search/deep_research/__init__.py`` ``__all__``).
from infrastructure.search.deep_research import (
    DEFAULT_GEMINI_AGENT,
    DEFAULT_OPENAI_MODEL,
    DeepResearchCitation,
    DeepResearchClient,
    DeepResearchConfig,
    DeepResearchRequest,
    DeepResearchResult,
)

#: Providers the infrastructure package can dispatch to, independent of which
#: API keys happen to be configured in the current environment.
PROVIDER_CATALOGUE: tuple[str, ...] = ("openai", "gemini")

#: Filename of the recorded report shipped alongside this module.
_FIXTURE_NAME = "recorded_report.json"


def default_fixture_path() -> Path:
    """Return the path to the recorded deep-research report bundled here."""
    return Path(__file__).resolve().parent / "fixtures" / _FIXTURE_NAME


def list_provider_profile() -> dict[str, Any]:
    """Describe deep-research providers without performing any network call.

    ``catalogue`` is the static set of dispatchable providers;
    ``available`` reflects which ones have keys configured in this environment
    (empty in CI, which is expected and CI-safe).
    """
    config = DeepResearchConfig.from_env()
    client = DeepResearchClient(config)
    return {
        "catalogue": list(PROVIDER_CATALOGUE),
        "available": list(client.available_providers()),
        "openai_model": config.openai_model or DEFAULT_OPENAI_MODEL,
        "gemini_agent": config.gemini_agent or DEFAULT_GEMINI_AGENT,
    }


def build_offline_request(query: str, *, provider: str = "auto") -> DeepResearchRequest:
    """Build a real provider-neutral :class:`DeepResearchRequest`.

    No network, no key required — this is the request a live ``submit`` would
    dispatch. Kept tiny so cloners can see exactly how the project's own query
    maps onto the infrastructure request model.
    """
    return DeepResearchRequest(query=query, provider=provider)


@dataclass(frozen=True)
class ReplayedReport:
    """Normalized, deterministic view of a recorded deep-research report."""

    provider: str
    job_id: str
    status: str
    query: str
    output_text: str
    citations: tuple[dict[str, str | None], ...]
    result: DeepResearchResult

    @property
    def citation_count(self) -> int:
        return len(self.citations)


def _citation_from_payload(item: dict[str, Any]) -> DeepResearchCitation:
    return DeepResearchCitation(
        title=item.get("title"),
        url=item.get("url"),
        start_index=item.get("start_index"),
        end_index=item.get("end_index"),
        text=item.get("text"),
        metadata=dict(item.get("metadata", {})),
    )


def replay_recorded_report(fixture_path: Path | str | None = None) -> ReplayedReport:
    """Load a recorded report fixture and return a normalized result.

    Args:
        fixture_path: Optional explicit fixture file. Defaults to the recorded
            report shipped with this module.

    Raises:
        FileNotFoundError: If the fixture is absent. Replay fails closed; it
            never fabricates a passing run.
    """
    path = Path(fixture_path) if fixture_path is not None else default_fixture_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"Recorded deep-research fixture not found: {path}. "
            "Replay fails closed; supply a recorded report or run a live dispatch."
        )

    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    citations = tuple(_citation_from_payload(c) for c in payload.get("citations", []))

    result = DeepResearchResult(
        provider=str(payload["provider"]),
        job_id=str(payload.get("job_id", "")),
        status=str(payload.get("status", "completed")),
        output_text=str(payload.get("output_text", "")),
        citations=citations,
        trace=tuple(payload.get("trace", ())),
        raw=dict(payload.get("raw", {})),
    )
    request_meta = payload.get("request", {}) or {}
    normalized_citations = tuple(
        {"title": c.title, "url": c.url} for c in result.citations
    )
    return ReplayedReport(
        provider=result.provider,
        job_id=result.job_id,
        status=result.status,
        query=str(request_meta.get("query", "")),
        output_text=result.output_text,
        citations=normalized_citations,
        result=result,
    )


__all__ = [
    "DeepResearchClient",
    "DeepResearchConfig",
    "DeepResearchRequest",
    "DeepResearchResult",
    "PROVIDER_CATALOGUE",
    "ReplayedReport",
    "build_offline_request",
    "default_fixture_path",
    "list_provider_profile",
    "replay_recorded_report",
]
