"""Real file controls for one-snapshot public readiness custody."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from infrastructure.reporting.readiness_receipts import project_source_identity, public_source_paths, source_fingerprint
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def test_facts_and_digest_use_the_same_bytes_after_file_replacement(tmp_path: Path) -> None:
    evidence = tmp_path / "output/readiness/check.json"
    evidence.parent.mkdir(parents=True)
    first = b'{"passed": false}\n'
    evidence.write_bytes(first)
    reader = SnapshotReader(tmp_path)
    observed = reader.read("output/readiness/check.json")
    replacement = evidence.with_suffix(".new")
    replacement.write_bytes(b'{"passed": true}\n')
    replacement.replace(evidence)
    reread = reader.read("output/readiness/check.json")
    assert reread is observed
    assert reread.json_object()["passed"] is False
    assert reread.sha256 == hashlib.sha256(first).hexdigest()
    assert reader.unchanged() is False


@pytest.mark.parametrize(
    "reference",
    [
        ".",
        "../private.json",
        "/tmp/private.json",
        "projects/working/private/output/evidence.json",
        "output/private/evidence.json",
        "private/evidence.json",
        ".env",
        ".private_projects_root",
        "secret.json",
        "projects/templates/template_code_project/.env.production",
        "fonds/working/private/data.json",
    ],
)
def test_artifact_references_cannot_escape_public_scope(tmp_path: Path, reference: str) -> None:
    with pytest.raises(ValueError):
        SnapshotReader(tmp_path).read(reference)


def test_symlink_swap_cannot_replace_an_observed_artifact(tmp_path: Path) -> None:
    evidence = tmp_path / "output/readiness/check.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("{}")
    reader = SnapshotReader(tmp_path)
    reader.read("output/readiness/check.json")
    alternate = tmp_path / "alternate.json"
    alternate.write_text("{}")
    evidence.unlink()
    evidence.symlink_to(alternate)
    assert reader.unchanged() is False
    with pytest.raises(ValueError, match="symlink"):
        reader.read("output/readiness/check.json")


def test_nested_output_build_and_dist_source_are_bound(tmp_path: Path) -> None:
    project = tmp_path / "projects/templates/template_code_project"
    paths = [project / "src/output/model.py", project / "src/build/model.py", project / "src/dist/model.py"]
    for path in paths:
        path.parent.mkdir(parents=True)
        path.write_text("parameter = 1\n")
    previous = source_fingerprint(tmp_path)
    for path in paths:
        path.write_text("parameter = 2\n")
        current = source_fingerprint(tmp_path)
        assert current != previous
        previous = current


def test_stable_pdf_mutation_invalidates_but_private_tree_is_not_consumed(tmp_path: Path) -> None:
    output = tmp_path / "projects/templates/template_code_project/output/pdf"
    output.mkdir(parents=True)
    pdf = output / "main.pdf"
    pdf.write_bytes(b"%PDF-1.7\nversion one")
    previous = source_fingerprint(tmp_path)
    private = tmp_path / "projects/working/private"
    private.mkdir(parents=True)
    (private / "secret.txt").write_text("local-only")
    assert source_fingerprint(tmp_path) == previous
    pdf.write_bytes(b"%PDF-1.7\nversion two")
    assert source_fingerprint(tmp_path) != previous


def test_exact_project_runtime_controls_do_not_change_source_or_export_inventory(tmp_path: Path) -> None:
    scope = "templates/template_code_project"
    project = tmp_path / "projects" / scope
    source = project / "src/model.py"
    source.parent.mkdir(parents=True)
    source.write_text("parameter = 1\n")
    before = (
        project_source_identity(tmp_path, scope),
        source_fingerprint(tmp_path),
        public_source_paths(tmp_path, scope),
    )
    for name in (
        ".hypothesis/examples/cache",
        ".coverage",
        ".coverage.project",
        "coverage_project.json",
        "htmlcov/index.html",
        "src/model.egg-info/PKG-INFO",
    ):
        path = project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("generated runtime metadata")
    after = (
        project_source_identity(tmp_path, scope),
        source_fingerprint(tmp_path),
        public_source_paths(tmp_path, scope),
    )
    assert before == after


@pytest.mark.parametrize(
    "name",
    [
        "data/.hypothesis/examples.json",
        "data/.coverage",
        "data/.coverage.project",
        "data/coverage_project.json",
        "src/data/htmlcov/index.html",
        "src/data/model.egg-info/authored.txt",
    ],
)
def test_nested_authored_runtime_names_remain_bound_inputs(tmp_path: Path, name: str) -> None:
    scope = "templates/template_code_project"
    project = tmp_path / "projects" / scope
    path = project / name
    path.parent.mkdir(parents=True)
    path.write_text("authored input one")
    before = project_source_identity(tmp_path, scope), source_fingerprint(tmp_path)
    assert path in public_source_paths(tmp_path, scope)
    path.write_text("authored input two")
    after = project_source_identity(tmp_path, scope), source_fingerprint(tmp_path)
    assert before[0] != after[0] and before[1] != after[1]


def test_smaller_snapshot_cap_refuses_before_read_and_applies_to_cached_bytes(tmp_path: Path) -> None:
    path = tmp_path / "output/readiness/bounded.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"x" * 1025)
    reader = SnapshotReader(tmp_path)
    with pytest.raises(ValueError):
        reader.read("output/readiness/bounded.json", max_bytes=1024)
    assert not reader.snapshots
    held = reader.read("output/readiness/bounded.json", max_bytes=1025)
    assert len(held.content) == 1025
    with pytest.raises(ValueError, match="held snapshot"):
        reader.read("output/readiness/bounded.json", max_bytes=1024)
    assert reader.read("output/readiness/bounded.json", max_bytes=1025) is held


@pytest.mark.parametrize("limit", [True, 0, -1, 64 * 1024 * 1024 + 1, 1.0])
def test_snapshot_cap_cannot_disable_the_original_global_ceiling(tmp_path: Path, limit: object) -> None:
    with pytest.raises(ValueError, match="positive bounded"):
        SnapshotReader(tmp_path).read("output/readiness/missing.json", max_bytes=limit)
