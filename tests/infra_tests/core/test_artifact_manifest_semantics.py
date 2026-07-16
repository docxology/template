"""Behavioral regressions for cross-stage artifact ownership and self-reports."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from infrastructure.core.pipeline.artifacts import (
    aggregate_artifact_manifests,
    snapshot_current_artifact_manifest,
    validate_artifact_manifest,
    write_stage_artifact_manifest,
)
from infrastructure.core.pipeline.types import StageContract


def test_aggregate_preserves_declaration_from_an_earlier_stage(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project = repo_root / "projects" / "p"
    artifact = project / "output" / "data" / "result.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text('{"result": 1}\n', encoding="utf-8")

    write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=project,
        stage_num=1,
        stage_name="Analysis",
        contract=StageContract(output_artifacts=("projects/{project}/output/data/",)),
    )
    (project / "output" / "reports").mkdir()
    write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=project,
        stage_num=2,
        stage_name="Validation",
        contract=StageContract(output_artifacts=("projects/{project}/output/reports/",)),
    )

    aggregate = aggregate_artifact_manifests(project / "output")

    assert len(aggregate.entries) == 1
    assert aggregate.entries[0].path == "output/data/result.json"
    assert aggregate.entries[0].stage_name == "Validation"
    assert aggregate.entries[0].contract_match is True
    assert validate_artifact_manifest(aggregate, project_dir=project).issues == ()


def test_validation_self_reports_are_not_attested_recursively(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project = repo_root / "projects" / "p"
    data = project / "output" / "data" / "result.json"
    report = project / "output" / "reports" / "validation_report.json"
    diagnostics = project / "output" / "reports" / "diagnostics.json"
    readiness = project / "output" / "reports" / "autoresearch_readiness.json"
    data.parent.mkdir(parents=True)
    report.parent.mkdir(parents=True)
    data.write_text('{"result": 1}\n', encoding="utf-8")
    report.write_text('{"summary": {"all_passed": true}}\n', encoding="utf-8")
    diagnostics.write_text('{"events": []}\n', encoding="utf-8")
    readiness.write_text('{"valid": true}\n', encoding="utf-8")

    write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=project,
        stage_num=1,
        stage_name="Validation",
        contract=StageContract(output_artifacts=("projects/{project}/output/",)),
    )
    aggregate = aggregate_artifact_manifests(project / "output")
    report.write_text('{"summary": {"all_passed": false}}\n', encoding="utf-8")

    assert [entry.path for entry in aggregate.entries] == ["output/data/result.json"]
    assert validate_artifact_manifest(aggregate, project_dir=project).issues == ()


def test_current_output_snapshot_rebaselines_without_inventing_stage_provenance(tmp_path: Path) -> None:
    project = tmp_path / "repo" / "projects" / "p"
    artifact = project / "output" / "data" / "result.json"
    cached_fulltext = project / "output" / "fulltext" / "provider-paper.txt"
    validation_report = project / "output" / "reports" / "validation_report.json"
    artifact.parent.mkdir(parents=True)
    cached_fulltext.parent.mkdir(parents=True)
    validation_report.parent.mkdir(parents=True)
    artifact.write_text('{"result": 1}\n', encoding="utf-8")
    cached_fulltext.write_text("provider-controlled full text\n", encoding="utf-8")
    validation_report.write_text('{"summary": {"all_passed": true}}\n', encoding="utf-8")

    first = snapshot_current_artifact_manifest(project / "output")
    second = snapshot_current_artifact_manifest(project / "output")

    assert first.to_dict() == second.to_dict()
    assert [entry.path for entry in first.entries] == ["output/data/result.json"]
    assert first.entries[0].stage_name == "current-output-snapshot"
    assert first.entries[0].timestamp == ""
    assert validate_artifact_manifest(first, project_dir=project).issues == ()

    artifact.write_text('{"result": 2}\n', encoding="utf-8")
    assert "changed artifact" in "\n".join(validate_artifact_manifest(first, project_dir=project).issues)


def test_current_output_snapshot_sanitizes_before_hashing(tmp_path: Path) -> None:
    project = tmp_path / "repo" / "projects" / "p"
    artifact = project / "output" / "data" / "result.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text('{"path": "/home/alice/work/result.csv"}\n', encoding="utf-8")

    manifest = snapshot_current_artifact_manifest(project / "output")

    assert artifact.read_text(encoding="utf-8") == '{"path": "<home>/work/result.csv"}\n'
    assert validate_artifact_manifest(manifest, project_dir=project).issues == ()


def test_refresh_manifest_maintenance_cli_uses_qualified_project(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    artifact = root / "projects" / "templates" / "demo" / "output" / "data" / "result.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text('{"result": 1}\n', encoding="utf-8")
    script = Path(__file__).parents[3] / "scripts" / "maintenance" / "refresh_artifact_manifests.py"

    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--repo-root",
            str(root),
            "--project",
            "templates/demo",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "PASS templates/demo: 1 stable artifacts" in completed.stdout
    payload = json.loads((artifact.parents[1] / "reports" / "artifact_manifest.json").read_text(encoding="utf-8"))
    assert payload["entries"][0]["stage_name"] == "current-output-snapshot"
