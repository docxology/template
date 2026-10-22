"""Actual source-confinement and frozen-input materialization controls."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from template_formal._tool_sources import materialize, snapshot_file, snapshot_tree


def test_source_admission_rejects_lexical_parent_traversal(tmp_path: Path) -> None:
    (tmp_path / "input.lean").write_bytes(b"admitted model\n")
    (tmp_path / "nested").mkdir()
    with pytest.raises(ValueError, match="lexical parent traversal"):
        snapshot_file(tmp_path / "nested/../input.lean", deadline=time.monotonic() + 2)


def test_source_admission_bounds_ancestor_depth_before_filesystem_work(tmp_path: Path) -> None:
    excessive = tmp_path.joinpath(*("nested" for _ in range(129)), "input.lean")
    with pytest.raises(ValueError, match="ancestor depth"):
        snapshot_file(excessive, deadline=time.monotonic() + 2)
    assert not (tmp_path / "nested").exists()


@pytest.mark.parametrize("kind", ["file", "symlink"])
def test_source_admission_refuses_non_directory_and_symlink_ancestors(tmp_path: Path, kind: str) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "input.lean").write_bytes(b"external model\n")
    parent = tmp_path / "parent"
    if kind == "file":
        parent.write_bytes(b"not a directory")
    else:
        parent.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="ancestor symlinks or non-directories"):
        snapshot_file(parent / "input.lean", deadline=time.monotonic() + 2)


def test_inventory_mutation_during_source_admission_cannot_return_partial_snapshot(tmp_path: Path) -> None:
    (tmp_path / "initial.lean").write_bytes(b"initial model\n")
    changed = False

    def exclude(_parts: tuple[str, ...]) -> bool:
        nonlocal changed
        if not changed:
            (tmp_path / "new.lean").write_bytes(b"new declared model\n")
            changed = True
        return False

    with pytest.raises(ValueError, match="directory changed"):
        snapshot_tree(tmp_path, deadline=time.monotonic() + 2, exclude=exclude)
    assert changed


@pytest.mark.parametrize("relative", ["../outside.lean", "/outside.lean", "", ".", "models//input.lean"])
def test_materialization_refuses_unconfined_or_ambiguous_names(tmp_path: Path, relative: str) -> None:
    with pytest.raises(ValueError, match="admitted relative path"):
        materialize({relative: b"untrusted model\n"}, tmp_path)
    assert not list(tmp_path.iterdir())


def test_actual_snapshot_materializes_identical_readonly_tool_inputs(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "model.lean").write_bytes(b"theorem control : True := True.intro\n")
    if hasattr(os, "O_SEARCH") or hasattr(os, "O_PATH"):
        # Ancestors need search permission; tree endpoints still need readable descriptors.
        original_mode = tmp_path.stat().st_mode & 0o7777
        tmp_path.chmod(0o111)
        try:
            if hasattr(os, "geteuid") and os.geteuid() != 0:
                with pytest.raises(PermissionError):
                    os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
            expected = b"theorem control : True := True.intro\n"
            assert snapshot_file(source / "model.lean", deadline=time.monotonic() + 2) == expected
            assert snapshot_tree(source, deadline=time.monotonic() + 2, exclude=lambda _parts: False) == {
                "model.lean": expected
            }
        finally:
            tmp_path.chmod(original_mode)
    snapshot = snapshot_tree(source, deadline=time.monotonic() + 2, exclude=lambda _parts: False)
    target = tmp_path / "frozen"
    materialize(snapshot, target)
    assert (target / "model.lean").read_bytes() == (source / "model.lean").read_bytes()
    assert (target / "model.lean").stat().st_mode & 0o777 == 0o400
