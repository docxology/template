"""Tests for reports helpers."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

from src.loop import build_run_config, run_sia_loop_project
from src.reports import compute_variables, format_metric

PROJECT_ROOT = Path(__file__).resolve().parent.parent

Copy = Callable[[Path], Path]


def test_format_metric_variants():
    assert format_metric(None) == "0"
    assert format_metric(0.75) == "0.7500"
    assert format_metric("custom") == "custom"


def test_build_run_config_llm_override():
    config = build_run_config(PROJECT_ROOT, live=True)
    assert config.live is True


def test_compute_variables_empty_metrics(tmp_path: Path, copy_project_sandbox: Copy):
    project = tmp_path / "proj"
    copy_project_sandbox(project)
    if (project / "output").exists():
        shutil.rmtree(project / "output")
    run_sia_loop_project(project, live=False)
    variables = compute_variables(project)
    assert int(variables["SIA_GENERATION_COUNT"]) >= 1
