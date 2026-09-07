"""Manifest validation: strict mode, hidden paths, duplicates, and git-ignore queries."""

from __future__ import annotations

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
    collect_current_artifact_manifest,
    collect_stable_output_inventory,
    compute_sha256,
    validate_artifact_manifest,
    write_stage_artifact_manifest,
)
from infrastructure.core.pipeline.types import StageContract


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
