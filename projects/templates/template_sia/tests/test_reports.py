"""Tests for reports helpers."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

from src.loop import build_run_config, run_sia_loop_project
from src.loop_config import load_sia_settings
from src.reports import compute_variables, format_metric

PROJECT_ROOT = Path(__file__).resolve().parent.parent

Copy = Callable[[Path], Path]


def test_format_metric_variants():
    assert format_metric(None) == "0"
    assert format_metric(0.75) == "0.7500"
    assert format_metric("custom") == "custom"


def test_format_metric_integer():
    """Integers are formatted with 4 decimal places like floats."""
    assert format_metric(1) == "1.0000"
    assert format_metric(0) == "0.0000"


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


def test_load_sia_settings_empty_yaml(tmp_path: Path):
    """An absent or empty config.yaml returns safe defaults."""
    # No manuscript/config.yaml exists — _load_yaml_mapping returns {} and
    # all settings fall back to their coded defaults.
    settings = load_sia_settings(tmp_path)
    assert settings.task_name == "mini_classify"
    assert settings.max_generations == 3
    assert settings.live is False
    assert settings.run_id == 1
    assert settings.target_timeout_sec == 60
    assert settings.llm_model == ""


def test_load_sia_settings_non_dict_yaml(tmp_path: Path):
    """A config.yaml whose root is a list (not a mapping) returns safe defaults."""
    cfg = tmp_path / "manuscript" / "config.yaml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("- item1\n- item2\n", encoding="utf-8")
    settings = load_sia_settings(tmp_path)
    assert settings.task_name == "mini_classify"
    assert settings.live is False
