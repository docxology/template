"""Real file controls for one-snapshot public readiness custody."""

from __future__ import annotations

import hashlib
import os
import sys
import time
from dataclasses import replace
from pathlib import Path
from types import FrameType
from typing import Any

import pytest

from infrastructure.reporting.native_readiness_input_copy import copy_source_mirror_data
from infrastructure.reporting.readiness_receipts import (
    _public_roots,
    project_source_identity,
    public_source_paths,
    source_fingerprint,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader, _snapshot_directory_unchanged
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


def test_every_public_project_and_output_scope_retains_real_file_custody(tmp_path: Path) -> None:
    reader = SnapshotReader(tmp_path)
    prefixes = {"output/readiness"}
    for name in PUBLIC_PROJECT_NAMES:
        prefixes.update((f"projects/{name}", f"output/{name}", f"output/{Path(name).name}"))
    for prefix in sorted(prefixes):
        relative = f"{prefix}/nested/evidence.json"
        target = tmp_path / relative
        target.parent.mkdir(parents=True)
        target.write_bytes(b'{"observed": true}\n')
        assert reader.read(relative).json_object() == {"observed": True}
    assert reader.unchanged()
    target.write_bytes(b'{"observed": false}\n')
    assert reader.unchanged() is False


def test_public_scope_prefixes_require_complete_components(tmp_path: Path) -> None:
    reader = SnapshotReader(tmp_path)
    refused = {"projects", "projects/templates", "output", "output/templates", "output/readiness-other/evidence.json"}
    for name in PUBLIC_PROJECT_NAMES:
        refused.update(
            (
                f"projects/{name}-other/evidence.json",
                f"projects/{name}_other/evidence.json",
                f"output/{name}-other/evidence.json",
                f"output/{Path(name).name}_other/evidence.json",
                f"projects/{name}/../evidence.json",
            )
        )
    for relative in sorted(refused):
        with pytest.raises(ValueError):
            reader.public_path(relative)


def test_public_scope_admission_rechecks_symlinked_parent_after_snapshot(tmp_path: Path) -> None:
    relative = f"projects/{PUBLIC_PROJECT_NAMES[0]}/nested/evidence.json"
    target = tmp_path / relative
    target.parent.mkdir(parents=True)
    target.write_bytes(b"{}")
    reader = SnapshotReader(tmp_path)
    reader.read(relative)
    original = target.parent.with_name("original")
    target.parent.rename(original)
    target.parent.symlink_to(original, target_is_directory=True)
    assert reader.unchanged() is False
    with pytest.raises(ValueError, match="symlink"):
        reader.read(relative)

    # A root replacement keeps the leaf intact and exercises resolved containment.
    repository = tmp_path / "repository"
    evidence = repository / "docs/nested/evidence.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"{}")
    rooted = SnapshotReader(repository)
    held = rooted.read("docs/nested/evidence.json")
    assert rooted.public_path("docs//./nested/evidence.json") == evidence
    relocated = tmp_path / "relocated-source"
    repository.rename(relocated)
    repository.symlink_to(relocated, target_is_directory=True)
    assert evidence.stat().st_ino == held.identity[0]
    assert evidence.read_bytes() == held.content
    assert rooted.unchanged() is False
    with pytest.raises(ValueError, match="escapes"):
        rooted.public_path("docs/nested/evidence.json")


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


def _source_mirror_fixture(tmp_path: Path) -> tuple[Path, Path]:
    """Create actual declared public Source directories and separate owned DATA."""
    source, destination = tmp_path / "source", tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    roots, _ = _public_roots(source)
    for root in roots:
        root.mkdir(parents=True, exist_ok=True)
    retained = source / "infrastructure/nested/retained.txt"
    retained.parent.mkdir()
    retained.write_bytes(b"actual owned source DATA\n")
    (source / "infrastructure/empty").mkdir()
    (source / "docs/ignored-empty").mkdir()
    (source / ".gitignore").write_text("docs/ignored-empty/\n", encoding="utf-8")
    (source / "infrastructure/.DS_Store").write_bytes(b"excluded metadata")
    private = source / "projects/working/private"
    private.mkdir(parents=True)
    (private / "secret.txt").write_bytes(b"owned private negative control")
    return source, destination


@pytest.mark.parametrize("existing", [False, True])
def test_source_mirror_copies_canonical_directories_and_declared_data(tmp_path: Path, existing: bool) -> None:
    source, destination = _source_mirror_fixture(tmp_path)
    relative = "infrastructure/nested/retained.txt"
    if existing:
        target = destination / relative
        target.parent.mkdir(parents=True)
        target.write_bytes((source / relative).read_bytes())
    identity = source_fingerprint(source)
    copy_source_mirror_data(source, destination, expected_identity=identity, deadline=time.monotonic() + 5)
    roots, _ = _public_roots(source)
    assert all((destination / root.relative_to(source)).is_dir() for root in roots if root.is_dir())
    assert (destination / "infrastructure/empty").is_dir()
    assert (destination / "docs/ignored-empty").is_dir()
    assert (destination / relative).read_bytes() == (source / relative).read_bytes()
    assert (destination / ".gitignore").read_bytes() == (source / ".gitignore").read_bytes()
    assert not (destination / "infrastructure/.DS_Store").exists()
    assert not (destination / "projects/working").exists()
    assert not list(destination.rglob(".reference-directory-policy"))
    assert source_fingerprint(source) == source_fingerprint(destination) == identity


@pytest.mark.parametrize("substitution", ["file", "symlink"])
def test_source_mirror_refuses_substituted_directory(tmp_path: Path, substitution: str) -> None:
    source, destination = _source_mirror_fixture(tmp_path)
    target = destination / "infrastructure"
    external = tmp_path / "external"
    external.mkdir()
    marker = external / "marker.txt"
    marker.write_bytes(b"owned external negative control")
    if substitution == "file":
        target.write_bytes(b"owned substituted directory")
    else:
        target.symlink_to(external, target_is_directory=True)
    identity = source_fingerprint(source)
    with pytest.raises(ValueError, match="substituted|symlink"):
        copy_source_mirror_data(source, destination, expected_identity=identity, deadline=time.monotonic() + 5)
    assert source_fingerprint(source) == identity
    assert marker.read_bytes() == b"owned external negative control"
    assert list(external.iterdir()) == [marker]
    if substitution == "file":
        assert target.read_bytes() == b"owned substituted directory"


def test_source_mirror_directory_admission_retains_credential_refusal(tmp_path: Path) -> None:
    source, destination = _source_mirror_fixture(tmp_path)
    credential = source / "infrastructure/.env"
    credential.mkdir()
    (credential / "retained.txt").write_bytes(b"owned private filename negative control")
    identity = source_fingerprint(source)
    with pytest.raises(ValueError, match="private credential/control"):
        copy_source_mirror_data(source, destination, expected_identity=identity, deadline=time.monotonic() + 5)
    assert source_fingerprint(source) == identity
    assert not (destination / "infrastructure/.env").exists()


@pytest.mark.parametrize("change", ["identity", "content"])
def test_source_mirror_refuses_wrong_identity_or_conflicting_file(tmp_path: Path, change: str) -> None:
    source, destination = _source_mirror_fixture(tmp_path)
    actual = source_fingerprint(source)
    identity = "0" * 64 if change == "identity" else actual
    if change == "content":
        target = destination / "infrastructure/nested/retained.txt"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"owned conflicting destination")
    with pytest.raises(ValueError, match="externally selected|cannot replace"):
        copy_source_mirror_data(source, destination, expected_identity=identity, deadline=time.monotonic() + 5)
    assert source_fingerprint(source) == actual
    if change == "content":
        assert target.read_bytes() == b"owned conflicting destination"


