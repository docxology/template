#!/usr/bin/env python3
"""Tests for infrastructure.publishing.repro_bundle (REPRO-BUNDLE-1).

No mocks: every test builds real files under ``tmp_path`` and exercises the
builder/verifier on those real bytes.
"""

from __future__ import annotations

import json
from pathlib import Path

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
    write_doc(root / "docs" / "_generated" / "canonical_facts.md", "# Canonical Facts\n\n- 214\n")

    # Declared output artifacts plus an artifact manifest pointing at them.
    fig = root / "output" / name / "figures" / "result.png"
    write_doc(fig, "PNG-BYTES")
    report = root / "output" / name / "reports" / "summary.json"
    write_doc(report, '{"value": 1}\n')
    artifact_manifest = project / "output" / "reports" / "artifact_manifest.json"
    write_doc(
        artifact_manifest,
        json.dumps(
            {
                "entries": [
                    {"path": f"output/{name}/figures/result.png"},
                    {"path": f"output/{name}/reports/summary.json"},
                ]
            }
        ),
    )
    return project


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
    assert "docs/_generated/canonical_facts.md" in paths
    assert f"output/{name}/figures/result.png" in paths
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
    qualified = f"templates/{name}"
    fig = root / "output" / qualified / "figures" / "result.png"
    write_doc(fig, f"PNG-{name}")
    artifact_manifest = project / "output" / "reports" / "artifact_manifest.json"
    write_doc(
        artifact_manifest,
        json.dumps({"entries": [{"path": f"output/{qualified}/figures/result.png"}]}),
    )
    return project


def _scaffold_two_public_exemplars(root: Path) -> tuple[str, str]:
    """Create two real public-roster exemplars plus the repo-level repro inputs."""
    # Names must be members of PUBLIC_PROJECT_NAMES for the roster to include them.
    a, b = "template_sia", "template_code_project"
    _scaffold_public_exemplar(root, a)
    _scaffold_public_exemplar(root, b)
    write_doc(root / "uv.lock", "# lock contents\n")
    write_doc(root / "pyproject.toml", "[project]\nname = 'demo'\n")
    write_doc(root / "docs" / "_generated" / "canonical_facts.md", "# Canonical Facts\n\n- 214\n")
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
    # per-bundle, not merged across the roster.
    (tmp_path / "output" / qa / "figures" / "result.png").write_text("tampered", encoding="utf-8")
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
