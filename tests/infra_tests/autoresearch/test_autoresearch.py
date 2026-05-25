"""Tests for deterministic AutoResearch readiness planning."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from infrastructure.core.pipeline.artifacts import compute_sha256


def _write_repo_scaffold(tmp_path: Path) -> Path:
    repo_root = tmp_path
    pipeline_dir = repo_root / "infrastructure" / "core" / "pipeline"
    pipeline_dir.mkdir(parents=True)
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
      gate: "experiment_method_design"
  - name: Output Validation
    script: 04_validate_output.py
    depends_on: [Project Analysis]
    contract:
      input_artifacts: ["projects/{project}/output/"]
      output_artifacts: ["projects/{project}/output/reports/"]
      definition_of_done: "Validation report is written."
      failure_code: "OUTPUT_VALIDATION_FAILED"
      retry_policy: 0
      gate: "publication_readiness"
control:
  hitl_mode: full-auto
""",
        encoding="utf-8",
    )
    project = repo_root / "projects" / "demo"
    for child in ("src", "tests", "scripts", "manuscript", "output/data", "output/reports"):
        (project / child).mkdir(parents=True)
    (project / "domain_profile.yaml").write_text(
        """
domain: code_research
display_name: Demo Research
validation_gates: [experiment_method_design, publication_readiness]
artifact_expectations: [output/data/result.csv]
""",
        encoding="utf-8",
    )
    (project / "experiment_plan.yaml").write_text(
        """
conditions:
  - name: baseline
    role: reference
  - name: proposal
    role: proposed
  - name: ablation
    role: variant
metrics:
  primary:
    name: score
    direction: maximize
protocol: "Run all conditions with identical seeds."
expected_figures: [fig:score]
expected_tables: [tbl:results]
baselines: [baseline]
ablations: [ablation]
""",
        encoding="utf-8",
    )
    result = project / "output" / "data" / "result.csv"
    result.write_text("score\n1.0\n", encoding="utf-8")
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
    (project / "output" / "reports" / "artifact_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    return repo_root


def test_load_config_defaults_when_absent(tmp_path: Path) -> None:
    from infrastructure.autoresearch import load_autoresearch_config

    project = tmp_path / "project"
    project.mkdir()

    config = load_autoresearch_config(project)

    assert config.enabled is True
    assert config.strict is False
    assert "evidence_registry" in config.quality_checks


def test_build_plan_composes_pipeline_and_project_overlays(tmp_path: Path) -> None:
    from infrastructure.autoresearch import build_autoresearch_plan

    repo_root = _write_repo_scaffold(tmp_path)
    (repo_root / "projects" / "demo" / "autoresearch.yaml").write_text(
        """
enabled: true
strict: true
topic: "Deterministic readiness"
quality_checks: [domain_profile, experiment_plan, pipeline_contracts, artifact_manifest]
stage_gates: [Project Analysis, Output Validation]
required_artifacts: [output/data/result.csv]
""",
        encoding="utf-8",
    )

    plan = build_autoresearch_plan(repo_root, "demo")

    assert plan.config.topic == "Deterministic readiness"
    assert plan.domain == "code_research"
    assert [stage.name for stage in plan.stages] == [
        "Environment Setup",
        "Project Analysis",
        "Output Validation",
    ]
    assert plan.stage_gates == ("Project Analysis", "Output Validation")
    assert "output/data/result.csv" in plan.required_artifacts


def test_validation_reports_invalid_stage_and_missing_artifact(tmp_path: Path) -> None:
    from infrastructure.autoresearch import build_autoresearch_plan, validate_autoresearch_plan

    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "autoresearch.yaml").write_text(
        """
strict: true
quality_checks: [domain_profile, experiment_plan, pipeline_contracts, artifact_manifest]
stage_gates: [Unknown Stage]
required_artifacts: [output/data/missing.csv]
""",
        encoding="utf-8",
    )

    plan = build_autoresearch_plan(repo_root, "demo")
    report = validate_autoresearch_plan(plan, project)

    assert report.valid is False
    assert {issue.code for issue in report.issues} >= {
        "AUTORESEARCH.STAGE_UNKNOWN",
        "AUTORESEARCH.ARTIFACT_MISSING",
    }
    assert report.summary["errors"] >= 2