def test_source_mirror_expired_original_deadline_precedes_copy(tmp_path: Path) -> None:
    source, destination = _source_mirror_fixture(tmp_path)
    identity = source_fingerprint(source)
    with pytest.raises(TimeoutError):
        copy_source_mirror_data(source, destination, expected_identity=identity, deadline=time.monotonic() - 1)
    assert not list(destination.iterdir())
    assert source_fingerprint(source) == identity


@pytest.mark.parametrize("change", ["parent", "ancestor", "add", "remove", "replace", "dictionary", "root"])
def test_snapshot_batch_closes_real_directories_and_held_inventory(tmp_path: Path, change: str) -> None:
    """Observe an actual leaf stat, then mutate owned state before closing checks."""
    root = tmp_path / "repository"
    target = root / "docs/nested/evidence.json"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"retained original bytes")
    reader = SnapshotReader(root)
    held = reader.read("docs/nested/evidence.json")
    extra = root / "docs/extra.json"
    extra.write_bytes(b"other actual evidence")
    additional = SnapshotReader(root).read("docs/extra.json")
    observed: list[str] = []

    def after_actual_stat(frame: FrameType, event: str, function: Any) -> None:
        if (
            observed
            or event != "c_return"
            or function is not os.stat
            or frame.f_code is not _snapshot_directory_unchanged.__code__
            or frame.f_locals.get("item") is not held
        ):
            return
        observed.append(change)
        if change in {"parent", "ancestor"}:
            directory = target.parent if change == "parent" else root / "docs"
            relocated = directory.with_name(directory.name + "-original")
            directory.rename(relocated)
            replacement = directory / target.relative_to(directory)
            replacement.parent.mkdir(parents=True)
            os.link(relocated / target.relative_to(directory), replacement)
        elif change == "add":
            reader.snapshots[extra] = additional
        elif change == "remove":
            del reader.snapshots[target]
        elif change == "replace":
            reader.snapshots[target] = replace(held)
        elif change == "dictionary":
            reader.snapshots = dict(reader.snapshots)
        else:
            reader.root = tmp_path

    previous = sys.getprofile()
    try:
        sys.setprofile(after_actual_stat)
        assert reader.unchanged() is False
    finally:
        sys.setprofile(previous)
    assert observed == [change]
    assert target.read_bytes() == held.content


