#!/usr/bin/env python3
"""Tests for infrastructure.publishing.repro_bundle (REPRO-BUNDLE-1).

No mocks: every test builds real files under ``tmp_path`` and exercises the
builder/verifier on those real bytes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.core.pipeline.artifacts import (
    STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    snapshot_current_artifact_manifest,
)
from infrastructure.publishing._repro_bundle_verify import collect_schema_findings
from infrastructure.publishing.repro_bundle import (
    BUNDLE_MANIFEST_NAME,
    SCHEMA_VERSION,
    build_public_repro_bundles,
    build_repro_bundle,
    main,
    verify_repro_bundle,
)
from tests._support.projects import make_project, write_doc


def _scaffold_repro_project(root: Path, name: str) -> Path:
    """Create a synthetic exemplar with a lockfile, artifact manifest, and outputs."""
    project = make_project(root, name, with_manuscript=True, with_scripts=True)
    (project / "src" / "demo.py").write_text("def run() -> int:\n    return 0\n", encoding="utf-8")

    # Repo-level reproduction inputs.
    write_doc(root / "uv.lock", "# lock contents\n")
    write_doc(root / "pyproject.toml", "[project]\nname = 'demo'\n")
    write_doc(root / "docs" / "_generated" / "COUNTS.md", "# Canonical Facts\n\n- 214\n")

    # Declared output artifacts live UNDER the project dir, and the artifact
    # manifest stores their paths relative to the project dir — matching the
    # real writer (infrastructure.core.pipeline.artifacts records
    # ``path.relative_to(project_dir)``). The bundle then rebases these onto the
    # repo root. (The earlier scaffold wrote repo-root-relative paths, which
    # masked the resolver bug that made every artifact 'absent'.)
    fig = project / "output" / "figures" / "result.png"
    write_doc(fig, "PNG-BYTES")
    report = project / "output" / "reports" / "summary.json"
    write_doc(report, '{"value": 1}\n')
    snapshot_current_artifact_manifest(
        project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )
    return project


def test_build_resolves_artifacts_from_real_manifest_writer(tmp_path: Path) -> None:
    """End-to-end guard against the project-rel vs repo-rel path-root mismatch.

    Builds the artifact manifest through the *real* pipeline writer
    (``write_stage_artifact_manifest`` + ``aggregate_artifact_manifests``, which
    record paths relative to the project dir), then asserts the repro bundle
    rebases them correctly so the output artifact is ``present`` with a non-null
    sha256. Before the fix the resolver looked under ``<repo_root>/output/...``
    and every artifact was reported absent, so ``verify`` always failed.
    """
    from infrastructure.core.pipeline.artifacts import (
        aggregate_artifact_manifests,
        write_stage_artifact_manifest,
    )
    from infrastructure.core.pipeline.types import StageContract

    name = "repro_real"
    project = make_project(tmp_path, name, with_manuscript=True, with_scripts=True)
    write_doc(tmp_path / "uv.lock", "# lock\n")
    write_doc(tmp_path / "pyproject.toml", "[project]\nname = 'demo'\n")
    write_doc(tmp_path / "docs" / "_generated" / "COUNTS.md", "# Canonical Facts\n")

    # A genuine output artifact under the project dir.
    artifact = project / "output" / "data" / "result.json"
    write_doc(artifact, '{"value": 42}\n')

    contract = StageContract(output_artifacts=("output/data/result.json",))
    write_stage_artifact_manifest(
        repo_root=tmp_path,
        project_dir=project,
        stage_num=2,
        stage_name="analysis",
        contract=contract,
    )
    aggregate_artifact_manifests(
        project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )
    assert (project / "output" / "reports" / "artifact_manifest.json").is_file()

    out_dir = build_repro_bundle(tmp_path, name, generated_at="2026-06-06T00:00:00+00:00")
    manifest = json.loads((out_dir / BUNDLE_MANIFEST_NAME).read_text(encoding="utf-8"))
    output_entries = [e for e in manifest["entries"] if e["kind"] == "output-artifact"]
    assert output_entries, "real manifest writer should yield at least one output artifact"
    assert all(e["present"] for e in output_entries)
    assert all(isinstance(e["sha256"], str) and len(e["sha256"]) == 64 for e in output_entries)

    report = verify_repro_bundle(out_dir / BUNDLE_MANIFEST_NAME, checkout_root=tmp_path)
    assert report.ok is True


def test_build_writes_deterministic_sorted_manifest(tmp_path: Path) -> None:
    name = "repro_demo"
    _scaffold_repro_project(tmp_path, name)

    out_dir = build_repro_bundle(tmp_path, name, generated_at="2026-06-06T00:00:00+00:00")

    manifest_path = out_dir / BUNDLE_MANIFEST_NAME
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == SCHEMA_VERSION
    assert manifest["project"] == name
    assert manifest["generated_at"] == "2026-06-06T00:00:00+00:00"
    assert any("execute_pipeline.py" in cmd for cmd in manifest["reproduce"])

    paths = [entry["path"] for entry in manifest["entries"]]
    assert paths == sorted(paths)  # deterministic, sorted entries
    assert "uv.lock" in paths
    assert "docs/_generated/COUNTS.md" in paths
    # Project-relative manifest path rebased onto the repo root.
    assert f"projects/{name}/output/figures/result.png" in paths
    for entry in manifest["entries"]:
        assert entry["present"] is True
        assert isinstance(entry["sha256"], str) and len(entry["sha256"]) == 64


def test_build_is_byte_stable_across_runs(tmp_path: Path) -> None:
    name = "repro_stable"
    _scaffold_repro_project(tmp_path, name)
    ts = "2026-01-01T00:00:00+00:00"

    first = build_repro_bundle(tmp_path, name, generated_at=ts)
    first_bytes = (first / BUNDLE_MANIFEST_NAME).read_bytes()
    second = build_repro_bundle(tmp_path, name, generated_at=ts)
    second_bytes = (second / BUNDLE_MANIFEST_NAME).read_bytes()

    assert first_bytes == second_bytes


@pytest.mark.parametrize(
    "generated_at",
    ("", "not-a-timestamp", "2026-06-06T00:00:00"),
)
def test_build_rejects_missing_malformed_or_naive_timestamp(tmp_path: Path, generated_at: str) -> None:
    name = "repro_bad_timestamp"
    _scaffold_repro_project(tmp_path, name)

    with pytest.raises(ValueError, match="timezone-aware ISO-8601/RFC3339"):
        build_repro_bundle(tmp_path, name, generated_at=generated_at)

    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize(
    "project_name",
    (
        "/absolute-project",
        "../outside-project",
        "templates/../../outside-project",
        "bad\x00project",
        "--all-public",
        "templates/-flag-spoof",
    ),
)
def test_build_rejects_unsafe_project_names_before_writing(tmp_path: Path, project_name: str) -> None:
    with pytest.raises(ValueError, match="project name"):
        build_repro_bundle(tmp_path, project_name, generated_at=_TS)

    assert not (tmp_path / "output").exists()


def test_build_rejects_external_lifecycle_project_before_writing(tmp_path: Path) -> None:
    private_root = tmp_path.parent / f"{tmp_path.name}-private-sidecar"
    private_project = make_project(
        private_root,
        "private_demo",
        with_manuscript=True,
        with_scripts=True,
    )
    write_doc(private_project / "output" / "data" / "result.json", '{"private": true}\n')
    snapshot_current_artifact_manifest(
        private_project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )
    lifecycle_link = tmp_path / "projects" / "working" / "private_demo"
    lifecycle_link.parent.mkdir(parents=True, exist_ok=True)
    lifecycle_link.symlink_to(private_project, target_is_directory=True)

    with pytest.raises(ValueError, match="must resolve inside the repository"):
        build_repro_bundle(tmp_path, "working/private_demo", generated_at=_TS)

    assert not (tmp_path / "output").exists()


def test_build_preserves_internal_lifecycle_local_inventory_mode(tmp_path: Path) -> None:
    project = make_project(
        tmp_path,
        "internal_demo",
        program="working",
        with_manuscript=True,
        with_scripts=True,
    )
    write_doc(project / "output" / "data" / "result.json", '{"local": true}\n')
    snapshot_current_artifact_manifest(
        project / "output",
        inventory_mode=STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    )

    out_dir = build_repro_bundle(tmp_path, "working/internal_demo", generated_at=_TS)

    manifest_path = out_dir / BUNDLE_MANIFEST_NAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["project"] == "working/internal_demo"
    assert verify_repro_bundle(manifest_path, checkout_root=tmp_path).ok is True


def test_explicit_external_output_directory_remains_supported(tmp_path: Path) -> None:
    name = "repro_external_output"
    _scaffold_repro_project(tmp_path, name)
    external_out = tmp_path.parent / f"{tmp_path.name}-external-bundle"

    result = build_repro_bundle(tmp_path, name, out_dir=external_out, generated_at=_TS)

    assert result == external_out
    assert (external_out / BUNDLE_MANIFEST_NAME).is_file()


def test_default_output_directory_must_remain_inside_repository(tmp_path: Path) -> None:
    name = "repro_output_link"
    _scaffold_repro_project(tmp_path, name)
    external_output = tmp_path.parent / f"{tmp_path.name}-external-output"
    external_output.mkdir()
    (tmp_path / "output").symlink_to(external_output, target_is_directory=True)

    with pytest.raises(ValueError, match="default output directory escapes the repository"):
        build_repro_bundle(tmp_path, name, generated_at=_TS)

    assert not (external_output / name).exists()


def test_verify_passes_on_unchanged_checkout(tmp_path: Path) -> None:
    name = "repro_ok"
    _scaffold_repro_project(tmp_path, name)
    out_dir = build_repro_bundle(tmp_path, name, generated_at="2026-06-06T00:00:00+00:00")

    report = verify_repro_bundle(out_dir / BUNDLE_MANIFEST_NAME, checkout_root=tmp_path)

    assert report.ok is True
    assert report.mismatches == []
    assert report.checked > 0


def test_verify_fails_closed_on_mutated_input(tmp_path: Path) -> None:
    name = "repro_mut"
    _scaffold_repro_project(tmp_path, name)
    out_dir = build_repro_bundle(tmp_path, name, generated_at="2026-06-06T00:00:00+00:00")

    # Mutate a tracked input after the bundle was built.
    (tmp_path / "uv.lock").write_text("# tampered\n", encoding="utf-8")

    report = verify_repro_bundle(out_dir / BUNDLE_MANIFEST_NAME, checkout_root=tmp_path)

    assert report.ok is False
    mutated = [m for m in report.mismatches if m["path"] == "uv.lock"]
    assert len(mutated) == 1
    assert mutated[0]["reason"] == "hash-changed"


def test_verify_fails_closed_on_missing_file(tmp_path: Path) -> None:
    name = "repro_gone"
    _scaffold_repro_project(tmp_path, name)
    out_dir = build_repro_bundle(tmp_path, name, generated_at="2026-06-06T00:00:00+00:00")

    (tmp_path / "uv.lock").unlink()

    report = verify_repro_bundle(out_dir / BUNDLE_MANIFEST_NAME, checkout_root=tmp_path)

    assert report.ok is False
    missing = [m for m in report.mismatches if m["path"] == "uv.lock"]
    assert len(missing) == 1
    assert missing[0]["reason"] == "missing"


def test_verify_rejects_unsafe_duplicate_and_symlink_entries(tmp_path: Path) -> None:
    """Manifest path controls must fail closed before any payload is trusted."""
    write_doc(tmp_path / "uv.lock", "# lock\n")
    outside = tmp_path.parent / "private-repro-input.txt"
    write_doc(outside, "private\n")
    (tmp_path / "escape").symlink_to(outside)

    base = {
        "schema_version": SCHEMA_VERSION,
        "project": "template_code_project",
        "generated_at": "2026-06-06T00:00:00+00:00",
        "reproduce": ["uv run python scripts/runner/execute_pipeline.py"],
    }
    for entries, expected_reason in (
        (
            [
                {
                    "kind": "lockfile",
                    "path": "uv.lock",
                    "present": True,
                    "sha256": "0" * 64,
                    "size_bytes": 7,
                },
                {
                    "kind": "lockfile",
                    "path": "uv.lock",
                    "present": True,
                    "sha256": "0" * 64,
                    "size_bytes": 7,
                },
            ],
            "unsafe-or-duplicate-path",
        ),
        (
            [
                {
                    "kind": "lockfile",
                    "path": "escape",
                    "present": True,
                    "sha256": "0" * 64,
                    "size_bytes": 8,
                }
            ],
            "missing",
        ),
    ):
        manifest = tmp_path / f"{expected_reason}.json"
        manifest.write_text(json.dumps({**base, "entries": entries}), encoding="utf-8")
        report = verify_repro_bundle(manifest, checkout_root=tmp_path)
        assert report.ok is False
        assert any(row["reason"] == expected_reason for row in report.mismatches)


@pytest.mark.parametrize(
    "alias",
    (
        "./uv.lock",
        "uv.lock/",
        "dir//uv.lock",
        "dir/./uv.lock",
        "dir/../uv.lock",
        "bad\x00path",
        "dir\\uv.lock",
        "/uv.lock",
        "C:/uv.lock",
    ),
)
def test_verify_rejects_noncanonical_posix_path_aliases(tmp_path: Path, alias: str) -> None:
    name = "repro_aliases"
    _scaffold_repro_project(tmp_path, name)
    out_dir = build_repro_bundle(tmp_path, name, generated_at=_TS)
    manifest_path = out_dir / BUNDLE_MANIFEST_NAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    lock_entry = next(entry for entry in payload["entries"] if entry["kind"] == "lockfile")
    payload["entries"].append({**lock_entry, "path": alias})
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    report = verify_repro_bundle(manifest_path, checkout_root=tmp_path)

    assert report.ok is False
    assert {row["reason"] for row in report.mismatches} >= {"unsafe-or-duplicate-path"}


def test_verify_requires_present_artifact_manifest_and_output_artifact(tmp_path: Path) -> None:
    name = "repro_required_entries"
    _scaffold_repro_project(tmp_path, name)
    out_dir = build_repro_bundle(tmp_path, name, generated_at=_TS)
    manifest_path = out_dir / BUNDLE_MANIFEST_NAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    no_manifest = {
        **payload,
        "entries": [entry for entry in payload["entries"] if entry["kind"] != "artifact-manifest"],
    }
    manifest_path.write_text(json.dumps(no_manifest), encoding="utf-8")
    report = verify_repro_bundle(manifest_path, checkout_root=tmp_path)
    assert report.ok is False
    assert any(row["reason"] == "missing-artifact-manifest" for row in report.mismatches)

    no_outputs = {
        **payload,
        "entries": [entry for entry in payload["entries"] if entry["kind"] != "output-artifact"],
    }
    manifest_path.write_text(json.dumps(no_outputs), encoding="utf-8")
    report = verify_repro_bundle(manifest_path, checkout_root=tmp_path)
    assert report.ok is False
    assert any(row["reason"] == "missing-output-artifacts" for row in report.mismatches)

    absent_manifest = json.loads(json.dumps(payload))
    manifest_entry = next(entry for entry in absent_manifest["entries"] if entry["kind"] == "artifact-manifest")
    manifest_entry.update({"present": False, "sha256": None, "size_bytes": 0})
    manifest_path.write_text(json.dumps(absent_manifest), encoding="utf-8")
    report = verify_repro_bundle(manifest_path, checkout_root=tmp_path)
    assert report.ok is False
    assert any(row["reason"] == "missing-artifact-manifest" for row in report.mismatches)


@pytest.mark.parametrize(
    "project_name",
    ("../escape", "templates\\template_code_project", "--all-public", "templates/-spoof"),
)
def test_verify_rejects_noncanonical_or_unsafe_project_field(tmp_path: Path, project_name: str) -> None:
    name = "repro_project_field"
    _scaffold_repro_project(tmp_path, name)
    out_dir = build_repro_bundle(tmp_path, name, generated_at=_TS)
    manifest_path = out_dir / BUNDLE_MANIFEST_NAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["project"] = project_name
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    report = verify_repro_bundle(manifest_path, checkout_root=tmp_path)

    assert report.ok is False
    assert any(row["reason"] == "invalid-project" for row in report.mismatches)


def test_verify_rejects_fabricated_project_command_and_kind_swaps(tmp_path: Path) -> None:
    name = "repro_semantic_binding"
    _scaffold_repro_project(tmp_path, name)
    out_dir = build_repro_bundle(tmp_path, name, generated_at=_TS)
    manifest_path = out_dir / BUNDLE_MANIFEST_NAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifact_entry = next(entry for entry in payload["entries"] if entry["kind"] == "artifact-manifest")
    lock_entry = next(entry for entry in payload["entries"] if entry["kind"] == "lockfile")
    artifact_entry["kind"] = "lockfile"
    lock_entry["kind"] = "artifact-manifest"
    payload["project"] = "totally_different_project"
    payload["reproduce"] = ["echo fabricated"]
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    report = verify_repro_bundle(manifest_path, checkout_root=tmp_path)

    assert report.ok is False
    reasons = {row["reason"] for row in report.mismatches}
    assert {"project-resolution-failed", "reproduce-command-mismatch"} <= reasons


@pytest.mark.parametrize(
    ("generated_at", "expected_reason"),
    (
        (None, "missing-generated-at"),
        ("not-a-timestamp", "invalid-generated-at"),
        ("2026-06-06T00:00:00", "invalid-generated-at"),
    ),
)
def test_verify_requires_timezone_aware_generated_at(
    tmp_path: Path,
    generated_at: str | None,
    expected_reason: str,
) -> None:
    name = "repro_timestamp_schema"
    _scaffold_repro_project(tmp_path, name)
    out_dir = build_repro_bundle(tmp_path, name, generated_at=_TS)
    manifest_path = out_dir / BUNDLE_MANIFEST_NAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if generated_at is None:
        payload.pop("generated_at")
    else:
        payload["generated_at"] = generated_at
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    report = verify_repro_bundle(manifest_path, checkout_root=tmp_path)

    assert report.ok is False
    assert any(row["reason"] == expected_reason for row in report.mismatches)


def test_verify_requires_explicit_present_field(tmp_path: Path) -> None:
    name = "repro_present_schema"
    _scaffold_repro_project(tmp_path, name)
    out_dir = build_repro_bundle(tmp_path, name, generated_at=_TS)
    manifest_path = out_dir / BUNDLE_MANIFEST_NAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload.pop("generated_at")
    for entry in payload["entries"]:
        entry.pop("present")
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    report = verify_repro_bundle(manifest_path, checkout_root=tmp_path)

    assert report.ok is False
    reasons = {row["reason"] for row in report.mismatches}
    assert {"missing-generated-at", "missing-entry-fields", "invalid-present-flag"} <= reasons


def test_verify_binds_entry_kinds_to_canonical_paths(tmp_path: Path) -> None:
    name = "repro_kind_binding"
    _scaffold_repro_project(tmp_path, name)
    out_dir = build_repro_bundle(tmp_path, name, generated_at=_TS)
    manifest_path = out_dir / BUNDLE_MANIFEST_NAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifact_entry = next(entry for entry in payload["entries"] if entry["kind"] == "artifact-manifest")
    lock_entry = next(entry for entry in payload["entries"] if entry["kind"] == "lockfile")
    artifact_entry["kind"] = "lockfile"
    lock_entry["kind"] = "artifact-manifest"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    report = verify_repro_bundle(manifest_path, checkout_root=tmp_path)

    assert report.ok is False
    kind_mismatches = [row for row in report.mismatches if row["reason"] == "kind-path-mismatch"]
    assert {row["path"] for row in kind_mismatches} == {artifact_entry["path"], lock_entry["path"]}


def test_verify_binds_safe_project_name_to_its_own_artifact_set(tmp_path: Path) -> None:
    name = "repro_project_binding"
    other_name = "repro_other_project"
    _scaffold_repro_project(tmp_path, name)
    _scaffold_repro_project(tmp_path, other_name)
    out_dir = build_repro_bundle(tmp_path, name, generated_at=_TS)
    manifest_path = out_dir / BUNDLE_MANIFEST_NAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["project"] = other_name
    payload["reproduce"] = [f"uv run python scripts/runner/execute_pipeline.py --project {other_name} --core-only"]
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    report = verify_repro_bundle(manifest_path, checkout_root=tmp_path)

    assert report.ok is False
    reasons = {row["reason"] for row in report.mismatches}
    assert {"unexpected-entry-path", "missing-required-entries", "output-artifact-set-mismatch"} <= reasons


def test_cli_build_then_verify(tmp_path: Path) -> None:
    name = "repro_cli"
    _scaffold_repro_project(tmp_path, name)
    from infrastructure.publishing.repro_bundle import main

    out_dir = tmp_path / "bundle_out"
    rc = main(
        [
            "build",
            name,
            "--repo-root",
            str(tmp_path),
            "--out",
            str(out_dir),
            "--generated-at",
            "2026-06-06T00:00:00+00:00",
        ]
    )
    assert rc == 0
    manifest = out_dir / BUNDLE_MANIFEST_NAME
    assert manifest.is_file()

    rc_ok = main(["verify", str(manifest), "--checkout-root", str(tmp_path)])
    assert rc_ok == 0

    (tmp_path / "uv.lock").write_text("# changed\n", encoding="utf-8")
    rc_fail = main(["verify", str(manifest), "--checkout-root", str(tmp_path)])
    assert rc_fail == 1


# --------------------------------------------------------------------------- #
# REPRO-MULTI-1: multi-exemplar (--all-public) bundles
# --------------------------------------------------------------------------- #

_TS = "2026-06-06T00:00:00+00:00"


def _scaffold_public_exemplar(root: Path, name: str) -> Path:
    """Scaffold a discoverable public exemplar under ``projects/templates/<name>``."""
    project = make_project(root, name, program="templates", with_manuscript=True, with_scripts=True)
    # Output artifact under the project dir; manifest path project-relative
    # (matches the real artifacts writer; the bundle rebases onto repo root).
    fig = project / "output" / "figures" / "result.png"
    write_doc(fig, f"PNG-{name}")
    snapshot_current_artifact_manifest(project / "output")
    return project


def test_public_repro_bundle_rejects_explicit_local_inventory_manifest(tmp_path: Path) -> None:
    project = _scaffold_public_exemplar(tmp_path, "template_sia")
    manifest_path = project / "output" / "reports" / "artifact_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["inventory_mode"] = STABLE_LOCAL_OUTPUT_INVENTORY_MODE
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="artifact inventory mode mismatch"):
        build_repro_bundle(tmp_path, "templates/template_sia", generated_at=_TS)


def test_repro_bundle_rejects_manifest_omitting_current_stable_output(tmp_path: Path) -> None:
    name = "repro_omission"
    project = _scaffold_repro_project(tmp_path, name)
    manifest_path = project / "output" / "reports" / "artifact_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["entries"] = [entry for entry in payload["entries"] if entry["path"] != "output/reports/summary.json"]
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="unattested stable artifact: output/reports/summary.json"):
        build_repro_bundle(tmp_path, name, generated_at=_TS)


def test_repro_bundle_never_skips_escaping_manifest_output(tmp_path: Path) -> None:
    name = "repro_escape"
    project = _scaffold_repro_project(tmp_path, name)
    manifest_path = project / "output" / "reports" / "artifact_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["entries"][0]["path"] = "../../private-result.json"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid artifact manifest"):
        build_repro_bundle(tmp_path, name, generated_at=_TS)

    assert not (tmp_path / "output").exists()


def _scaffold_two_public_exemplars(root: Path) -> tuple[str, str]:
    """Create two real public-roster exemplars plus the repo-level repro inputs."""
    # Names must be members of PUBLIC_PROJECT_NAMES for the roster to include them.
    a, b = "template_sia", "template_code_project"
    _scaffold_public_exemplar(root, a)
    _scaffold_public_exemplar(root, b)
    write_doc(root / "uv.lock", "# lock contents\n")
    write_doc(root / "pyproject.toml", "[project]\nname = 'demo'\n")
    write_doc(root / "docs" / "_generated" / "COUNTS.md", "# Canonical Facts\n\n- 214\n")
    return f"templates/{a}", f"templates/{b}"


def test_build_all_public_emits_manifest_per_exemplar(tmp_path: Path) -> None:
    qa, qb = _scaffold_two_public_exemplars(tmp_path)

    results = build_public_repro_bundles(tmp_path, out_dir=tmp_path / "bundles", generated_at=_TS)

    assert set(results) == {qa, qb}
    for qualified in (qa, qb):
        manifest = results[qualified] / BUNDLE_MANIFEST_NAME
        assert manifest.is_file()
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["project"] == qualified
        assert data["schema_version"] == SCHEMA_VERSION


def test_cli_build_all_public_then_verify_each_independently(tmp_path: Path) -> None:
    qa, qb = _scaffold_two_public_exemplars(tmp_path)
    out_dir = tmp_path / "bundles"

    rc = main(["build", "--all-public", "--repo-root", str(tmp_path), "--out", str(out_dir), "--generated-at", _TS])
    assert rc == 0

    manifest_a = out_dir / qa / "repro_bundle" / BUNDLE_MANIFEST_NAME
    manifest_b = out_dir / qb / "repro_bundle" / BUNDLE_MANIFEST_NAME
    assert manifest_a.is_file() and manifest_b.is_file()

    # Both verify clean on the unchanged checkout.
    assert verify_repro_bundle(manifest_a, checkout_root=tmp_path).ok is True
    assert verify_repro_bundle(manifest_b, checkout_root=tmp_path).ok is True

    # Mutating one exemplar's input fails only that exemplar — verification is
    # per-bundle, not merged across the roster. The artifact lives under the
    # project dir (qa == "templates/<name>").
    (tmp_path / "projects" / qa / "output" / "figures" / "result.png").write_text("tampered", encoding="utf-8")
    assert verify_repro_bundle(manifest_a, checkout_root=tmp_path).ok is False
    assert verify_repro_bundle(manifest_b, checkout_root=tmp_path).ok is True


def test_build_requires_project_or_all_public(tmp_path: Path) -> None:
    """``build`` with neither a project nor --all-public is a usage error (exit 2)."""
    import pytest

    with pytest.raises(SystemExit) as exc:
        main(["build", "--repo-root", str(tmp_path)])
    assert exc.value.code == 2


def test_build_rejects_project_and_all_public_together(tmp_path: Path) -> None:
    """A positional project AND --all-public is ambiguous and must error (exit 2),

    never silently ignore the named project and build the whole roster.
    """
    import pytest

    _scaffold_two_public_exemplars(tmp_path)
    with pytest.raises(SystemExit) as exc:
        main(["build", "template_sia", "--all-public", "--repo-root", str(tmp_path), "--out", str(tmp_path / "o")])
    assert exc.value.code == 2


def test_collect_schema_findings_rejects_unsupported_schema() -> None:
    findings, project = collect_schema_findings(
        {
            "schema_version": "0.0",
            "generated_at": "2026-01-01T00:00:00Z",
            "project": "templates/demo",
            "reproduce": ["not-the-command"],
        }
    )
    reasons = {item["reason"] for item in findings}
    assert "unsupported-schema" in reasons
    assert project == "templates/demo"
