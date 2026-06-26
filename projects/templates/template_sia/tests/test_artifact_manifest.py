"""Tests for artifact manifest writer."""

from __future__ import annotations

import json
from pathlib import Path

from src.artifact_manifest import (
    ArtifactManifestEntry,
    collect_run_artifact_paths,
    compute_sha256,
    write_artifact_manifest,
)
from src.loop import run_sia_loop_project

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_collect_run_artifact_paths_after_loop():
    run_sia_loop_project(PROJECT_ROOT, live=False)
    paths = collect_run_artifact_paths(PROJECT_ROOT, run_id=1)
    assert any(path.name == "run_summary.json" for path in paths)
    manifest_path = write_artifact_manifest(PROJECT_ROOT, paths)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["entries"]
    rel_paths = {entry["path"] for entry in payload["entries"]}
    assert "output/runs/run_1/run_summary.json" in rel_paths
    assert "output/reports/artifact_manifest.json" not in rel_paths


def test_write_artifact_manifest_deduplicates_paths(tmp_path: Path) -> None:
    """Passing the same path twice must yield only one manifest entry."""
    present = tmp_path / "output" / "data" / "vars.json"
    present.parent.mkdir(parents=True)
    present.write_text("{}", encoding="utf-8")
    manifest_path = write_artifact_manifest(tmp_path, [present, present])
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    rel_paths = [entry["path"] for entry in payload["entries"]]
    assert rel_paths.count("output/data/vars.json") == 1


def test_write_artifact_manifest_outside_root_path(tmp_path: Path) -> None:
    """A path outside the project root is stored as an absolute string (not relative)."""
    # This exercises the except ValueError branch in _relative_path.
    outside = tmp_path / "outside_root.json"
    outside.write_text("{}", encoding="utf-8")
    project = tmp_path / "project"
    project.mkdir()
    manifest_path = write_artifact_manifest(project, [outside])
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    # The entry is still recorded — just with a non-relative path string.
    assert len(payload["entries"]) == 1
    # The path stored must be the absolute string, not a relative one.
    stored = payload["entries"][0]["path"]
    assert stored == str(outside)


def test_compute_sha256_deterministic(tmp_path: Path) -> None:
    """SHA-256 of the same content is stable across calls."""
    f = tmp_path / "data.txt"
    f.write_text("hello world", encoding="utf-8")
    assert compute_sha256(f) == compute_sha256(f)
    # Known SHA-256 for b"hello world"
    import hashlib
    expected = hashlib.sha256(b"hello world").hexdigest()
    assert compute_sha256(f) == expected


def test_artifact_manifest_entry_timestamp_set() -> None:
    """ArtifactManifestEntry auto-populates a non-empty ISO timestamp."""
    entry = ArtifactManifestEntry(
        path="output/foo.json",
        size_bytes=10,
        sha256="abc",
        stage_num=1,
        stage_name="test",
        contract_match=True,
    )
    assert entry.timestamp  # non-empty
    assert "T" in entry.timestamp  # ISO format contains T separator
