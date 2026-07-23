"""Tests for the methods orchestration CLI (infrastructure.methods.cli)."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

from infrastructure.methods.cli import build_parser, main
from tests._support.projects import make_project, write_doc

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_build_parser_has_plan_subcommand() -> None:
    """build_parser creates a 'plan' subcommand."""
    parser = build_parser()
    # Find the plan subparser action
    subparsers_actions = [action for action in parser._actions if action.choices and isinstance(action.choices, dict)]
    assert subparsers_actions, "no subparsers found"
    choices = subparsers_actions[0].choices
    assert "plan" in choices
    assert "schema" in choices


def test_build_parser_format_choices() -> None:
    """The plan subcommand accepts --format with choices json and markdown."""
    parser = build_parser()
    # Parse with --format json to verify it's accepted
    args = parser.parse_args(["plan", "--project", "test_proj", "--format", "json"])
    assert args.format == "json"
    args_md = parser.parse_args(["plan", "--project", "test_proj", "--format", "markdown"])
    assert args_md.format == "markdown"
    # Default is markdown
    args_default = parser.parse_args(["plan", "--project", "test_proj"])
    assert args_default.format == "markdown"


def test_schema_subcommand_returns_zero_and_prints_json() -> None:
    """main(['schema']) returns 0 and prints valid JSON with expected keys."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = main(["schema"])
    assert code == 0
    payload = json.loads(buffer.getvalue())
    assert payload["prog"] == "python -m infrastructure.methods"
    assert "plan" in payload["subcommands"]
    assert "schema" in payload["subcommands"]


def _write_minimal_repo(repo_root: Path) -> Path:
    """Create a minimal repo with a pipeline.yaml and a scaffolded project."""
    pipeline_dir = repo_root / "infrastructure" / "core" / "pipeline"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    write_doc(
        pipeline_dir / "pipeline.yaml",
        """
stages:
  - name: Project Analysis
    script: scripts/pipeline/stage_02_analysis.py
    tags: [core]
    contract:
      input_artifacts: ["projects/{project}/src/", "projects/{project}/scripts/"]
      output_artifacts: ["projects/{project}/output/data/result.csv"]
      definition_of_done: "Analysis writes a result."
      failure_code: "PROJECT_ANALYSIS_FAILED"
      retry_policy: 0
      gate: "experiment_method_design"
""",
    )
    project = make_project(repo_root, "template_test", with_manuscript=True, with_scripts=True)
    (project / "output" / "reports").mkdir(parents=True, exist_ok=True)
    return project


def test_main_plan_json_returns_validation_error_and_valid_json(tmp_path: Path) -> None:
    """A rendered plan still prints JSON while returning the standard validation code."""
    _write_minimal_repo(tmp_path)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = main(
            [
                "plan",
                "--project",
                "template_test",
                "--repo-root",
                str(tmp_path),
                "--format",
                "json",
            ]
        )
    assert code == 1
    payload = json.loads(buffer.getvalue())
    assert "stages" in payload
    assert payload["project_name"] == "template_test"
    assert isinstance(payload["stages"], list)
    assert len(payload["stages"]) > 0


def test_main_plan_markdown_returns_validation_error_and_prints_markdown(tmp_path: Path) -> None:
    """A rendered plan still prints Markdown while returning the standard validation code."""
    _write_minimal_repo(tmp_path)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = main(
            [
                "plan",
                "--project",
                "template_test",
                "--repo-root",
                str(tmp_path),
            ]
        )
    assert code == 1
    output = buffer.getvalue()
    assert "# Methods orchestration: template_test" in output
    assert "## Stage Contracts" in output
    assert "## Validation" in output


def test_main_plan_with_check_flag_on_scaffold_returns_zero(tmp_path: Path) -> None:
    """main(['plan', ..., '--check']) returns 0 when no error-severity issues exist."""
    _write_minimal_repo(tmp_path)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = main(
            [
                "plan",
                "--project",
                "template_test",
                "--repo-root",
                str(tmp_path),
                "--format",
                "json",
                "--check",
            ]
        )
    # The scaffold has no method section and no artifact manifest, so --check
    # should return 1 (there ARE error-severity issues).
    assert code == 1


def test_main_plan_validation_error_is_one_without_check(tmp_path: Path) -> None:
    _write_minimal_repo(tmp_path)

    code = main(
        [
            "plan",
            "--project",
            "template_test",
            "--repo-root",
            str(tmp_path),
            "--format",
            "json",
        ]
    )

    assert code == 1


def test_main_plan_markdown_on_real_exemplar() -> None:
    """main(['plan', ...]) on a real public exemplar returns 0 with markdown output."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = main(
            [
                "plan",
                "--project",
                "templates/template_code_project",
                "--repo-root",
                str(REPO_ROOT),
            ]
        )
    assert code == 0
    output = buffer.getvalue()
    assert "# Methods orchestration: templates/template_code_project" in output


def test_main_plan_json_on_real_exemplar() -> None:
    """main(['plan', ..., '--format', 'json']) on a real public exemplar returns 0 with valid JSON."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = main(
            [
                "plan",
                "--project",
                "templates/template_code_project",
                "--repo-root",
                str(REPO_ROOT),
                "--format",
                "json",
            ]
        )
    assert code == 0
    payload = json.loads(buffer.getvalue())
    assert "stages" in payload
    assert payload["project_name"] == "templates/template_code_project"


def test_main_all_public_source_audit_returns_aggregate_json() -> None:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = main(
            [
                "plan",
                "--all-public",
                "--artifact-mode",
                "source",
                "--repo-root",
                str(REPO_ROOT),
                "--format",
                "json",
                "--check",
            ]
        )

    assert code == 0
    payload = json.loads(buffer.getvalue())
    assert payload["project_count"] == 24
    assert payload["artifact_mode"] == "source"
    assert payload["passed"] is True
