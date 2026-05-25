"""Tests for repo-wide methods orchestration contracts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


def test_build_plan_maps_pipeline_contracts_to_methods_surface(repo_root: Path) -> None:
    from infrastructure.methods import build_methods_orchestration_plan, validate_methods_orchestration_plan

    plan = build_methods_orchestration_plan(repo_root, "template_code_project")

    assert plan.project_name == "template_code_project"
    assert plan.pipeline_source.as_posix().endswith("infrastructure/core/pipeline/pipeline.yaml")
    assert "projects/template_code_project/manuscript/02_methodology.md" in plan.method_sections
    assert plan.artifact_manifest == Path("projects/template_code_project/output/reports/artifact_manifest.json")
    assert plan.evidence_registry == Path("projects/template_code_project/output/reports/evidence_registry.json")

    by_name = {stage.name: stage for stage in plan.stages}
    analysis = by_name["Project Analysis"]
    assert analysis.gate == "experiment_method_design"
    assert "projects/template_code_project/src/" in analysis.input_artifacts
    assert "projects/template_code_project/scripts/" in analysis.input_artifacts
    assert any("scripts/02_run_analysis.py" in command for command in analysis.verification_commands)

    render = by_name["PDF Rendering"]
    assert render.depends_on == ("Project Analysis",)
    assert any(
        "execute_pipeline.py --project template_code_project --stage render_pdf" in command
        for command in render.verification_commands
    )

    issues = validate_methods_orchestration_plan(plan)
    assert [issue for issue in issues if issue.severity == "error"] == []


def test_public_template_projects_have_methods_orchestration_plans(repo_root: Path) -> None:
    from infrastructure.methods import build_methods_orchestration_plan

    plans = [build_methods_orchestration_plan(repo_root, project) for project in PUBLIC_PROJECT_NAMES]

    assert {plan.project_name for plan in plans} == set(PUBLIC_PROJECT_NAMES)
    for plan in plans:
        assert plan.method_sections, plan.project_name
        assert any(stage.gate for stage in plan.stages), plan.project_name
        assert any(stage.output_artifacts for stage in plan.stages), plan.project_name


def test_render_markdown_includes_actions_and_validation(repo_root: Path) -> None:
    from infrastructure.methods import build_methods_orchestration_plan, render_methods_orchestration_markdown

    plan = build_methods_orchestration_plan(repo_root, "template_autoresearch_project")
    markdown = render_methods_orchestration_markdown(plan)

    assert "# Methods orchestration: template_autoresearch_project" in markdown
    assert "## Method Surfaces" in markdown
    assert "Project Analysis" in markdown
    assert "artifact_manifest.json" in markdown
    assert "evidence_registry.json" in markdown
    assert "uv run python scripts/execute_pipeline.py --project template_autoresearch_project --core-only" in markdown


def test_validation_reports_missing_method_section(tmp_path: Path) -> None:
    from infrastructure.methods import build_methods_orchestration_plan, validate_methods_orchestration_plan

    _write_minimal_repo(tmp_path)

    plan = build_methods_orchestration_plan(tmp_path, "demo")
    issues = validate_methods_orchestration_plan(plan)

    assert any(issue.code == "METHODS.METHOD_SECTION_MISSING" for issue in issues)
    assert any(issue.code == "METHODS.ARTIFACT_MANIFEST_MISSING" for issue in issues)
    assert any(issue.code == "METHODS.EVIDENCE_REGISTRY_MISSING" for issue in issues)


def test_methods_cli_outputs_json_and_markdown(repo_root: Path) -> None:
    json_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "infrastructure.methods",
            "plan",
            "--repo-root",
            str(repo_root),
            "--project",
            "template_prose_project",
            "--format",
            "json",
        ],
        check=False,
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    assert json_result.returncode == 0, json_result.stderr
    payload = json.loads(json_result.stdout)
    assert payload["project_name"] == "template_prose_project"
    assert payload["stages"]

    markdown_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "infrastructure.methods",
            "plan",
            "--repo-root",
            str(repo_root),
            "--project",
            "template_prose_project",
            "--format",
            "markdown",
        ],
        check=False,
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    assert markdown_result.returncode == 0, markdown_result.stderr
    assert "# Methods orchestration: template_prose_project" in markdown_result.stdout
    assert "Validation" in markdown_result.stdout


def _write_minimal_repo(repo_root: Path) -> None:
    pipeline_dir = repo_root / "infrastructure" / "core" / "pipeline"
    pipeline_dir.mkdir(parents=True)
    (pipeline_dir / "pipeline.yaml").write_text(
        """
stages:
  - name: Project Analysis
    script: 02_run_analysis.py
    tags: [core]
    contract:
      input_artifacts: ["projects/{project}/src/", "projects/{project}/scripts/"]
      output_artifacts: ["projects/{project}/output/data/result.csv"]
      definition_of_done: "Analysis writes a result."
      failure_code: "PROJECT_ANALYSIS_FAILED"
      retry_policy: 0
      gate: "experiment_method_design"
""",
        encoding="utf-8",
    )
    project = repo_root / "projects" / "demo"
    for path in ("src", "tests", "scripts", "manuscript", "output/reports"):
        (project / path).mkdir(parents=True)
