"""Real filesystem controls for lexical admission inside held Source traversal."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from infrastructure.core.pipeline.fingerprints import tree_records
from infrastructure.project.public_reference import _path_admission
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def test_source_tree_policy_retains_exact_names_and_content(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    source = root / "docs"
    (source / "nested").mkdir(parents=True)
    (source / "nested/guide.md").write_bytes(b"public source\n")
    records = tree_records(source, source=True, path_admission=_path_admission(SnapshotReader(root)))
    assert records == (
        (".", "directory", ""),
        ("./nested", "directory", ""),
        ("./nested/guide.md", "file", hashlib.sha256(b"public source\n").hexdigest()),
    )


@pytest.mark.parametrize("linked", ("leaf", "directory", "ancestor"))
def test_source_tree_policy_still_refuses_actual_symlinks(tmp_path: Path, linked: str) -> None:
    root = tmp_path.resolve()
    source = root / "docs"
    source.mkdir()
    outside = root / "outside"
    outside.mkdir()
    (outside / "guide.md").write_text("must not become public Source")
    if linked == "leaf":
        (source / "guide.md").symlink_to(outside / "guide.md")
    elif linked == "directory":
        (source / "nested").symlink_to(outside, target_is_directory=True)
    else:
        source.rmdir()
        source.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink|non-directory"):
        tree_records(source, source=True, path_admission=_path_admission(SnapshotReader(root)))


@pytest.mark.parametrize("relative", ("docs/.env", "projects/working/private/secret.md"))
def test_source_tree_policy_still_refuses_private_paths(tmp_path: Path, relative: str) -> None:
    root = tmp_path.resolve()
    path = root / relative
    path.parent.mkdir(parents=True)
    path.write_text("private")
    with pytest.raises(ValueError, match="private|unknown"):
        tree_records(path, source=True, path_admission=_path_admission(SnapshotReader(root)))
