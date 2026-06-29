#!/usr/bin/env python3
"""No-mocks tests for the deep-research fixture-replay adapter.

This exemplar demonstrates ``infrastructure.search.deep_research`` wiring
*offline*: ``deep_research`` is a PAID, non-deterministic capability, so the
public template exercises only its provider-neutral request construction and a
recorded-report replay path. Mirrors the fixture-replay idiom used by
``template_sia`` (recorded artifacts, fail-closed when missing, no network).

No mocks: every assertion runs the real adapter over the real shipped fixture
file and the real infrastructure dataclasses.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deep_research.deep_research_adapter import (
    ReplayedReport,
    build_offline_request,
    default_fixture_path,
    list_provider_profile,
    replay_recorded_report,
)


def test_adapter_imports_real_infrastructure_symbols() -> None:
    """The adapter must wire to the genuine infrastructure package, not a stub."""
    import deep_research.deep_research_adapter as adapter
    from infrastructure.search.deep_research import (
        DeepResearchConfig,
        DeepResearchRequest,
        DeepResearchResult,
    )

    # Real classes, re-exported via the adapter module namespace.
    assert adapter.DeepResearchConfig is DeepResearchConfig
    assert adapter.DeepResearchRequest is DeepResearchRequest
    assert adapter.DeepResearchResult is DeepResearchResult


def test_provider_profile_returns_non_empty_structure() -> None:
    """Provider listing returns a structured, non-empty catalogue offline."""
    profile = list_provider_profile()

    assert isinstance(profile, dict)
    # Catalogue of providers the package can dispatch to (independent of keys).
    assert profile["catalogue"], "expected a non-empty provider catalogue"
    assert set(profile["catalogue"]) == {"openai", "gemini"}
    # Default model/agent come straight from infrastructure defaults.
    assert profile["openai_model"]
    assert profile["gemini_agent"]
    # "available" depends on env keys; offline in CI it is a (possibly empty) list.
    assert isinstance(profile["available"], list)


def test_build_offline_request_is_provider_neutral() -> None:
    """The adapter builds a real DeepResearchRequest from project inputs."""
    request = build_offline_request("Survey of modafinil cognitive effects")

    from infrastructure.search.deep_research import DeepResearchRequest

    assert isinstance(request, DeepResearchRequest)
    assert request.query == "Survey of modafinil cognitive effects"
    assert request.provider == "auto"
    assert request.output_format == "markdown"
    # Sources default to web-enabled and at least one supported source.
    assert request.sources.has_supported_source()


def test_default_fixture_path_exists_and_is_json() -> None:
    """The recorded fixture ships inside the template and is valid JSON."""
    fixture = default_fixture_path()

    assert fixture.is_file(), f"recorded fixture missing: {fixture}"
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    assert payload["provider"] in {"openai", "gemini"}
    assert payload["output_text"]


def test_replay_returns_normalized_fields_from_real_fixture() -> None:
    """Replay loads the shipped fixture and normalizes the recorded report."""
    report = replay_recorded_report()

    assert isinstance(report, ReplayedReport)
    assert report.provider in {"openai", "gemini"}
    assert report.status == "completed"
    assert report.output_text.strip()
    assert report.query  # carried from the recorded request
    # Citations normalized into title/url pairs.
    assert report.citation_count == len(report.citations)
    assert report.citation_count >= 1
    first = report.citations[0]
    assert "title" in first and "url" in first
    # The normalized result round-trips through the real DeepResearchResult model.
    from infrastructure.search.deep_research import DeepResearchResult

    assert isinstance(report.result, DeepResearchResult)
    assert report.result.output_text == report.output_text


def test_replay_accepts_explicit_fixture_path(tmp_path: Path) -> None:
    """Replay works against a caller-supplied recorded report on disk."""
    recorded = {
        "provider": "gemini",
        "job_id": "job-test-001",
        "status": "completed",
        "output_text": "## Executive Summary\nSynthetic offline report.",
        "citations": [
            {"title": "Example Source", "url": "https://example.org/a"},
        ],
        "trace": [],
        "raw": {},
        "request": {"query": "offline replay probe", "provider": "gemini"},
    }
    fixture = tmp_path / "recorded.json"
    fixture.write_text(json.dumps(recorded), encoding="utf-8")

    report = replay_recorded_report(fixture)

    assert report.provider == "gemini"
    assert report.query == "offline replay probe"
    assert report.citation_count == 1


def test_replay_fails_closed_when_fixture_missing(tmp_path: Path) -> None:
    """Replay raises (never fabricates) when the recorded report is absent."""
    missing = tmp_path / "does_not_exist.json"

    with pytest.raises(FileNotFoundError):
        replay_recorded_report(missing)
