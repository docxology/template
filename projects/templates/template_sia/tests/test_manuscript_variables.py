"""Tests for manuscript variable hydration."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.generation_records import load_run_summary
from src.loop import run_sia_loop_project
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
