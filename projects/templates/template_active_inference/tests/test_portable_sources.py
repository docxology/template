"""Real permission and namespace controls for confined Lean source snapshots."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from orchestration.portable_sources import snapshot_file, snapshot_tree


def _snapshot(root: Path, operation: str) -> bytes | dict[str, bytes]:
    deadline = time.monotonic() + 5
    if operation == "file":
        return snapshot_file(root / "input.lean", deadline=deadline)
    return snapshot_tree(root, deadline=deadline, exclude=lambda _parts: False)


@pytest.mark.parametrize("operation", ["file", "tree"])
def test_search_only_strict_ancestor_is_supported_or_refused_closed(tmp_path: Path, operation: str) -> None:
    ancestor = tmp_path / "search-only"
    root = ancestor / "selected"
    root.mkdir(parents=True)
    (root / "input.lean").write_bytes(b"theorem ready : True := trivial\n")
    ancestor.chmod(0o100)
    try:
        # Prove the actual kernel denies enumeration; running as root cannot
        # silently turn this permission control into a passing simulation.
        with pytest.raises(PermissionError):
            os.listdir(ancestor)
        if hasattr(os, "O_PATH"):
            result = _snapshot(root, operation)
            expected = b"theorem ready : True := trivial\n"
            assert result == (expected if operation == "file" else {"input.lean": expected})
        else:
            with pytest.raises(PermissionError):
                _snapshot(root, operation)
    finally:
        ancestor.chmod(0o700)


def test_selected_tree_still_requires_readable_enumeration(tmp_path: Path) -> None:
    root = tmp_path / "selected"
    root.mkdir()
    (root / "input.lean").write_bytes(b"known input")
    root.chmod(0o100)
    try:
        with pytest.raises(PermissionError):
            _snapshot(root, "tree")
    finally:
        root.chmod(0o700)


def test_selected_file_still_requires_readable_bytes(tmp_path: Path) -> None:
    path = tmp_path / "input.lean"
    path.write_bytes(b"private input")
    path.chmod(0)
    try:
        with pytest.raises(PermissionError):
            _snapshot(tmp_path, "file")
    finally:
        path.chmod(0o600)


@pytest.mark.parametrize("operation", ["file", "tree"])
def test_search_handles_refuse_ancestor_symlinks(tmp_path: Path, operation: str) -> None:
    target = tmp_path / "physical"
    target.mkdir()
    (target / "input.lean").write_bytes(b"outside alias")
    alias = tmp_path / "alias"
    alias.symlink_to(target, target_is_directory=True)

    with pytest.raises((OSError, ValueError)):
        _snapshot(alias, operation)


def test_held_search_ancestor_replacement_is_refused(tmp_path: Path) -> None:
    ancestor = tmp_path / "ancestor"
    root = ancestor / "selected"
    root.mkdir(parents=True)
    (root / "input.lean").write_bytes(b"held original")
    replaced = False

    def replace_ancestor(_parts: tuple[str, ...]) -> bool:
        nonlocal replaced
        if not replaced:
            ancestor.rename(tmp_path / "old-ancestor")
            root.mkdir(parents=True)
            (root / "input.lean").write_bytes(b"replacement")
            replaced = True
        return False

    with pytest.raises(ValueError, match="ancestor changed"):
        snapshot_tree(root, deadline=time.monotonic() + 5, exclude=replace_ancestor)
    assert replaced
