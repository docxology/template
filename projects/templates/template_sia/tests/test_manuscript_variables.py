"""Tests for manuscript variable hydration."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.generation_records import load_run_summary
from src.loop import run_sia_loop_project
from src.manuscript_tokens_metrics import compute_metrics_variables
from src.manuscript_variables import compute_variables

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_manuscript_tokens_cover_manuscript_files():
    run_sia_loop_project(PROJECT_ROOT, live=False)
    variables = compute_variables(PROJECT_ROOT)
    tokens: set[str] = set()
    for path in (PROJECT_ROOT / "manuscript").glob("[0-9][0-9]_*.md"):
        tokens.update(re.findall(r"\{\{([A-Z0-9_]+)\}\}", path.read_text(encoding="utf-8")))
    assert tokens
    missing = tokens - set(variables)
    assert not missing, f"Unresolved tokens: {sorted(missing)}"


def test_metrics_table_matches_run_summary():
    run_sia_loop_project(PROJECT_ROOT, live=False)
    variables = compute_variables(PROJECT_ROOT)
    summary = load_run_summary(PROJECT_ROOT, run_id=1)
    generations = summary.get("generations") or []
    assert str(len(generations)) == variables["SIA_GENERATION_COUNT"]
    assert variables["SIA_GEN1_METRIC_VALUE"] in variables["SIA_METRICS_TABLE"]
    assert variables["SIA_METRIC_DELTA"] == f"{float(variables['SIA_FINAL_METRIC_VALUE']) - float(variables['SIA_GEN1_METRIC_VALUE']):.4f}"


def test_variables_json_round_trip():
    run_sia_loop_project(PROJECT_ROOT, live=False)
    variables = compute_variables(PROJECT_ROOT)
    saved = json.loads((PROJECT_ROOT / "output" / "data" / "manuscript_variables.json").read_text())
    for key, value in variables.items():
        assert saved[key] == value


def test_compute_metrics_variables_no_numeric_values(tmp_path: Path) -> None:
    """When no generation has a numeric metric_value, SIA_METRIC_DELTA must be '0'."""
    # Build a minimal run_summary with one generation whose metric_value is None.
    summary_dir = tmp_path / "output" / "runs" / "run_1"
    summary_dir.mkdir(parents=True)
    payload = {
        "run_id": 1,
        "live": False,
        "max_generations": 1,
        "task_dir": "tasks/mini_classify",
        "generations": [
            {
                "generation": 1,
                "evaluation": {
                    "metric_name": "accuracy",
                    "metric_value": None,
                    "n_samples": 0,
                },
            }
        ],
    }
    (summary_dir / "run_summary.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")
    # Also need a minimal config.yaml so load_sia_settings resolves run_id=1
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "config.yaml").write_text("sia:\n  run_id: 1\n", encoding="utf-8")

    variables = compute_metrics_variables(tmp_path)
    assert variables["SIA_METRIC_DELTA"] == "0"


def test_compute_metrics_variables_non_numeric_metric_value(tmp_path: Path) -> None:
    """A string metric_value (e.g. 'n/a') must not raise; delta must be '0'."""
    summary_dir = tmp_path / "output" / "runs" / "run_1"
    summary_dir.mkdir(parents=True)
    payload = {
        "run_id": 1,
        "live": False,
        "max_generations": 2,
        "task_dir": "tasks/mini_classify",
        "generations": [
            {
                "generation": 1,
                "evaluation": {"metric_name": "accuracy", "metric_value": "n/a", "n_samples": 6},
            },
            {
                "generation": 2,
                "evaluation": {"metric_name": "accuracy", "metric_value": "n/a", "n_samples": 6},
            },
        ],
    }
    (summary_dir / "run_summary.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "config.yaml").write_text("sia:\n  run_id: 1\n", encoding="utf-8")

    variables = compute_metrics_variables(tmp_path)
    assert variables["SIA_METRIC_DELTA"] == "0"
