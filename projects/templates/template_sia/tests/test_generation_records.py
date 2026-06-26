"""Tests for generation_records."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from src.generation_records import generation_metrics, load_run_summary

PROJECT_ROOT = Path(__file__).resolve().parent.parent

Copy = Callable[[Path], Path]


def test_load_run_summary_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_run_summary(tmp_path)


def test_load_run_summary_invalid_payload(tmp_path: Path):
    """A run_summary.json that is a JSON array (not an object) must raise ValueError."""
    path = tmp_path / "output" / "runs" / "run_1" / "run_summary.json"
    path.parent.mkdir(parents=True)
    path.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ValueError, match="(?i)invalid run summary"):
        load_run_summary(tmp_path)


def test_generation_metrics_parses_rows():
    summary = {
        "generations": [
            {"generation": 1, "evaluation": {"metric_name": "accuracy", "metric_value": 0.5, "n_samples": 6}},
            {"generation": 2, "evaluation": None},
            "bad",
        ]
    }
    rows = generation_metrics(summary)
    assert len(rows) == 1
    assert rows[0]["metric_name"] == "accuracy"


def test_generation_metrics_empty_generations():
    """An empty generations list returns an empty metrics list."""
    rows = generation_metrics({"generations": []})
    assert rows == []


def test_generation_metrics_missing_generations_key():
    """A summary without a 'generations' key returns an empty list."""
    rows = generation_metrics({})
    assert rows == []


def test_load_run_summary_from_fixture_run(tmp_path: Path, copy_project_sandbox: Copy):
    project = tmp_path / "proj"
    copy_project_sandbox(project)
    if (project / "output").exists():
        shutil.rmtree(project / "output")
    from src.loop import run_sia_loop_project

    run_sia_loop_project(project, live=False)
    summary = load_run_summary(project)
    assert summary["run_id"] == 1
    path = project / "output" / "runs" / "run_1" / "run_summary.json"
    assert path.is_file()
    roundtrip = json.loads(path.read_text(encoding="utf-8"))
    assert roundtrip["generations"]
