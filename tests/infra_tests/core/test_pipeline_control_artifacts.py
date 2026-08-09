"""Tests for adaptive pipeline control surfaces.

These tests cover the AutoResearchClaw-inspired additions without making the
template pipeline autonomous: stage contracts, explicit hooks, lightweight HITL,
and run lessons remain opt-in and reproducible.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.pipeline.dag import PipelineDAG
from infrastructure.core.pipeline.artifacts import (
    ArtifactManifest,
    ArtifactManifestEntry,
    aggregate_artifact_manifests,
    validate_artifact_manifest,
    write_stage_artifact_manifest,
)
from infrastructure.validation.output.artifacts import current_project_manifest_if_valid
from infrastructure.core.pipeline.types import (
    StageContract,
)


def test_stage_artifact_manifest_records_hashes_and_contract_issues(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_dir = repo_root / "projects" / "p"
    (project_dir / "output" / "data").mkdir(parents=True)
    (project_dir / "output" / "logs").mkdir()
    (project_dir / "output" / ".checkpoints").mkdir()
    (project_dir / "output" / "reports" / "snapshots").mkdir(parents=True)
    (project_dir / "output" / "data" / "result.json").write_text('{"ok": true}\n', encoding="utf-8")
    (project_dir / "output" / "logs" / "pipeline.log").write_text("ignore me\n", encoding="utf-8")
    (project_dir / "output" / ".checkpoints" / "pipeline_checkpoint.json").write_text("{}", encoding="utf-8")
    (project_dir / "output" / "reports" / "artifact_manifest.json").write_text("{}", encoding="utf-8")
    (project_dir / "output" / "reports" / "evidence_registry.json").write_text("{}", encoding="utf-8")
    (project_dir / "output" / "reports" / "snapshots" / "stage-01.json").write_text("{}", encoding="utf-8")
    (project_dir / "output" / "slides").mkdir()
    (project_dir / "output" / "slides" / "section_slides.aux").write_text("ignore me\n", encoding="utf-8")
    contract = StageContract(output_artifacts=("projects/{project}/output/data/", "projects/{project}/output/pdf/"))

    manifest = write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=project_dir,
        stage_num=4,
        stage_name="Project Analysis",
        contract=contract,
    )
    aggregate = aggregate_artifact_manifests(project_dir / "output")
    validation = validate_artifact_manifest(aggregate)

    assert manifest.entries[0].sha256
    assert manifest.entries[0].contract_match is True
    assert all("logs/" not in entry.path for entry in manifest.entries)
    assert all(".checkpoints/" not in entry.path for entry in manifest.entries)
    assert all("artifact_manifest.json" not in entry.path for entry in manifest.entries)
    assert all("evidence_registry.json" not in entry.path for entry in manifest.entries)
    assert all("snapshots/" not in entry.path for entry in manifest.entries)
    assert all(not entry.path.endswith(".aux") for entry in manifest.entries)
    assert any("missing declared output" in issue for issue in validation.issues)
    assert (project_dir / "output" / "reports" / "artifact_manifest.json").exists()


def test_aggregate_artifact_manifest_scans_outputs_without_stage_manifests(tmp_path: Path) -> None:
    project_dir = tmp_path / "projects" / "p"
    output_file = project_dir / "output" / "data" / "result.json"
    output_file.parent.mkdir(parents=True)
    output_file.write_text('{"ok": true}\n', encoding="utf-8")

    aggregate = aggregate_artifact_manifests(project_dir / "output")
    validation = validate_artifact_manifest(aggregate, project_dir=project_dir)

    assert len(aggregate.entries) == 1
    assert aggregate.entries[0].path == "output/data/result.json"
    assert aggregate.entries[0].stage_name == "standalone-output-scan"
    assert validation.issues == ()


@pytest.mark.parametrize("target_is_directory", [False, True])
def test_artifact_manifests_reject_output_symlinks(tmp_path: Path, target_is_directory: bool) -> None:
    repo_root = tmp_path / "repo"
    project_dir = repo_root / "projects" / "p"
    output_dir = project_dir / "output"
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True)
    outside = tmp_path / ("outside-dir" if target_is_directory else "outside.txt")
    if target_is_directory:
        outside.mkdir()
        (outside / "private.txt").write_text("private", encoding="utf-8")
    else:
        outside.write_text("private", encoding="utf-8")
    linked = data_dir / "linked"
    linked.symlink_to(outside, target_is_directory=target_is_directory)

    stage = write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=project_dir,
        stage_num=4,
        stage_name="Project Analysis",
        contract=StageContract(output_artifacts=("projects/{project}/output/data/",)),
    )
    aggregate = aggregate_artifact_manifests(output_dir)
    validation = validate_artifact_manifest(aggregate, project_dir=project_dir)

    assert stage.entries == ()
    assert "symlink artifact forbidden: data/linked" in stage.issues
    assert all(entry.path != "output/data/linked" for entry in aggregate.entries)
    assert "symlink artifact forbidden: data/linked" in validation.issues


def test_artifact_manifest_validation_rejects_path_escape(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    outside = tmp_path / "private.txt"
    outside.write_text("private", encoding="utf-8")
    manifest = ArtifactManifest(
        entries=(
            ArtifactManifestEntry(
                path="../private.txt",
                size_bytes=outside.stat().st_size,
                sha256="not-trusted",
                stage_num=0,
                stage_name="malicious",
                contract_match=True,
            ),
        )
    )

    validation = validate_artifact_manifest(manifest, project_dir=project_dir)

    assert validation.issues == ("unsafe artifact path: ../private.txt",)


def test_manifest_writers_reject_symlinked_control_destinations(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_dir = repo_root / "projects" / "p"
    output_dir = project_dir / "output"
    output_dir.mkdir(parents=True)
    outside_stage = tmp_path / "outside-stage"
    outside_stage.mkdir()
    (output_dir / ".pipeline").symlink_to(outside_stage, target_is_directory=True)

    with pytest.raises(ValueError, match="write a manifest through symlink"):
        write_stage_artifact_manifest(
            repo_root=repo_root,
            project_dir=project_dir,
            stage_num=1,
            stage_name="Unsafe",
            contract=StageContract(),
        )
    assert list(outside_stage.iterdir()) == []

    (output_dir / ".pipeline").unlink()
    outside_report = tmp_path / "outside-report"
    outside_report.mkdir()
    (output_dir / "reports").symlink_to(outside_report, target_is_directory=True)

    with pytest.raises(ValueError, match="aggregate manifest through symlink"):
        aggregate_artifact_manifests(output_dir)
    assert list(outside_report.iterdir()) == []


def test_empty_project_manifest_is_not_accepted_when_outputs_exist(tmp_path: Path) -> None:
    project_dir = tmp_path / "projects" / "p"
    output_dir = project_dir / "output"
    (output_dir / "pdf").mkdir(parents=True)
    (output_dir / "pdf" / "book.pdf").write_bytes(b"%PDF-1.7\n")
    (output_dir / "reports").mkdir()
    (output_dir / "reports" / "artifact_manifest.json").write_text('{"entries": [], "issues": []}\n', encoding="utf-8")

    assert current_project_manifest_if_valid(output_dir, project_dir) is None


def test_stage_artifact_manifest_accepts_symlinked_private_project_contracts(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    private_root = tmp_path / "private" / "active"
    project_dir = private_root / "p"
    linked_project = repo_root / "projects" / "p"
    output_file = project_dir / "output" / "data" / "result.json"
    output_file.parent.mkdir(parents=True)
    linked_project.parent.mkdir(parents=True)
    linked_project.symlink_to(project_dir, target_is_directory=True)
    output_file.write_text('{"ok": true}\n', encoding="utf-8")

    manifest = write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=project_dir,
        stage_num=4,
        stage_name="Project Analysis",
        contract=StageContract(output_artifacts=("projects/{project}/output/data/",)),
    )
    validation = validate_artifact_manifest(manifest, project_dir=project_dir)

    assert [entry.contract_match for entry in manifest.entries] == [True]
    assert validation.issues == ()


def test_stage_artifact_manifest_preserves_lifecycle_slug_for_symlinked_working_project(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    private_project = tmp_path / "private" / "working" / "AGEINT"
    linked_project = repo_root / "projects" / "working" / "AGEINT"
    output_file = private_project / "output" / "reports" / "result.json"
    copied_output = repo_root / "output" / "working" / "AGEINT" / "manifest.json"
    output_file.parent.mkdir(parents=True)
    copied_output.parent.mkdir(parents=True)
    linked_project.parent.mkdir(parents=True)
    linked_project.symlink_to(private_project, target_is_directory=True)
    output_file.write_text('{"ok": true}\n', encoding="utf-8")
    copied_output.write_text('{"ok": true}\n', encoding="utf-8")

    manifest = write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=private_project,
        stage_num=9,
        stage_name="Copy Outputs",
        contract=StageContract(
            output_artifacts=(
                "projects/{project}/output/reports/",
                "output/{project}/",
            )
        ),
    )
    validation = validate_artifact_manifest(manifest, project_dir=private_project)

    assert manifest.issues == ()
    assert [entry.contract_match for entry in manifest.entries] == [True]
    assert validation.issues == ()


def test_stage_artifact_manifest_uses_qualified_template_project_slug(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_dir = repo_root / "projects" / "templates" / "template_active_inference"
    project_output = project_dir / "output" / "data" / "result.json"
    copied_output = repo_root / "output" / "templates" / "template_active_inference" / "data" / "result.json"
    project_output.parent.mkdir(parents=True)
    copied_output.parent.mkdir(parents=True)
    project_output.write_text('{"ok": true}\n', encoding="utf-8")
    copied_output.write_text('{"ok": true}\n', encoding="utf-8")

    manifest = write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=project_dir,
        stage_num=8,
        stage_name="Copy Outputs",
        contract=StageContract(
            output_artifacts=(
                "projects/{project}/output/data/",
                "output/{project}/data/",
            )
        ),
    )
    validation = validate_artifact_manifest(manifest, project_dir=project_dir)

    assert [entry.contract_match for entry in manifest.entries] == [True]
    assert validation.issues == ()


def test_default_environment_setup_contract_allows_setup_hook_outputs() -> None:
    pipeline_path = Path(__file__).resolve().parents[3] / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
    dag = PipelineDAG.from_yaml(pipeline_path)
    setup = next(stage for stage in dag.stages if stage.name == "Environment Setup")

    assert "projects/{project}/output/" in setup.contract.output_artifacts


def test_default_test_stage_contracts_allow_generated_project_outputs() -> None:
    pipeline_path = Path(__file__).resolve().parents[3] / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
    dag = PipelineDAG.from_yaml(pipeline_path)
    test_stages = {stage.name: stage for stage in dag.stages if stage.name in {"Infrastructure Tests", "Project Tests"}}

    assert test_stages["Infrastructure Tests"].contract.output_artifacts == ("projects/{project}/output/",)
    assert test_stages["Project Tests"].contract.output_artifacts == ("projects/{project}/output/",)


def test_stage_artifact_manifest_detects_changed_hash(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_dir = repo_root / "projects" / "p"
    output_file = project_dir / "output" / "data" / "result.json"
    output_file.parent.mkdir(parents=True)
    output_file.write_text('{"ok": true}\n', encoding="utf-8")

    manifest = write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=project_dir,
        stage_num=4,
        stage_name="Project Analysis",
        contract=StageContract(output_artifacts=("projects/{project}/output/data/",)),
    )
    output_file.write_text('{"ok": false}\n', encoding="utf-8")

    validation = validate_artifact_manifest(manifest, project_dir=project_dir)

    assert any("changed artifact" in issue for issue in validation.issues)


def test_stage_artifact_manifest_validates_latest_hash_per_path(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_dir = repo_root / "projects" / "p"
    output_file = project_dir / "output" / "data" / "result.json"
    output_file.parent.mkdir(parents=True)
    output_file.write_text('{"ok": true}\n', encoding="utf-8")

    write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=project_dir,
        stage_num=4,
        stage_name="Project Analysis",
        contract=StageContract(output_artifacts=("projects/{project}/output/data/",)),
    )
    output_file.write_text('{"ok": false}\n', encoding="utf-8")
    write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=project_dir,
        stage_num=5,
        stage_name="PDF Rendering",
        contract=StageContract(output_artifacts=("projects/{project}/output/data/",)),
    )

    aggregate = aggregate_artifact_manifests(project_dir / "output")
    validation = validate_artifact_manifest(aggregate, project_dir=project_dir)

    assert not any("changed artifact" in issue for issue in validation.issues)


def test_stage_artifact_manifest_reemits_unchanged_artifacts(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_dir = repo_root / "projects" / "p"
    output_file = project_dir / "output" / "data" / "result.json"
    output_file.parent.mkdir(parents=True)
    output_file.write_text('{"ok": true}\n', encoding="utf-8")

    first = write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=project_dir,
        stage_num=4,
        stage_name="Project Analysis",
        contract=StageContract(output_artifacts=("projects/{project}/output/data/",)),
    )
    second = write_stage_artifact_manifest(
        repo_root=repo_root,
        project_dir=project_dir,
        stage_num=5,
        stage_name="PDF Rendering",
        contract=StageContract(output_artifacts=("projects/{project}/output/data/",)),
    )

    assert [entry.path for entry in first.entries] == ["output/data/result.json"]
    assert [entry.path for entry in second.entries] == ["output/data/result.json"]
