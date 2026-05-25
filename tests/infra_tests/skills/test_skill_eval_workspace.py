#!/usr/bin/env python3
"""Tests for skill eval workspace loader."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SKILLS_TESTS = Path(__file__).resolve().parent
_SCRIPTS = _REPO / "docs/prompts/_skill-eval/scripts"
sys.path.insert(0, str(_SCRIPTS))
sys.path.insert(0, str(_SKILLS_TESTS))

from skill_eval.workspace import (  # noqa: E402
    load_benchmark,
    load_gradings_by_eval,
    load_workspace_state,
)
from skill_eval_fixtures import write_minimal_workspace


def test_load_benchmark_round_trip(tmp_path: Path) -> None:
    write_minimal_workspace(tmp_path)
    benchmark = load_benchmark(tmp_path)
    assert benchmark["run_dir"] == "latest"
    assert benchmark["summary"]["with_skill_positive_only_pass_rate"] == 1.0


def test_load_benchmark_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Missing benchmark.json"):
        load_benchmark(tmp_path)


def test_load_gradings_by_eval(tmp_path: Path) -> None:
    write_minimal_workspace(tmp_path)
    gradings = load_gradings_by_eval(tmp_path)
    assert "analysis-fast-fail" in gradings
    assert gradings["analysis-fast-fail"]["with_skill"]["summary"]["passed"] == 4
    assert gradings["analysis-fast-fail"]["without_skill"]["summary"]["passed"] == 3
    assert gradings["analysis-fast-fail"]["with_skill"]["negative"] is False


def test_load_workspace_state(tmp_path: Path) -> None:
    write_minimal_workspace(tmp_path)
    benchmark, gradings = load_workspace_state(tmp_path)
    assert benchmark["skill_name"] == "template-workflows"
    assert "analysis-fast-fail" in gradings
