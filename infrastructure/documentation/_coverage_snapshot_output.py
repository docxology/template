"""Admit a retained DATA copy for coverage literals without rewriting SDK code."""

from __future__ import annotations

import stat
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.files.secure_write import (
    atomic_write_bytes_confined,
    read_bytes_confined,
)

_MAX_SNAPSHOT_BYTES = 4 * 1024 * 1024


def _identity(path: Path) -> tuple[int, int, int, int, int, int, int]:
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise ValueError("coverage snapshot DATA must be an independent single-link regular file")
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
        metadata.st_nlink,
    )


def _directory_identity(path: Path) -> tuple[int, int]:
    metadata = path.lstat()
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("coverage snapshot DATA parent must be a real directory")
    return metadata.st_dev, metadata.st_ino


def _confined_body(path: Path, parent_identity: tuple[int, int]) -> bytes:
    return read_bytes_confined(
        path.parent,
        path,
        max_bytes=_MAX_SNAPSHOT_BYTES,
        expected_root_identity=parent_identity,
    )


def _outside_protected_roots(output: Path, repo_root: Path, source: Path) -> None:
    if ".." in output.parts or ".." in repo_root.parts or ".." in source.parts:
        raise ValueError("coverage snapshot nominations cannot contain parent traversal")
    # The selected SDK root is the parent of infrastructure/, including every
    # installed sibling package. Physical ancestor identities also catch aliases
    # not expressed by the same lexical spelling (including case-insensitive FS).
    protected = (repo_root.absolute(), source.absolute().parents[2])
    output_physical = output.resolve(strict=True)
    ancestors = (output.parent, *output.parent.parents)
    for root in protected:
        root_physical = root.resolve(strict=True)
        for candidate, boundary in ((output, root), (output_physical, root_physical)):
            if candidate.is_relative_to(boundary):
                raise ValueError("coverage snapshot DATA must be outside the repository and selected SDK root")
        root_identity = _directory_identity(root_physical)
        if any(_directory_identity(parent) == root_identity for parent in ancestors):
            raise ValueError("coverage snapshot DATA physically overlaps a protected root")


@dataclass(frozen=True)
class CoverageSnapshotOutput:
    """One admitted original copy; it is never an executable Source exception."""

    path: Path
    repo_root: Path
    source: Path
    original: bytes
    source_identity: tuple[int, int, int, int, int, int, int]
    output_identity: tuple[int, int, int, int, int, int, int]
    source_parent_identity: tuple[int, int]
    output_parent_identity: tuple[int, int]

    @classmethod
    def admit(cls, repo_root: Path, output: Path, source: Path) -> CoverageSnapshotOutput:
        """Require an existing independent exact copy, outside protected code/data.

        The owning launcher preserves this original before measurement, then
        reviews and applies only the resulting literal delta after its original
        process, complete Source/Code/wheel closure and terminal evidence finish.
        A selected wheel cannot pass the exact UTF-8 Source-copy comparison;
        hardlink and symlink aliases are refused before any write or measurement.
        """
        output = output.absolute()
        source = source.absolute()
        repo_root = repo_root.absolute()
        _outside_protected_roots(output, repo_root, source)
        source_identity = _identity(source)
        output_identity = _identity(output)
        if source_identity[:2] == output_identity[:2]:
            raise ValueError("coverage snapshot DATA aliases the consumed Source")
        source_parent = _directory_identity(source.parent)
        output_parent = _directory_identity(output.parent)
        original = _confined_body(source, source_parent)
        original.decode("utf-8")
        if _confined_body(output, output_parent) != original:
            raise ValueError("coverage snapshot DATA must initially copy the selected counts_coverage.py exactly")
        admitted = cls(
            output,
            repo_root,
            source,
            original,
            source_identity,
            output_identity,
            source_parent,
            output_parent,
        )
        admitted.original_text()
        return admitted

    def _check_source(self) -> None:
        if (
            _identity(self.source) != self.source_identity
            or _confined_body(self.source, self.source_parent_identity) != self.original
        ):
            raise ValueError("consumed coverage snapshot Source changed after DATA admission")

    def original_text(self) -> str:
        """Recheck original Source and DATA before the existing literal writer."""
        _outside_protected_roots(self.path, self.repo_root, self.source)
        self._check_source()
        if (
            _identity(self.path) != self.output_identity
            or _confined_body(self.path, self.output_parent_identity) != self.original
        ):
            raise ValueError("coverage snapshot DATA changed after admission")
        return self.original.decode("utf-8")

    def write_text(self, content: str) -> None:
        """Persist only the retained DATA nomination through the existing writer."""
        self.original_text()
        encoded = content.encode("utf-8")
        if len(encoded) > _MAX_SNAPSHOT_BYTES:
            raise ValueError("coverage snapshot DATA exceeds its bounded copy budget")
        atomic_write_bytes_confined(
            self.path.parent,
            self.path,
            encoded,
            mode=stat.S_IMODE(self.output_identity[2]),
            expected_root_identity=self.output_parent_identity,
        )
        _outside_protected_roots(self.path, self.repo_root, self.source)
        self._check_source()
        if _confined_body(self.path, self.output_parent_identity) != encoded:
            raise ValueError("coverage snapshot DATA did not retain the exact emitted bytes")
        _identity(self.path)