def test_snapshot_batches_reobserve_file_clocks_and_empty_inventory(tmp_path: Path) -> None:
    reader = SnapshotReader(tmp_path)
    assert reader.unchanged()
    for directory in ("docs/first", "docs/second", "output/readiness"):
        for index in range(8):
            relative = f"{directory}/{index}.json"
            path = tmp_path / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"original")
            reader.read(relative)
    assert reader.unchanged()
    path.write_bytes(b"changed!")
    os.utime(path, ns=(path.stat().st_atime_ns, reader.snapshots[path].identity[2]))
    assert path.stat().st_size == reader.snapshots[path].identity[1]
    assert reader.unchanged() is False


def test_snapshot_traversal_does_not_depend_on_python_recursion_depth(tmp_path: Path) -> None:
    reader = SnapshotReader(tmp_path)
    target = tmp_path / "docs"
    for _ in range(180):
        target /= "d"
        target.mkdir(parents=True, exist_ok=True)
    target /= "evidence.json"
    target.write_bytes(b"actual deeply nested file")
    reader.read(target.relative_to(tmp_path).as_posix())
    previous = sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(120)
        assert reader.unchanged()
    finally:
        sys.setrecursionlimit(previous)


def test_snapshot_traversal_bounds_live_handles_and_closes_failed_paths(tmp_path: Path) -> None:
    descriptors = Path("/dev/fd")
    if not descriptors.is_dir():
        pytest.skip("the actual process descriptor table is unavailable")
    reader = SnapshotReader(tmp_path)
    for index in range(100):
        path = tmp_path / f"docs/{index}/evidence.json"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"actual breadth control")
        reader.read(path.relative_to(tmp_path).as_posix())
    baseline = len(list(descriptors.iterdir()))
    peak = baseline

    def observe_open(frame: FrameType, event: str, function: Any) -> None:
        nonlocal peak
        if event == "c_return" and function is os.open:
            peak = max(peak, len(list(descriptors.iterdir())))

    previous = sys.getprofile()
    try:
        sys.setprofile(observe_open)
        assert reader.unchanged()
    finally:
        sys.setprofile(previous)
    assert peak > baseline
    assert peak < baseline + len(tmp_path.resolve().parts) + 8
    assert len(list(descriptors.iterdir())) == baseline
    parent = path.parent
    original = parent.with_name("retained-original")
    parent.rename(original)
    parent.symlink_to(original, target_is_directory=True)
    for _ in range(20):
        assert reader.unchanged() is False
    assert len(list(descriptors.iterdir())) == baseline


def test_snapshot_traversal_refuses_fifo_without_opening_it(tmp_path: Path) -> None:
    path = tmp_path / "docs/evidence.json"
    path.parent.mkdir()
    path.write_bytes(b"regular file")
    reader = SnapshotReader(tmp_path)
    reader.read("docs/evidence.json")
    path.unlink()
    os.mkfifo(path)
    assert reader.unchanged() is False


def test_generic_agent_config_is_bound_while_runtime_memory_stays_private(tmp_path: Path) -> None:
    from infrastructure.reporting.release_readiness_snapshot import PUBLIC_AGENT_FILES

    for name in PUBLIC_AGENT_FILES | {".agents/workflows/owned/SKILL.md", ".agents/roles/owned.md"}:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("owned public agent configuration\n")
    private = tmp_path / ".agents/state/continual-learning-memory.json"
    private.write_text("owned private state\n")
    reader = SnapshotReader(tmp_path)
    public = public_source_paths(tmp_path)
    assert {tmp_path / name for name in PUBLIC_AGENT_FILES} <= set(public)
    assert private not in public
    for target in public:
        reader.read(target.relative_to(tmp_path).as_posix())
    before = source_fingerprint(tmp_path)
    private.write_text("changed private state\n")
    assert reader.unchanged() and source_fingerprint(tmp_path) == before
    with pytest.raises(ValueError, match="private agent state"):
        reader.read(private.relative_to(tmp_path).as_posix())
    (tmp_path / ".agents/skill_manifest.json").write_text("changed public manifest\n")
    assert not reader.unchanged() and source_fingerprint(tmp_path) != before
