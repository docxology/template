"""No-mocks tests for the advanced exemplar's offline Stage 08 replay."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC = PROJECT_ROOT / "src"
REPO_ROOT = PROJECT_ROOT.parents[2]
for import_root in (REPO_ROOT, SRC):
    import_text = str(import_root)
    if import_text not in sys.path:
        sys.path.insert(0, import_text)

from infrastructure.search.deep_research import (  # noqa: E402
    DeepResearchRequest,
    DeepResearchResult,
)

from deep_research.dispatch import (  # noqa: E402
    default_fixture_path,
    dispatch_offline_replay,
)


def test_dispatch_writes_normalized_exoplanet_replay(tmp_path: Path) -> None:
    replay = dispatch_offline_replay(
        "Review exoplanet atmosphere evidence",
        tmp_path,
    )

    assert isinstance(replay.request, DeepResearchRequest)
    assert isinstance(replay.result, DeepResearchResult)
    assert replay.request.query == "Review exoplanet atmosphere evidence"
    assert replay.request.provider == "auto"
    assert replay.result.provider == "curated-fixture"
    assert replay.result.job_id == ""
    assert replay.result.status == "completed"
    assert replay.recorded_query.startswith("Survey robust evidence")
    assert len(replay.result.citations) == 2
    assert replay.output_path == tmp_path / "deep_research_replay.json"

    payload = json.loads(replay.output_path.read_text(encoding="utf-8"))
    assert payload["mode"] == "fixture-replay"
    assert payload["request"]["query"] == replay.request.query
    assert payload["report"]["citation_count"] == 2
    assert payload["report"]["query"] == replay.recorded_query
    assert payload["report"]["provider"] == "curated-fixture"
    assert set(payload["provider_profile"]["catalogue"]) == {"openai", "gemini"}


def test_default_fixture_is_tracked_exoplanet_evidence() -> None:
    fixture = default_fixture_path()
    payload = json.loads(fixture.read_text(encoding="utf-8"))

    assert fixture.is_file()
    assert "exoplanet" in payload["request"]["query"].lower()
    assert payload["output_text"]


def test_dispatch_accepts_explicit_recorded_report(tmp_path: Path) -> None:
    fixture = tmp_path / "recorded.json"
    fixture.write_text(
        json.dumps(
            {
                "provider": "gemini",
                "job_id": "offline-1",
                "status": "completed",
                "output_text": "Recorded output",
                "citations": [],
                "request": {"query": "Recorded query"},
            }
        ),
        encoding="utf-8",
    )

    replay = dispatch_offline_replay(
        "Current query",
        tmp_path / "out",
        fixture_path=fixture,
    )

    assert replay.result.provider == "gemini"
    assert replay.result.job_id == "offline-1"
    assert replay.recorded_query == "Recorded query"
    assert replay.result.citations == ()


def test_dispatch_fails_closed_when_fixture_is_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Replay fails closed"):
        dispatch_offline_replay(
            "query",
            tmp_path / "out",
            fixture_path=tmp_path / "missing.json",
        )
