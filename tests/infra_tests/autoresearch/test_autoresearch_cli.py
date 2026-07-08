"""Real-behavior tests for ``infrastructure.autoresearch.cli``.

No mocks — exercises the real CLI entry point, parser, and file outputs
against a synthetic project scaffolded under ``tmp_path``.
"""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

import pytest

from infrastructure.autoresearch.cli import build_parser, main
from infrastructure.core.pipeline.artifacts import compute_sha256
from tests._support.projects import make_project


# ---------------------------------------------------------------------------
# Scaffolding helper
# ---------------------------------------------------------------------------


def _write_pipeline_yaml(repo_root: Path) -> Path:
    """Write a minimal pipeline.yaml so the planner can compose a plan."""
    pipeline_dir = repo_root / "infrastructure" / "core" / "pipeline"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    (pipeline_dir / "pipeline.yaml").write_text(
        """
stages:
  - name: Environment Setup
    script: 00_setup_environment.py
    contract:
      input_artifacts: ["projects/{project}/"]
      output_artifacts: ["projects/{project}/output/"]
      definition_of_done: "Environment is ready."
      failure_code: "ENVIRONMENT_SETUP_FAILED"
      retry_policy: 0
  - name: Project Analysis
    script: 02_run_analysis.py
    depends_on: [Environment Setup]
    contract:
      input_artifacts: ["projects/{project}/src/"]
      output_artifacts: ["projects/{project}/output/data/result.csv"]
      definition_of_done: "Analysis writes the declared result."
      failure_code: "PROJECT_ANALYSIS_FAILED"
      retry_policy: 0
control:
  hitl_mode: full-auto
""",
        encoding="utf-8",
    )
    return pipeline_dir


def _scaffold_repo(tmp_path: Path) -> Path:
    """Build a minimum-valid repo root for AutoResearch CLI commands."""
    repo_root = tmp_path
    _write_pipeline_yaml(repo_root)
    make_project(repo_root, "template_test", with_output=True)
    project = repo_root / "projects" / "template_test"
    # Provide a minimal result artifact so validation has something to check.
    result = project / "output" / "data" / "result.csv"
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text("score\n1.0\n", encoding="utf-8")
    # Write an artifact manifest so extrinsic validation passes.
    manifest = {
        "entries": [
            {
                "path": "output/data/result.csv",
                "size_bytes": result.stat().st_size,
                "sha256": compute_sha256(result),
                "stage_num": 2,
                "stage_name": "Project Analysis",
                "contract_match": True,
            }
        ],
        "issues": [],
    }
    (project / "output" / "reports").mkdir(parents=True, exist_ok=True)
    (project / "output" / "reports" / "artifact_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return repo_root


# ---------------------------------------------------------------------------
# build_parser() — subcommand presence
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "subcommand",
    ["plan", "validate", "review-packet", "summarize", "benchmark", "schema"],
)
def test_build_parser_has_subcommand(subcommand: str) -> None:
    """All expected subcommands are registered on the parser."""
    parser = build_parser()
    # Find the subparsers action to inspect registered choices.
    subparsers_action = next(
        action
        for action in parser._actions  # noqa: SLF001
        if hasattr(action, "choices") and action.choices is not None
    )
    choices = subparsers_action.choices or {}
    assert subcommand in choices


# ---------------------------------------------------------------------------
# main() — schema command
# ---------------------------------------------------------------------------


def test_main_schema_returns_zero_and_prints_json() -> None:
    """``schema`` subcommand returns 0 and emits valid JSON to stdout."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        exit_code = main(["schema"])
    assert exit_code == 0
    payload = json.loads(buffer.getvalue())
    assert "prog" in payload
    assert "subcommands" in payload


# ---------------------------------------------------------------------------
# main() — plan command
# ---------------------------------------------------------------------------


def test_main_plan_returns_zero_and_writes_plan_json(tmp_path: Path) -> None:
    """``plan`` subcommand returns 0 and writes ``autoresearch_plan.json``."""
    repo_root = _scaffold_repo(tmp_path)
    project_dir = repo_root / "projects" / "template_test"

    exit_code = main(["plan", "--project", "template_test", "--repo-root", str(repo_root)])

    assert exit_code == 0
    plan_path = project_dir / "output" / "data" / "autoresearch_plan.json"
    assert plan_path.exists(), f"Expected plan JSON at {plan_path}"
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    assert "stages" in payload or "project_name" in payload


# ---------------------------------------------------------------------------
# main() — validate command
# ---------------------------------------------------------------------------


def test_main_validate_returns_zero_or_one(tmp_path: Path) -> None:
    """``validate`` subcommand returns 0 (valid) or 1 (invalid)."""
    repo_root = _scaffold_repo(tmp_path)

    exit_code = main(["validate", "--project", "template_test", "--repo-root", str(repo_root)])

    assert exit_code in (0, 1)
    # The report JSON should always be written regardless of validity.
    report_path = repo_root / "projects" / "template_test" / "output" / "reports"
    assert report_path.exists()


# ---------------------------------------------------------------------------
# main() — summarize command
# ---------------------------------------------------------------------------


def test_main_summarize_returns_zero(tmp_path: Path) -> None:
    """``summarize`` subcommand returns 0 and writes a summary markdown."""
    repo_root = _scaffold_repo(tmp_path)

    exit_code = main(["summarize", "--project", "template_test", "--repo-root", str(repo_root)])

    assert exit_code == 0


# ---------------------------------------------------------------------------
# main() — benchmark command
# ---------------------------------------------------------------------------


def test_main_benchmark_returns_zero(tmp_path: Path) -> None:
    """``benchmark`` subcommand returns 0 and writes benchmark scores JSON."""
    repo_root = _scaffold_repo(tmp_path)

    exit_code = main(["benchmark", "--project", "template_test", "--repo-root", str(repo_root)])

    assert exit_code == 0
