#!/usr/bin/env python3
"""Tests for skill eval harness report formatting."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SCRIPTS = _REPO / "docs/prompts/_skill-eval/scripts"
sys.path.insert(0, str(_SCRIPTS))

from skill_eval.report import (  # noqa: E402
    format_compare_section,
    format_eval_row,
    format_harness_report,
    load_baseline_benchmark,
)


def _sample_benchmark(*, run_dir: str = "latest") -> dict:
    return {
        "skill_name": "template-workflows",
        "run_dir": run_dir,
        "configurations": [
            {
                "name": "with_skill",
                "evals": [
                    {"eval_name": "analysis-fast-fail", "pass_rate": 1.0, "passed": 4, "total": 4},
                    {"eval_name": "near-miss-fibonacci", "pass_rate": 1.0, "passed": 3, "total": 3},
                ],
            },
            {
                "name": "without_skill",
                "evals": [
                    {"eval_name": "analysis-fast-fail", "pass_rate": 0.75, "passed": 3, "total": 4},
                    {"eval_name": "near-miss-fibonacci", "pass_rate": 0.0, "passed": 0, "total": 3},
                ],
            },
        ],
        "summary": {
            "with_skill_mean_pass_rate": 1.0,
            "without_skill_mean_pass_rate": 0.375,
            "with_skill_positive_only_pass_rate": 1.0,
            "without_skill_positive_only_pass_rate": 0.75,
            "delta_pass_rate": 0.625,
            "delta_positive_only_pass_rate": 0.25,
            "positive_eval_count": 1,
            "negative_eval_count": 1,
        },
    }


def test_format_eval_row_perfect() -> None:
    row = format_eval_row("analysis-fast-fail", 1.0, 0.75, [])
    assert "analysis-fast-fail" in row
    assert "100%" in row
    assert "75%" in row
    assert "+25%" in row
    assert "—" in row


def test_format_eval_row_shows_failed_expectations() -> None:
    row = format_eval_row("infra-package", 0.8, 0.4, ["Places code under infrastructure/"])
    assert "Places code under infrastructure/" in row


def test_format_harness_report_sections() -> None:
    benchmark = _sample_benchmark()
    workspace = _REPO / "docs/prompts/_skill-eval/latest"
    gradings: dict[str, dict[str, dict]] = {}
    for block in benchmark["configurations"]:
        mode = block["name"]
        for row in block["evals"]:
            name = row["eval_name"]
            gradings.setdefault(name, {})[mode] = {
                "summary": {
                    "passed": row["passed"],
                    "total": row["total"],
                    "pass_rate": row["pass_rate"],
                },
                "expectations": [],
                "negative": name.startswith("near-miss"),
            }
    report = format_harness_report(
        benchmark,
        workspace,
        gradings_by_eval=gradings,
        review_path=workspace / "review.html",
    )
    assert "SKILL EVAL HARNESS" in report
    assert "iteration-" not in report
    assert "Run directory: latest" in report
    assert "SUMMARY" in report
    assert "PER-EVAL (positive)" in report
    assert "NEGATIVE (with_skill must route out-of-scope)" in report
    assert "ARTIFACTS" in report
    assert "analysis-fast-fail" in report
    assert "benchmark.json" in report
    assert "review.html" in report


def test_format_harness_report_surfaces_with_skill_gaps() -> None:
    benchmark = {
        "run_dir": "latest",
        "configurations": [
            {
                "name": "with_skill",
                "evals": [{"eval_name": "infra-package", "pass_rate": 0.8, "passed": 4, "total": 5}],
            },
            {
                "name": "without_skill",
                "evals": [{"eval_name": "infra-package", "pass_rate": 0.4, "passed": 2, "total": 5}],
            },
        ],
        "summary": {
            "with_skill_mean_pass_rate": 0.8,
            "without_skill_mean_pass_rate": 0.4,
            "with_skill_positive_only_pass_rate": 0.8,
            "without_skill_positive_only_pass_rate": 0.4,
            "delta_pass_rate": 0.4,
            "delta_positive_only_pass_rate": 0.4,
            "positive_eval_count": 1,
            "negative_eval_count": 0,
        },
    }
    gradings = {
        "infra-package": {
            "with_skill": {
                "summary": {"passed": 4, "total": 5, "pass_rate": 0.8},
                "expectations": [
                    {"text": "Places code under infrastructure/", "passed": False},
                    {"text": "Mentions tests/infra_tests/", "passed": True},
                ],
                "negative": False,
            },
            "without_skill": {
                "summary": {"passed": 2, "total": 5, "pass_rate": 0.4},
                "expectations": [],
                "negative": False,
            },
        }
    }
    report = format_harness_report(
        benchmark,
        Path("/tmp/skill-eval-latest"),
        gradings_by_eval=gradings,
    )
    assert "Places code under infrastructure/" in report


def test_format_compare_section_regression() -> None:
    baseline = {
        "run_dir": "baseline",
        "configurations": [
            {
                "name": "with_skill",
                "evals": [
                    {"eval_name": "analysis-fast-fail", "pass_rate": 1.0},
                    {"eval_name": "infra-package", "pass_rate": 1.0},
                ],
            },
        ],
    }
    current = {
        "run_dir": "latest",
        "configurations": [
            {
                "name": "with_skill",
                "evals": [
                    {"eval_name": "analysis-fast-fail", "pass_rate": 0.75},
                    {"eval_name": "infra-package", "pass_rate": 1.0},
                ],
            },
        ],
    }
    lines = format_compare_section(current, baseline)
    text = "\n".join(lines)
    assert "COMPARE (vs baseline with_skill)" in text
    assert "REGRESSION" in text
    assert "analysis-fast-fail" in text


def test_format_compare_section_no_regressions() -> None:
    benchmark = _sample_benchmark()
    lines = format_compare_section(benchmark, benchmark)
    text = "\n".join(lines)
    assert "No with_skill regressions." in text


def test_load_baseline_benchmark_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import skill_eval.config as config_mod

    monkeypatch.setattr(config_mod, "BASELINE_DIR", tmp_path / "missing-baseline")
    assert load_baseline_benchmark() is None


def test_load_baseline_benchmark_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import skill_eval.config as config_mod

    baseline_dir = tmp_path / "baseline"
    baseline_dir.mkdir()
    payload = _sample_benchmark(run_dir="baseline")
    (baseline_dir / "benchmark.json").write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(config_mod, "BASELINE_DIR", baseline_dir)
    loaded = load_baseline_benchmark()
    assert loaded is not None
    assert loaded["run_dir"] == "baseline"
