"""Offline transcript replay and stale-fixture contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.transcript import replay_transcript, transcript_digest, validate_transcript


FIXTURE = Path(__file__).resolve().parents[1] / "data" / "transcript_fixture.json"


def test_fixture_is_replayable_offline() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert validate_transcript(payload, expected_revision="fixture-2026-08-09-v1") == []
    assert len(replay_transcript(FIXTURE, expected_revision="fixture-2026-08-09-v1")) == 3


def test_revision_drift_is_rejected() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    issues = validate_transcript(payload, expected_revision="fixture-older")
    assert any("stale transcript revision" in issue for issue in issues)


def test_network_mode_is_not_an_offline_replay() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["mode"] = "live"
    assert any("mode=offline" in issue for issue in validate_transcript(payload))


def test_malformed_entry_fails_closed(tmp_path: Path) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["entries"][0].pop("content")
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid transcript"):
        replay_transcript(path, expected_revision="fixture-2026-08-09-v1")


def test_transcript_digest_changes_on_revision_drift() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    changed = dict(payload)
    changed["revision"] = "fixture-2026-08-09-v2"
    assert transcript_digest(payload) != transcript_digest(changed)
