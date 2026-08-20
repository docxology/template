"""Behavioral regressions for cross-stage artifact ownership and self-reports."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.core.pipeline.artifacts import (
    STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    STABLE_OUTPUT_INVENTORY_MODE,
    ArtifactManifest,
    ArtifactManifestEntry,
    _git_ignore_matches,
    aggregate_artifact_manifests,
    artifact_manifest_from_payload,
    collect_current_artifact_manifest,
    collect_stable_output_inventory,
    compute_sha256,
    snapshot_current_artifact_manifest,
    validate_artifact_manifest,
    write_stage_artifact_manifest,
)
from infrastructure.core.pipeline.types import StageContract
from infrastructure.validation.output.artifacts import current_project_manifest_if_valid, read_artifact_manifest


def test_legacy_manifest_reader_defaults_to_strict_shippable_mode(tmp_path: Path) -> None:
    manifest_path = tmp_path / "artifact_manifest.json"
    manifest_path.write_text('{"entries": [], "issues": []}\n', encoding="utf-8")

    manifest = read_artifact_manifest(manifest_path)

    assert manifest.inventory_mode == STABLE_OUTPUT_INVENTORY_MODE
    assert manifest.to_dict()["inventory_mode"] == STABLE_OUTPUT_INVENTORY_MODE


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("contract_match", "false"),
        ("size_bytes", 1.5),
        ("stage_num", "1"),
        ("sha256", "A" * 64),
        ("path", "output\\data\\result.json"),
        ("path", "output/data/../secret.json"),
        ("path", "output//data.json"),
        ("path", "output/C:/secret.json"),
        ("path", "output/data/nul\0.json"),
        ("timestamp", 0),
    ],
)
def test_manifest_parser_rejects_coerced_or_noncanonical_entry_fields(
    field: str,
    invalid: object,
) -> None:
    entry: dict[str, object] = {
        "path": "output/data/result.json",
        "size_bytes": 3,
        "sha256": "0" * 64,
        "stage_num": 1,
        "stage_name": "Analysis",
        "contract_match": False,
        "timestamp": "",
    }
    entry[field] = invalid

    with pytest.raises(ValueError):
        artifact_manifest_from_payload({"entries": [entry], "issues": []})


def test_manifest_parser_rejects_non_string_issues() -> None:
    with pytest.raises(ValueError, match="list of strings"):
        artifact_manifest_from_payload({"entries": [], "issues": [7]})


def test_manifest_parser_preserves_nul_safe_newline_path() -> None:
    payload = {
        "entries": [
            {
                "path": "output/data/line\nbreak.json",
                "size_bytes": 3,
                "sha256": "0" * 64,
                "stage_num": 1,
                "stage_name": "Analysis",
                "contract_match": True,
                "timestamp": "",
            }
        ],
        "issues": [],
    }

    parsed = artifact_manifest_from_payload(payload)

    assert parsed.entries[0].path == "output/data/line\nbreak.json"


def test_local_manifest_roundtrip_preserves_inventory_mode(tmp_path: Path) -> None:
    output = tmp_path / "private-project" / "output"
    result = output / "data" / "result.json"
    result.parent.mkdir(parents=True)
    result.write_text('{"result": 1}\n', encoding="utf-8")

    written = snapshot_current_artifact_manifest(
        output,
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )
    loaded = read_artifact_manifest(output / "reports" / "artifact_manifest.json")

    assert written.inventory_mode == STABLE_LOCAL_OUTPUT_INVENTORY_MODE
    assert loaded == written
    assert (
        current_project_manifest_if_valid(
            output,
            output.parent,
            expected_inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
        )
        == written
    )
    assert current_project_manifest_if_valid(output, output.parent) is None


def test_local_aggregate_inherits_unspecified_legacy_stage_mode_but_rejects_explicit_conflict(
    tmp_path: Path,
) -> None:
    project = tmp_path / "private-project"
    output = project / "output"
    result = output / "data" / "result.json"
    result.parent.mkdir(parents=True)
    result.write_text('{"result": 1}\n', encoding="utf-8")
    stage_path = output / ".pipeline" / "artifacts" / "stage-01-analysis.json"
    stage_path.parent.mkdir(parents=True)
    payload = {
        "entries": [
            {
                "path": "output/data/result.json",
                "size_bytes": result.stat().st_size,
                "sha256": compute_sha256(result),
                "stage_num": 1,
                "stage_name": "Analysis",
                "contract_match": True,
                "timestamp": "",
            }
        ],
        "issues": [],
    }
    stage_path.write_text(json.dumps(payload), encoding="utf-8")

    inherited = aggregate_artifact_manifests(
        output,
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    assert inherited.inventory_mode == STABLE_LOCAL_OUTPUT_INVENTORY_MODE
    assert inherited.issues == ()

    payload["inventory_mode"] = STABLE_OUTPUT_INVENTORY_MODE
    stage_path.write_text(json.dumps(payload), encoding="utf-8")
    contradictory = aggregate_artifact_manifests(
        output,
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    assert contradictory.inventory_mode == STABLE_LOCAL_OUTPUT_INVENTORY_MODE
    assert contradictory.issues == (
        "stage artifact manifest inventory mode mismatch: "
        "stage-01-analysis.json: expected stable-local-output-v1, found stable-shippable-output-v1",
    )


def test_strict_manifest_rejects_git_ignored_entry_even_when_mode_label_matches(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    project = repo / "projects" / "templates" / "demo"
    stable = project / "output" / "data" / "public.json"
    ignored = project / "output" / "data" / "private.json"
    for path in (stable, ignored):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
    (repo / ".gitignore").write_text(
        "projects/templates/demo/output/data/private.json\n",
        encoding="utf-8",
    )
    manifest = ArtifactManifest(
        entries=(
            ArtifactManifestEntry(
                path="output/data/public.json",
                size_bytes=stable.stat().st_size,
                sha256=compute_sha256(stable),
                stage_num=1,
                stage_name="Analysis",
                contract_match=True,
            ),
            ArtifactManifestEntry(
                path="output/data/private.json",
                size_bytes=ignored.stat().st_size,
                sha256=compute_sha256(ignored),
                stage_num=1,
                stage_name="Analysis",
                contract_match=True,
            ),
        ),
    )

    validation = validate_artifact_manifest(
        manifest,
        project_dir=project,
        expected_inventory_mode=STABLE_OUTPUT_INVENTORY_MODE,
    )

    assert validation.issues == ("artifact outside stable-shippable-output-v1 inventory: output/data/private.json",)


def test_manifest_rejects_explicit_hidden_control_and_backslash_paths(tmp_path: Path) -> None:
    project = tmp_path / "project"
    hidden = project / "output" / "data" / ".secret"
    control = project / "output" / "logs" / "private.log"
    for path in (hidden, control):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("private\n", encoding="utf-8")
    entries = tuple(
        ArtifactManifestEntry(
            path=relative,
            size_bytes=path.stat().st_size,
            sha256=compute_sha256(path),
            stage_num=1,
            stage_name="Analysis",
            contract_match=True,
        )
        for relative, path in (
            ("output/data/.secret", hidden),
            ("output/logs/private.log", control),
        )
    ) + (
        ArtifactManifestEntry(
            path="output\\data\\result.json",
            size_bytes=0,
            sha256="",
            stage_num=1,
            stage_name="Analysis",
            contract_match=True,
        ),
    )

    validation = validate_artifact_manifest(ArtifactManifest(entries=entries), project_dir=project)

    assert validation.issues == (
        "non-stable artifact forbidden: output/data/.secret",
        "non-stable artifact forbidden: output/logs/private.log",
        "unsafe artifact path: output\\data\\result.json",
    )


def test_manifest_validator_rejects_duplicate_entry_paths(tmp_path: Path) -> None:
    project = tmp_path / "project"
    artifact = project / "output" / "data" / "result.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}\n", encoding="utf-8")
    entry = ArtifactManifestEntry(
        path="output/data/result.json",
        size_bytes=artifact.stat().st_size,
        sha256=compute_sha256(artifact),
        stage_num=1,
        stage_name="Analysis",
        contract_match=True,
    )

    validation = validate_artifact_manifest(
        ArtifactManifest(entries=(entry, entry)),
        project_dir=project,
    )

    assert validation.issues == ("duplicate artifact path: output/data/result.json",)


def test_manifest_validator_rejects_unattested_stable_inventory_member(tmp_path: Path) -> None:
    project = tmp_path / "project"
    first = project / "output" / "data" / "first.json"
    second = project / "output" / "data" / "second.json"
    for path in (first, second):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
    manifest = ArtifactManifest(
        entries=(
            ArtifactManifestEntry(
                path="output/data/first.json",
                size_bytes=first.stat().st_size,
                sha256=compute_sha256(first),
                stage_num=1,
                stage_name="Analysis",
                contract_match=True,
            ),
        )
    )

    validation = validate_artifact_manifest(
        manifest,
        project_dir=project,
        expected_inventory_mode=STABLE_OUTPUT_INVENTORY_MODE,
    )

    assert validation.issues == ("unattested stable artifact: output/data/second.json",)


def test_git_ignore_query_distinguishes_errors_malformed_output_and_valid_no_match(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "project" / "output" / "data" / "result.json"
    candidate.parent.mkdir(parents=True)
    candidate.write_text("{}\n", encoding="utf-8")

    unavailable = _git_ignore_matches(
        (candidate,),
        candidate.parent,
        command=(str(tmp_path / "missing-git"),),
    )

    exit_two = tmp_path / "exit_two.py"
    exit_two.write_text("raise SystemExit(2)\n", encoding="utf-8")
    failed = _git_ignore_matches(
        (candidate,),
        candidate.parent,
        command=(sys.executable, str(exit_two)),
    )

    malformed_script = tmp_path / "malformed.py"
    malformed_script.write_text(
        "import sys\nsys.stdout.buffer.write(b'incomplete\\0')\n",
        encoding="utf-8",
    )
    malformed = _git_ignore_matches(
        (candidate,),
        candidate.parent,
        command=(sys.executable, str(malformed_script)),
    )

    no_match_script = tmp_path / "no_match.py"
    no_match_script.write_text("raise SystemExit(1)\n", encoding="utf-8")
    no_match = _git_ignore_matches(
        (candidate,),
        candidate.parent,
        command=(sys.executable, str(no_match_script)),
    )

    assert unavailable.error == "git check-ignore unavailable"
    assert failed.error == "git check-ignore exited with status 2"
    assert malformed.error == "git check-ignore returned malformed output"
    assert no_match.ok is True
    assert no_match.matches == {}


def test_git_ignore_unavailable_blocks_a_worktree_but_not_a_nonrepo_static_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo_file = repo / "output" / "data" / "result.json"
    repo_file.parent.mkdir(parents=True)
    repo_file.write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
    nonrepo_file = tmp_path / "nonrepo" / "output" / "data" / "result.json"
    nonrepo_file.parent.mkdir(parents=True)
    nonrepo_file.write_text("{}\n", encoding="utf-8")
    empty_path = tmp_path / "empty-path"
    empty_path.mkdir()
    monkeypatch.setenv("PATH", str(empty_path))

    blocked = collect_stable_output_inventory(repo / "output")
    fallback = collect_stable_output_inventory(nonrepo_file.parents[2] / "output")

    assert blocked.files == ()
    assert blocked.issues == ("git ignore evaluation failed: git check-ignore unavailable",)
    assert fallback.issues == ()
    assert [path.name for path in fallback.files] == ["result.json"]


def test_aggregate_and_current_inventory_both_retain_allowlisted_fulltext_inventory(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    project = repo / "projects" / "working" / "demo"
    inventory_path = project / "output" / "fulltext" / "fulltext_inventory.json"
    inventory_path.parent.mkdir(parents=True)
    inventory_path.write_text('{"schema_version": "inventory/1"}\n', encoding="utf-8")
    write_stage_artifact_manifest(
        repo_root=repo,
        project_dir=project,
        stage_num=2,
        stage_name="Analysis",
        contract=StageContract(output_artifacts=("projects/{project}/output/fulltext/",)),
    )

    aggregate = aggregate_artifact_manifests(
        project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )
    current = collect_current_artifact_manifest(
        project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    expected = ["output/fulltext/fulltext_inventory.json"]
    assert [entry.path for entry in aggregate.entries] == expected
    assert [entry.path for entry in current.entries] == expected
    assert (
        validate_artifact_manifest(
            aggregate,
            project_dir=project,
            expected_inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
        ).issues
        == ()
    )


def test_fulltext_inventory_allowlist_is_scoped_to_exact_canonical_path(tmp_path: Path) -> None:
    output = tmp_path / "project" / "output"
    exact = output / "fulltext" / "fulltext_inventory.json"
    ordinary_visible = output / "data" / "fulltext_inventory.json"
    forbidden = [
        output / category / "fulltext_inventory.json"
        for category in ("logs", "hitl", "snapshots", "llm", "translations")
    ]
    for path in (exact, ordinary_visible, *forbidden):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"schema_version": "inventory/1"}\n', encoding="utf-8")

    inventory = collect_stable_output_inventory(
        output,
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    assert inventory.issues == ()
    assert [path.relative_to(output).as_posix() for path in inventory.files] == [
        "data/fulltext_inventory.json",
        "fulltext/fulltext_inventory.json",
    ]


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
    (output / "render.log").write_text("noise\n", encoding="utf-8")

    manifest = snapshot_current_artifact_manifest(project / "output")
    recorded = {entry.path for entry in manifest.entries}
    assert "output/data/results.json" in recorded
    assert "output/data/render.log" not in recorded, "static suffix exclusions must still apply"


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
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Git-ignore evaluation and admission must consume one traversal snapshot."""
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
    real_git = shutil.which("git")
    assert real_git is not None
    wrapper_dir = tmp_path / "git-wrapper"
    wrapper_dir.mkdir()
    wrapper = wrapper_dir / "git"
    wrapper.write_text(
        "#!/usr/bin/env python3\n"
        "import os\n"
        "from pathlib import Path\n"
        "import sys\n"
        "late = Path(os.environ['TEMPLATE_TEST_LATE_IGNORED'])\n"
        "deleted = Path(os.environ['TEMPLATE_TEST_DELETED'])\n"
        "replaced = Path(os.environ['TEMPLATE_TEST_REPLACED'])\n"
        "if 'check-ignore' in sys.argv and not late.exists():\n"
        "    late.write_text('ignored but too late for this snapshot\\n', encoding='utf-8')\n"
        "    deleted.unlink()\n"
        "    replaced.unlink()\n"
        "    replaced.write_text('replacement with a different identity and size\\n', encoding='utf-8')\n"
        "real_git = os.environ['TEMPLATE_TEST_REAL_GIT']\n"
        "os.execv(real_git, [real_git, *sys.argv[1:]])\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    monkeypatch.setenv("TEMPLATE_TEST_LATE_IGNORED", str(late_ignored))
    monkeypatch.setenv("TEMPLATE_TEST_DELETED", str(deleted))
    monkeypatch.setenv("TEMPLATE_TEST_REPLACED", str(replaced))
    monkeypatch.setenv("TEMPLATE_TEST_REAL_GIT", real_git)
    monkeypatch.setenv("PATH", f"{wrapper_dir}{os.pathsep}{os.environ['PATH']}")

    inventory = collect_stable_output_inventory(project / "output")

    assert late_ignored.is_file(), "interleaving precondition: the late ignored file was created"
    assert inventory.issues == ()
    assert inventory.files == (stable,)


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


def test_whole_ignored_project_output_uses_explicit_stable_local_mode(tmp_path: Path) -> None:
    """Private project output remains testable without claiming Git shippability."""
    project = tmp_path / "private-project"
    stable = project / "output" / "data" / "result.json"
    hidden = project / "output" / "data" / ".private" / "token.txt"
    runtime = project / "output" / "logs" / "pipeline.log"
    renderer_intermediate = project / "output" / "pdf" / "_combined_manuscript.tex"
    for path in (stable, hidden, runtime, renderer_intermediate):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("payload\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True, capture_output=True)
    (project / ".gitignore").write_text("output/\n", encoding="utf-8")

    strict = collect_stable_output_inventory(project / "output")
    inventory = collect_stable_output_inventory(
        project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    assert strict.mode == "stable-shippable-output-v1"
    assert strict.files == ()
    assert inventory.mode == "stable-local-output-v1"
    assert [path.relative_to(project / "output").as_posix() for path in inventory.files] == ["data/result.json"]


@pytest.mark.parametrize("blanket_rule", ["output/", "output/*", "output/**"])
def test_stable_local_mode_bypasses_equivalent_blanket_packaging_rules(
    tmp_path: Path,
    blanket_rule: str,
) -> None:
    project = tmp_path / "private-project"
    stable = project / "output" / "data" / "result.json"
    stable.parent.mkdir(parents=True)
    stable.write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True, capture_output=True)
    (project / ".gitignore").write_text(blanket_rule + "\n", encoding="utf-8")

    inventory = collect_stable_output_inventory(
        project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    assert [path.relative_to(project / "output").as_posix() for path in inventory.files] == ["data/result.json"]


def test_stable_local_mode_still_honors_selective_git_ignores(tmp_path: Path) -> None:
    project = tmp_path / "private-project"
    stable = project / "output" / "data" / "result.json"
    scratch = project / "output" / "data" / "local.scratch"
    for path in (stable, scratch):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("payload\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True, capture_output=True)
    (project / ".gitignore").write_text("output/data/*.scratch\n", encoding="utf-8")

    inventory = collect_stable_output_inventory(
        project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    assert [path.relative_to(project / "output").as_posix() for path in inventory.files] == ["data/result.json"]


def test_stable_local_mode_does_not_misclassify_extension_ignore_as_blanket(tmp_path: Path) -> None:
    project = tmp_path / "private-project"
    stable = project / "output" / "data" / "result.json"
    binary = project / "output" / "data" / "private.bin"
    for path in (stable, binary):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("payload\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True, capture_output=True)
    (project / ".gitignore").write_text("*.bin\n", encoding="utf-8")

    inventory = collect_stable_output_inventory(
        project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    assert [path.relative_to(project / "output").as_posix() for path in inventory.files] == ["data/result.json"]


def test_runtime_history_is_not_stable_but_regular_reports_are(tmp_path: Path) -> None:
    """Telemetry history stays local without hiding genuine stable reports."""
    project = tmp_path / "nogit"
    reports = project / "output" / "reports"
    history = reports / ".history"
    history.mkdir(parents=True)
    (history / "telemetry-123.json").write_text('{"runtime": true}\n', encoding="utf-8")
    (reports / "quality_summary.json").write_text('{"all_passed": true}\n', encoding="utf-8")

    manifest = snapshot_current_artifact_manifest(project / "output")

    recorded = {entry.path for entry in manifest.entries}
    assert "output/reports/.history/telemetry-123.json" not in recorded
    assert "output/reports/quality_summary.json" in recorded


def test_optional_full_evidence_registry_is_not_stable(tmp_path: Path) -> None:
    """The opt-in diagnostic registry cannot perturb publication statistics."""
    output = tmp_path / "project" / "output"
    result = output / "data" / "result.json"
    result.parent.mkdir(parents=True)
    result.write_text('{"measured": 7}\n', encoding="utf-8")

    baseline = collect_stable_output_inventory(output)
    debug_registry = output / "reports" / "evidence_registry_full.json"
    debug_registry.parent.mkdir(parents=True)
    debug_registry.write_text('{"debug_fact_count": 999}\n', encoding="utf-8")
    rerun = collect_stable_output_inventory(output)

    assert rerun == baseline
    assert debug_registry not in rerun.files


def test_runtime_history_is_gitignored_after_public_template_negations() -> None:
    """Post-negation rules must ignore project history and the generated mirror."""
    repo_root = Path(__file__).resolve().parents[3]
    candidates = (
        "projects/templates/template_code_project/output/reports/.history/telemetry-123.json",
        "projects/templates/template_code_project/output/reports/diagnostics.json",
        "projects/templates/template_code_project/output/reports/evidence_registry_full.json",
        "output/templates/template_code_project/reports/.history/telemetry-123.json",
    )

    for candidate in candidates:
        completed = subprocess.run(
            ["git", "check-ignore", "--no-index", "--quiet", candidate],
            cwd=repo_root,
            check=False,
        )
        assert completed.returncode == 0, f"runtime history is not ignored: {candidate}"


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


def test_declared_output_paths_reject_parent_traversal(tmp_path: Path) -> None:
    """A projects/ prefix must not be enough to walk out of the repository."""
    from infrastructure.core.pipeline.artifacts import _declared_output_paths

    repo = tmp_path / "repo"
    project = repo / "projects" / "p"
    project.mkdir(parents=True)
    victim = tmp_path / "victim.txt"
    victim.write_text("SECRET_OUTSIDE\n", encoding="utf-8")

    with pytest.raises(ValueError, match="escapes confinement"):
        _declared_output_paths(repo, project, StageContract(output_artifacts=("projects/../victim.txt",)))
    assert victim.read_text(encoding="utf-8") == "SECRET_OUTSIDE\n"


def test_declared_output_paths_keep_in_repo_outputs(tmp_path: Path) -> None:
    from infrastructure.core.pipeline.artifacts import _declared_output_paths

    repo = tmp_path / "repo"
    project = repo / "projects" / "p"
    project.mkdir(parents=True)
    paths = _declared_output_paths(
        repo,
        project,
        StageContract(output_artifacts=("projects/{project}/output/data/result.json",)),
    )
    assert paths == (repo / "projects" / "p" / "output" / "data" / "result.json",)