def test_write_report_outputs_json_and_markdown(tmp_path: Path) -> None:
    from infrastructure.autoresearch import (
        AutoResearchIssue,
        AutoResearchReport,
        write_autoresearch_report,
    )

    project = tmp_path / "project"
    project.mkdir()
    report = AutoResearchReport(
        project_name="demo",
        valid=False,
        issues=(
            AutoResearchIssue(
                severity="error",
                code="AUTORESEARCH.TEST",
                message="Example issue",
                source_path="autoresearch.yaml",
                suggested_action="Fix the config.",
            ),
        ),
    )

    json_path, md_path = write_autoresearch_report(project, report)

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["summary"]["errors"] == 1
    assert "AUTORESEARCH.TEST" in md_path.read_text(encoding="utf-8")


def test_validation_intrinsic_passes_without_loop_outputs(tmp_path: Path) -> None:
    from infrastructure.autoresearch import build_autoresearch_plan, validate_autoresearch_plan

    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "output" / "reports" / "artifact_manifest.json").unlink()
    (project / "autoresearch.yaml").write_text(
        """
strict: true
quality_checks: [domain_profile, experiment_plan, pipeline_contracts, artifact_manifest, evidence_registry]
stage_gates: [Project Analysis]
required_artifacts: [output/data/result.csv]
""",
        encoding="utf-8",
    )

    plan = build_autoresearch_plan(repo_root, "demo")
    report = validate_autoresearch_plan(plan, project, phase="intrinsic")

    assert report.valid is True
    assert not any(issue.code.startswith("AUTORESEARCH.ARTIFACT") for issue in report.issues)
    assert not any(issue.code.startswith("AUTORESEARCH.EVIDENCE") for issue in report.issues)


def test_validation_extrinsic_fails_before_manifest_and_passes_after(tmp_path: Path) -> None:
    from infrastructure.autoresearch import build_autoresearch_plan, validate_autoresearch_plan

    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "output" / "reports" / "artifact_manifest.json").unlink()
    (project / "autoresearch.yaml").write_text(
        """
strict: true
quality_checks: [artifact_manifest]
required_artifacts: [output/data/result.csv]
""",
        encoding="utf-8",
    )
    plan = build_autoresearch_plan(repo_root, "demo")

    missing = validate_autoresearch_plan(plan, project, phase="extrinsic")
    assert missing.valid is False
    assert "AUTORESEARCH.ARTIFACT_MANIFEST_MISSING" in {issue.code for issue in missing.issues}

    result = project / "output" / "data" / "result.csv"
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
    (project / "output" / "reports" / "artifact_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    present = validate_autoresearch_plan(plan, project, phase="extrinsic")
    assert present.valid is True


def test_validation_phase_all_matches_combined_checks(tmp_path: Path) -> None:
    from infrastructure.autoresearch import build_autoresearch_plan, validate_autoresearch_plan

    repo_root = _write_repo_scaffold(tmp_path)
    project = repo_root / "projects" / "demo"
    (project / "autoresearch.yaml").write_text(
        """
strict: true
quality_checks: [domain_profile, artifact_manifest]
required_artifacts: [output/data/missing.csv]
""",
        encoding="utf-8",
    )
    plan = build_autoresearch_plan(repo_root, "demo")
    report = validate_autoresearch_plan(plan, project, phase="all")

    assert report.valid is False
    assert "AUTORESEARCH.ARTIFACT_MISSING" in {issue.code for issue in report.issues}


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
    assert (project / "output" / "reports" / "autoresearch_readiness.json").exists()
