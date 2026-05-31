"""Tests for artifact manifest writer."""

from __future__ import annotations

import json
from pathlib import Path

from src.artifact_manifest import collect_run_artifact_paths, write_artifact_manifest
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
