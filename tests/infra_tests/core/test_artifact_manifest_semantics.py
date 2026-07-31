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
    rendered_provenance = project / "output" / "reports" / "rendered_provenance.json"
    data.parent.mkdir(parents=True)
    report.parent.mkdir(parents=True)
    data.write_text('{"result": 1}\n', encoding="utf-8")
    report.write_text('{"summary": {"all_passed": true}}\n', encoding="utf-8")
    diagnostics.write_text('{"events": []}\n', encoding="utf-8")
    readiness.write_text('{"valid": true}\n', encoding="utf-8")
    rendered_provenance.write_text('{"schema_version": "receipt"}\n', encoding="utf-8")

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
    fulltext_inventory = project / "output" / "fulltext" / "fulltext_inventory.json"
    validation_report = project / "output" / "reports" / "validation_report.json"
    artifact.parent.mkdir(parents=True)
    cached_fulltext.parent.mkdir(parents=True)
    validation_report.parent.mkdir(parents=True)
    artifact.write_text('{"result": 1}\n', encoding="utf-8")
    cached_fulltext.write_text("provider-controlled full text\n", encoding="utf-8")
    fulltext_inventory.write_text('{"schema_version": "inventory/1"}\n', encoding="utf-8")
    validation_report.write_text('{"summary": {"all_passed": true}}\n', encoding="utf-8")

    first = snapshot_current_artifact_manifest(project / "output")
    second = snapshot_current_artifact_manifest(project / "output")

    assert first.to_dict() == second.to_dict()
    assert [entry.path for entry in first.entries] == [
        "output/data/result.json",
        "output/fulltext/fulltext_inventory.json",
    ]
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


def test_git_ignored_artifacts_are_never_recorded(tmp_path: Path) -> None:
    """A committed manifest must only reference files that can actually ship.

    Originating defect (2026-07-28): `template_code_project`'s tracked
    `artifact_manifest.json` listed 15 LaTeX intermediates (`.bbl`, `.blg`,
    `_combined_manuscript.tex`, `references.bib`) that exist after a local render
    but are gitignored, so a fresh clone lacked them. Three `methods/` tests
    failed on every CI platform while passing locally, because locally the files
    were present. The static suffix list could not express path-scoped rules like
    `output/slides/**/*.tex`, so it had drifted from `.gitignore`; asking git
    removes the second source of truth.
    """
    import subprocess

    from infrastructure.core.pipeline.artifacts import snapshot_current_artifact_manifest

    project = tmp_path / "proj"
    output = project / "output" / "pdf"
    output.mkdir(parents=True)
    (output / "paper.pdf").write_bytes(b"%PDF-1.7\n")
    (output / "paper.bbl").write_text("bibliography intermediate\n", encoding="utf-8")

    subprocess.run(["git", "init", "-q"], cwd=project, check=True, capture_output=True)
    (project / ".gitignore").write_text("output/pdf/*.bbl\n", encoding="utf-8")

    manifest = snapshot_current_artifact_manifest(project / "output")
    recorded = {entry.path for entry in manifest.entries}
    assert "output/pdf/paper.pdf" in recorded
    assert "output/pdf/paper.bbl" not in recorded, "gitignored intermediates must not enter committed evidence"


def test_manifest_snapshot_still_works_outside_a_git_repository(tmp_path: Path) -> None:
    """Falling back must not silently drop artifacts.

    Unit trees under `tmp_path` are not repositories; when git cannot answer, the
    static exclusion lists still apply and real artifacts are still recorded.
    """
    from infrastructure.core.pipeline.artifacts import snapshot_current_artifact_manifest

    project = tmp_path / "nogit"
    output = project / "output" / "data"
    output.mkdir(parents=True)
    (output / "results.json").write_text("{}\n", encoding="utf-8")
    (output / "render.log").write_text("noise\n", encoding="utf-8")

    manifest = snapshot_current_artifact_manifest(project / "output")
    recorded = {entry.path for entry in manifest.entries}
    assert "output/data/results.json" in recorded
    assert "output/data/render.log" not in recorded, "static suffix exclusions must still apply"


def test_current_output_snapshot_omits_hidden_atomic_write_leftovers(tmp_path: Path) -> None:
    """Interrupted hidden writers must never become publication evidence."""
    project = tmp_path / "nogit"
    figures = project / "output" / "figures"
    figures.mkdir(parents=True)
    (figures / ".trace.png").write_bytes(b"transient payload")
    (figures / "trace.png").write_bytes(b"stable payload")

    manifest = snapshot_current_artifact_manifest(project / "output")

    recorded = {entry.path for entry in manifest.entries}
    assert "output/figures/trace.png" in recorded
    assert "output/figures/.trace.png" not in recorded


def test_every_public_exemplar_manifest_references_only_tracked_files() -> None:
    """Bind to the live tree — this is the assertion CI was failing on."""
    import json
    import subprocess

    from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

    repo_root = Path(__file__).resolve().parents[3]
    tracked = set(
        subprocess.run(["git", "ls-files"], cwd=repo_root, capture_output=True, text=True, check=True).stdout.split()
    )
    checked = 0
    offenders: list[str] = []
    for qualified in PUBLIC_PROJECT_NAMES:
        manifest_path = repo_root / "projects" / qualified / "output" / "reports" / "artifact_manifest.json"
        if f"projects/{qualified}/output/reports/artifact_manifest.json" not in tracked:
            continue
        checked += 1
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in payload.get("entries", []):
            rel = entry.get("path")
            if rel and f"projects/{qualified}/{rel}" not in tracked:
                offenders.append(f"{qualified}: {rel}")
    assert checked > 0, "no tracked exemplar manifests found — the scan set went empty"
    assert not offenders, offenders[:10]
