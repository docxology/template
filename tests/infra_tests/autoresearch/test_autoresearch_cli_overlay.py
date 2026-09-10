"""AutoResearch CLI subprocess and overlay entrypoint tests (formerly part of test_autoresearch.py)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.infra_tests.autoresearch._autoresearch_plan_helpers import _write_repo_scaffold


def test_cli_validate_writes_report_and_fails_on_strict_issues(tmp_path: Path) -> None:
    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "autoresearch.yaml").write_text(
        """
strict: true
quality_checks: [unknown_check]
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "infrastructure.autoresearch.cli",
            "validate",
            "--repo-root",
            str(repo_root),
            "--project",
            "demo",
            "--fail-on-issues",
        ],
        cwd=Path(__file__).resolve().parents[3],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1


@pytest.mark.timeout(120)
def test_cli_plan_review_summarize_and_benchmark_write_declared_artifacts(tmp_path: Path) -> None:
    # Four real subprocess CLI invocations (plan/review-packet/summarize/benchmark);
    # measured ~24s standalone, so the 10s global budget is not sufficient on a
    # loaded machine. Explicit budget keeps the suite from cascade-aborting.
    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "autoresearch.yaml").write_text(
        """
strict: true
quality_checks: [benchmark_tasks]
benchmark_tasks:
  - id: smoke
    description: Smoke benchmark
    grading_output: output/reports/benchmark_smoke.json
""",
        encoding="utf-8",
    )
    (project / "output" / "reports" / "benchmark_smoke.json").write_text('{"score": 1.0}\n', encoding="utf-8")

    root = Path(__file__).resolve().parents[3]
    for command in ("plan", "review-packet", "summarize", "benchmark"):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "infrastructure.autoresearch.cli",
                command,
                "--repo-root",
                str(repo_root),
                "--project",
                "demo",
            ],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr

    assert (project / "output" / "data" / "autoresearch_plan.json").exists()
    assert (project / "output" / "reports" / "autoresearch_review_packet.md").exists()
    assert (project / "output" / "reports" / "autoresearch_summary.md").exists()
    scores = json.loads((project / "output" / "data" / "benchmark_scores.json").read_text(encoding="utf-8"))
    assert scores["tasks"][0]["id"] == "smoke"


def test_validate_autoresearch_overlay_returns_empty_without_marker(tmp_path: Path) -> None:
    from infrastructure.autoresearch import validate_autoresearch_overlay

    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)

    issues = validate_autoresearch_overlay(project, tmp_path)

    assert issues == []
    assert not (project / "output" / "reports" / "autoresearch_readiness.json").exists()


def test_validate_autoresearch_overlay_surfaces_errors_and_writes_report(tmp_path: Path) -> None:
    from infrastructure.autoresearch import validate_autoresearch_overlay

    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "autoresearch.yaml").write_text(
        "strict: true\nquality_checks: [unknown_check]\n",
        encoding="utf-8",
    )

    issues = validate_autoresearch_overlay(project, repo_root)

    assert any("AUTORESEARCH.QUALITY_CHECK_UNKNOWN" in issue for issue in issues)
    assert (project / "output" / "reports" / "autoresearch_readiness.json").exists()


def test_validate_autoresearch_overlay_reports_failures_gracefully(tmp_path: Path) -> None:
    from infrastructure.autoresearch import validate_autoresearch_overlay

    # Marker present but no pipeline.yaml scaffold -> build raises, surfaced as a string.
    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)
    (project / "autoresearch.yaml").write_text("strict: true\n", encoding="utf-8")

    issues = validate_autoresearch_overlay(project, tmp_path)

    assert any("AutoResearch readiness validation failed" in issue for issue in issues)
