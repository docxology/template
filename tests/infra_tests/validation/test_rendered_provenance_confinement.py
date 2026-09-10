"""Rendered publication provenance: fail-closed receipts, confined atomic writes, and symlink confinement."""

from __future__ import annotations
import threading
from pathlib import Path
import pytest
from infrastructure.core.files.secure_write import atomic_write_text_confined
from infrastructure.validation.publication.rendered_provenance import (
    RECEIPT_RELATIVE_PATH,
    validate_rendered_provenance,
    write_rendered_provenance_receipt,
)
from infrastructure.validation.rendered_snapshot import (
    build_current_rendered_snapshot,
)
from tests._support.projects import write_doc
from tests.infra_tests.validation._rendered_provenance_helpers import (
    PROJECT,
    _green_project,
    _write_green_validation_report,
)


def test_receipt_fails_closed_when_missing_or_malformed(tmp_path: Path) -> None:
    project = _green_project(tmp_path)

    missing = validate_rendered_provenance(tmp_path, PROJECT)
    assert [issue.code for issue in missing.issues] == ["MISSING"]

    write_doc(project / RECEIPT_RELATIVE_PATH, '{"schema_version": "wrong"}\n')
    malformed = validate_rendered_provenance(tmp_path, PROJECT)
    assert [issue.code for issue in malformed.issues] == ["MALFORMED"]


def test_confined_atomic_writer_rejects_symlink_components_without_overwrite(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "validation_report.json"
    write_doc(sentinel, "original\n")
    project.mkdir()
    (project / "output").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink component"):
        atomic_write_text_confined(
            project,
            project / "output" / "validation_report.json",
            "replacement\n",
        )

    assert sentinel.read_text(encoding="utf-8") == "original\n"


def test_confined_atomic_writer_resists_parent_symlink_swap_race(tmp_path: Path) -> None:
    project = tmp_path / "project"
    reports = project / "output" / "reports"
    reports.mkdir(parents=True)
    displaced = project / "output" / "reports-displaced"
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "validation_report.json"
    write_doc(sentinel, "outside sentinel\n")
    encode_started = threading.Event()
    parent_swapped = threading.Event()

    class CoordinatedText(str):
        def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
            encode_started.set()
            assert parent_swapped.wait(timeout=5)
            return super().encode(encoding, errors)

    def swap_parent_for_symlink() -> None:
        assert encode_started.wait(timeout=5)
        reports.rename(displaced)
        reports.symlink_to(outside, target_is_directory=True)
        parent_swapped.set()

    attacker = threading.Thread(target=swap_parent_for_symlink)
    attacker.start()
    try:
        with pytest.raises(ValueError, match="write parent changed"):
            atomic_write_text_confined(
                project,
                reports / "validation_report.json",
                CoordinatedText("replacement\n"),
            )
    finally:
        attacker.join(timeout=5)

    assert not attacker.is_alive()
    assert sentinel.read_text(encoding="utf-8") == "outside sentinel\n"
    assert not (displaced / "validation_report.json").exists()


def test_source_symlink_target_is_confined_and_fingerprinted(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    shared = tmp_path / "projects" / "templates" / "shared" / "src" / "engine.py"
    write_doc(shared, "VALUE = 1\n")
    (project / "src" / "shared").symlink_to(shared.parent, target_is_directory=True)
    _write_green_validation_report(tmp_path, project)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    before = build_current_rendered_snapshot(tmp_path, PROJECT)

    write_doc(shared, "VALUE = 2\n")
    after = build_current_rendered_snapshot(tmp_path, PROJECT)

    assert after.source != before.source
    _write_green_validation_report(tmp_path, project)
    assert "SOURCE_FINGERPRINT_DRIFT" in {
        issue.code for issue in validate_rendered_provenance(tmp_path, PROJECT).issues
    }


def test_directory_symlink_fingerprint_is_checkout_root_independent(tmp_path: Path) -> None:
    snapshots = []
    for checkout_name in ("checkout-a", "different-checkout-root"):
        root = tmp_path / checkout_name
        project = _green_project(root)
        shared = root / "projects" / "templates" / "shared" / "src" / "engine.py"
        write_doc(shared, "VALUE = 1\n")
        (project / "src" / "shared").symlink_to(shared.parent, target_is_directory=True)
        snapshots.append(build_current_rendered_snapshot(root, PROJECT))

    assert snapshots[0].source == snapshots[1].source


def test_symlinked_project_tree_is_walkable_and_escapes_are_still_refused(tmp_path: Path) -> None:
    """A project symlinked into the repository is in scope; anything else is not.

    Projects are not always stored inside the repository. A private sidecar
    checkout is linked in at ``projects/working/<name>``, so the project root
    resolves outside ``repo_root``; the containment guard refused the very first
    directory and made the whole tree unreadable, even though that tree is
    exactly what the snapshot was asked to describe.

    ``extra_root`` admits the project being walked and nothing else. The three
    cases below are the ones that matter: the declared project is walkable, a
    symlink leaving both the repository and the project is still refused, and a
    caller that declares no extra root keeps the original behavior.
    """
    from infrastructure.validation.rendered_snapshot import (
        RenderedSnapshotError,
        _iter_tree_files,
    )

    repository = tmp_path / "repo"
    (repository / "projects" / "working").mkdir(parents=True)
    outside = tmp_path / "sidecar" / "my_project"
    (outside / "src").mkdir(parents=True)
    (outside / "src" / "module.py").write_text("x = 1\n", encoding="utf-8")

    linked = repository / "projects" / "working" / "my_project"
    linked.symlink_to(outside, target_is_directory=True)

    # POSITIVE: declaring the project root makes its tree walkable.
    records = list(_iter_tree_files(linked, repo_root=repository, extra_root=linked))
    assert [record.path.name for record in records] == ["module.py"]

    # NEGATIVE CONTROL: without the declaration the boundary is unchanged, so
    # the same walk is still refused. Without this the parameter could be
    # widening the guard for everyone.
    with pytest.raises(RenderedSnapshotError) as unguarded:
        list(_iter_tree_files(linked, repo_root=repository))
    assert unguarded.value.code == "SOURCE_SYMLINK_ESCAPE"

    # NEGATIVE CONTROL: a symlink escaping BOTH the repository and the declared
    # project is still refused, which is the case the guard exists for.
    elsewhere = tmp_path / "unrelated"
    elsewhere.mkdir()
    (elsewhere / "secret.py").write_text("y = 2\n", encoding="utf-8")
    (outside / "src" / "escape").symlink_to(elsewhere, target_is_directory=True)

    with pytest.raises(RenderedSnapshotError) as escaped:
        list(_iter_tree_files(linked, repo_root=repository, extra_root=linked))
    assert escaped.value.code == "SOURCE_SYMLINK_ESCAPE"

    # Internal alias inside the declared project is in scope. The guard exists
    # to stop escapes, not to refuse a sidecar project linking to itself.
    (outside / "src" / "escape").unlink()
    (outside / "src" / "alias.py").symlink_to(outside / "src" / "module.py")
    aliased = list(_iter_tree_files(linked, repo_root=repository, extra_root=linked))
    keys = {record.key for record in aliased}
    assert any(record.path.name == "module.py" for record in aliased)
    assert any("alias.py" in key for key in keys)
