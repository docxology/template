"""Negative-control tests for SIA artifact validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.sia.evaluation_runner import read_results_json
from src.artifact_manifest import write_artifact_manifest


def test_read_results_json_rejects_hollow_object(tmp_path: Path) -> None:
    path = tmp_path / "results.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(Exception):
        read_results_json(path)


def test_read_results_json_rejects_wrong_types(tmp_path: Path) -> None:
    path = tmp_path / "results.json"
    path.write_text(
        json.dumps({"metric_name": "accuracy", "metric_value": "not-a-number", "n_samples": 6}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        read_results_json(path)


def test_artifact_manifest_omits_missing_paths(tmp_path: Path) -> None:
    present = tmp_path / "output" / "data" / "manuscript_variables.json"
    present.parent.mkdir(parents=True)
    present.write_text("{}", encoding="utf-8")
    missing = tmp_path / "output" / "missing.json"
    manifest_path = write_artifact_manifest(tmp_path, [present, missing])
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths = {entry["path"] for entry in payload["entries"]}
    assert "output/data/manuscript_variables.json" in paths
    assert "output/missing.json" not in paths
