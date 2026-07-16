"""Provider-neutral, offline deep-research replay orchestration.

Live deep-research jobs are paid and non-deterministic. This module therefore
constructs the genuine infrastructure request model but only replays a tracked
report fixture. The numbered Stage 08 script is a CLI boundary over this
source-level behavior.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.search.deep_research import (
    DEFAULT_GEMINI_AGENT,
    DEFAULT_OPENAI_MODEL,
    DeepResearchCitation,
    DeepResearchClient,
    DeepResearchConfig,
    DeepResearchRequest,
    DeepResearchResult,
)

PROVIDER_CATALOGUE: tuple[str, ...] = ("openai", "gemini")


@dataclass(frozen=True)
class DeepResearchReplay:
    """Completed offline replay and the artifact written for later stages."""

    provider_profile: dict[str, Any]
    request: DeepResearchRequest
    result: DeepResearchResult
    recorded_query: str
    output_path: Path


def default_fixture_path() -> Path:
    """Return the tracked exoplanet-atmosphere report fixture."""
    return Path(__file__).resolve().parent / "fixtures" / "recorded_report.json"


def _provider_profile() -> dict[str, Any]:
    """Describe configured providers without performing a network call."""
    config = DeepResearchConfig.from_env()
    client = DeepResearchClient(config)
    return {
        "catalogue": list(PROVIDER_CATALOGUE),
        "available": list(client.available_providers()),
        "openai_model": config.openai_model or DEFAULT_OPENAI_MODEL,
        "gemini_agent": config.gemini_agent or DEFAULT_GEMINI_AGENT,
    }


def _load_recorded_result(path: Path) -> tuple[DeepResearchResult, str]:
    """Normalize one fixture through the real infrastructure result model."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Recorded deep-research fixture not found: {path}. Replay fails closed; supply a recorded report."
        )
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    citations = tuple(
        DeepResearchCitation(
            title=item.get("title"),
            url=item.get("url"),
            start_index=item.get("start_index"),
            end_index=item.get("end_index"),
            text=item.get("text"),
            metadata=dict(item.get("metadata", {})),
        )
        for item in payload.get("citations", [])
    )
    result = DeepResearchResult(
        provider=str(payload["provider"]),
        job_id=str(payload.get("job_id", "")),
        status=str(payload.get("status", "completed")),
        output_text=str(payload.get("output_text", "")),
        citations=citations,
        trace=tuple(payload.get("trace", ())),
        raw=dict(payload.get("raw", {})),
    )
    request = payload.get("request", {}) or {}
    return result, str(request.get("query", ""))


def dispatch_offline_replay(
    query: str,
    output_dir: Path,
    *,
    fixture_path: Path | None = None,
) -> DeepResearchReplay:
    """Build a real request, replay a fixture, and persist normalized evidence."""
    profile = _provider_profile()
    request = DeepResearchRequest(query=query, provider="auto")
    result, recorded_query = _load_recorded_result(fixture_path if fixture_path is not None else default_fixture_path())
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "deep_research_replay.json"
    payload = {
        "mode": "fixture-replay",
        "provider_profile": profile,
        "request": {"query": request.query, "provider": request.provider},
        "report": {
            "provider": result.provider,
            "job_id": result.job_id,
            "status": result.status,
            "query": recorded_query,
            "output_chars": len(result.output_text),
            "citation_count": len(result.citations),
            "citations": [{"title": citation.title, "url": citation.url} for citation in result.citations],
        },
    }
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return DeepResearchReplay(
        provider_profile=profile,
        request=request,
        result=result,
        recorded_query=recorded_query,
        output_path=output_path,
    )


__all__ = [
    "PROVIDER_CATALOGUE",
    "DeepResearchReplay",
    "default_fixture_path",
    "dispatch_offline_replay",
]
