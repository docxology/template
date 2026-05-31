"""Tests for reports helpers."""

from __future__ import annotations

from pathlib import Path

from src.loop import build_run_config, run_sia_loop_project
from src.reports import _format_metric, compute_variables

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_format_metric_variants():
    assert _format_metric(None) == "0"
    assert _format_metric(0.75) == "0.7500"
    assert _format_metric("custom") == "custom"


def test_build_run_config_llm_override():
    config = build_run_config(PROJECT_ROOT, live=True)
    assert config.live is True


def test_compute_variables_empty_metrics(tmp_path: Path):
    import shutil

    project = tmp_path / "proj"
    shutil.copytree(PROJECT_ROOT, project)
    if (project / "output").exists():
        shutil.rmtree(project / "output")
    run_sia_loop_project(project, live=False)
    variables = compute_variables(project)
    assert int(variables["SIA_GENERATION_COUNT"]) >= 1
