"""Manifest snapshot provenance, refresh CLI, and git-ignored artifact behavior."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest

from infrastructure.core.pipeline.artifacts import (
    STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    STABLE_OUTPUT_INVENTORY_MODE,
    aggregate_artifact_manifests,
    collect_stable_output_inventory,
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

    aggregate = aggregate_artifact_manifests(
        project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

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
    aggregate = aggregate_artifact_manifests(
        project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )
    report.write_text('{"summary": {"all_passed": false}}\n', encoding="utf-8")

    assert [entry.path for entry in aggregate.entries] == ["output/data/result.json"]
    assert validate_artifact_manifest(aggregate, project_dir=project).issues == ()


def test_current_output_snapshot_rebaselines_without_inventing_stage_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The CI setup exports SOURCE_DATE_EPOCH for deterministic build products,
    # but this snapshot contract deliberately omits even deterministic stage
    # timestamps: it is a current-output baseline, not stage provenance.
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
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
    assert payload["inventory_mode"] == STABLE_OUTPUT_INVENTORY_MODE


def test_refresh_validation_detects_stable_file_appearing_after_snapshot(tmp_path: Path) -> None:
    project = tmp_path / "private" / "demo"
    first = project / "output" / "data" / "first.json"
    first.parent.mkdir(parents=True)
    first.write_text("{}\n", encoding="utf-8")
    manifest = snapshot_current_artifact_manifest(
        project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )
    late = project / "output" / "data" / "late.json"
    late.write_text("{}\n", encoding="utf-8")

    validation = validate_artifact_manifest(
        manifest,
        project_dir=project,
        expected_inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    assert validation.issues == ("unattested stable artifact: output/data/late.json",)


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
    (output / "observations.log").write_text("measurement\n", encoding="utf-8")
    renderer_output = project / "output" / "pdf"
    renderer_output.mkdir()
    (renderer_output / "render.log").write_text("renderer intermediate\n", encoding="utf-8")

    manifest = snapshot_current_artifact_manifest(project / "output")
    recorded = {entry.path for entry in manifest.entries}
    assert "output/data/results.json" in recorded
    assert "output/data/observations.log" in recorded
    assert "output/pdf/render.log" not in recorded, "renderer intermediates remain excluded"


def test_copied_inventory_maps_git_ignores_to_canonical_source(tmp_path: Path) -> None:
    """An ignored delivery mirror must reuse source-scoped publication rules."""
    repo_root = tmp_path / "repo"
    source_output = repo_root / "projects" / "templates" / "demo" / "output"
    copied_output = repo_root / "output" / "templates" / "demo"
    for root in (source_output, copied_output):
        pdf_dir = root / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "demo_combined.pdf").write_bytes(b"%PDF-1.7\n")
        (pdf_dir / "_combined_manuscript.tex").write_text("intermediate\n", encoding="utf-8")
    (copied_output / "demo_combined.pdf").write_bytes(b"%PDF-1.7\n")

    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True, capture_output=True)
    (repo_root / ".gitignore").write_text(
        "/output/\n"
        "projects/templates/demo/output/**\n"
        "!projects/templates/demo/output/pdf/\n"
        "!projects/templates/demo/output/pdf/demo_combined.pdf\n",
        encoding="utf-8",
    )

    assert collect_stable_output_inventory(copied_output).files == ()

    mapped = collect_stable_output_inventory(
        copied_output,
        git_ignore_output_dir=source_output,
        git_ignore_path_overrides={Path("demo_combined.pdf"): Path("pdf/demo_combined.pdf")},
    )

    assert mapped.issues == ()
    assert [path.relative_to(copied_output).as_posix() for path in mapped.files] == [
        "demo_combined.pdf",
        "pdf/demo_combined.pdf",
    ]

    with pytest.raises(ValueError, match="invalid Git-ignore path override"):
        collect_stable_output_inventory(
            copied_output,
            git_ignore_output_dir=source_output,
            git_ignore_path_overrides={Path("demo_combined.pdf"): Path("../escape.pdf")},
        )


@pytest.mark.parametrize("name", ["café.scratch", "line\nbreak.scratch"])
def test_git_ignore_inventory_handles_unquoted_path_bytes(tmp_path: Path, name: str) -> None:
    """Unicode and newline names must round-trip through Git without quoting drift."""
    project = tmp_path / "project"
    data_dir = project / "output" / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "stable.json").write_text("{}\n", encoding="utf-8")
    (data_dir / name).write_text("ignored\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True, capture_output=True)
    (project / ".gitignore").write_text("output/data/*.scratch\n", encoding="utf-8")

    inventory = collect_stable_output_inventory(project / "output")

    assert inventory.issues == ()
    assert [path.name for path in inventory.files] == ["stable.json"]


def test_stable_inventory_does_not_admit_file_created_during_git_ignore_evaluation(
    tmp_path: Path,
) -> None:
    """Real Git runs after the traversal snapshot while fixture files change."""
    project = tmp_path / "project"
    data_dir = project / "output" / "data"
    data_dir.mkdir(parents=True)
    stable = data_dir / "stable.json"
    stable.write_text("{}\n", encoding="utf-8")
    deleted = data_dir / "deleted.json"
    replaced = data_dir / "replaced.json"
    deleted.write_text("delete me\n", encoding="utf-8")
    replaced.write_text("original\n", encoding="utf-8")
    late_ignored = data_dir / "late.scratch"
    subprocess.run(["git", "init", "-q"], cwd=project, check=True, capture_output=True)
    (project / ".gitignore").write_text("output/data/*.scratch\n", encoding="utf-8")
    script = tmp_path / "observe_real_git.py"
    script.write_text(
        dedent(
            """\
            import json
            import os
            from pathlib import Path
            import shutil
            import sys

            source_root, project = map(Path, sys.argv[1:])
            sys.path.insert(0, str(source_root))
            from infrastructure.core.pipeline.artifacts import collect_stable_output_inventory

            data = project / "output" / "data"
            late = data / "late.scratch"
            deleted = data / "deleted.json"
            replaced = data / "replaced.json"
            native_git = shutil.which("git", path=os.defpath)
            assert native_git is not None
            observations = []

            def observe(event, args):
                if event != "subprocess.Popen":
                    return
                executable, command, cwd, environment = args
                if "check-ignore" not in command:
                    return
                assert Path(executable).resolve() == Path(native_git).resolve()
                assert command[command.index("-C") + 1] == str(project)
                observations.append(command)
                if len(observations) == 1:
                    late.write_text("ignored but too late for this snapshot\\n", encoding="utf-8")
                    deleted.unlink()
                    replaced.unlink()
                    replaced.write_text("replacement with a different identity and size\\n", encoding="utf-8")

            # Audit hooks cannot be removed, so their lifetime belongs to this
            # isolated child. The observer changes only real fixture files;
            # subprocess execution and Git's actual result remain untouched.
            sys.addaudithook(observe)
            inventory = collect_stable_output_inventory(project / "output")
            assert len(observations) == 1, observations
            assert late.is_file(), "interleaving precondition: the late ignored file was created"
            assert not deleted.exists()
            assert replaced.read_text(encoding="utf-8").startswith("replacement ")
            assert inventory.issues == (), inventory.issues
            assert inventory.files == (data / "stable.json",), inventory.files
            print(json.dumps({"files": [str(path) for path in inventory.files], "git_calls": len(observations)}))
            """
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [sys.executable, "-I", "-B", str(script), str(Path(__file__).parents[3]), str(project)],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout) == {"files": [str(stable)], "git_calls": 1}
    assert late_ignored.is_file(), "interleaving precondition: the late ignored file was created"
    assert not deleted.exists()
    assert replaced.read_text(encoding="utf-8").startswith("replacement ")


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


def test_stable_inventory_excludes_every_hidden_path_component(tmp_path: Path) -> None:
    """Nested hidden caches and repository metadata can never become evidence."""
    output = tmp_path / "nogit" / "output"
    visible = output / "data" / "result.json"
    private_cache = output / "data" / ".private-cache" / "token.txt"
    git_config = output / ".git" / "config"
    for path, payload in (
        (visible, "{}\n"),
        (private_cache, "secret\n"),
        (git_config, "[core]\n"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")

    inventory = collect_stable_output_inventory(output)

    assert inventory.issues == ()
    assert [path.relative_to(output).as_posix() for path in inventory.files] == ["data/result.json"]
